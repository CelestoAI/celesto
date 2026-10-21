//! Isolated tests for the credential proxy (D-08).
//!
//! The proxy holds real secrets and parses untrusted guest traffic, so its
//! injection rules are tested in isolation. Each test names the D-08 failure
//! mode it guards:
//!
//! 1. inject for a host not bound to the secret
//! 2. inject when the request lacks the exact placeholder
//! 3. inject into body or query
//! 4. SNI and `Host` disagree (domain fronting)
//! 5. Basic auth decode/re-encode wrong or applied to the wrong header
//! 6. placeholder split across headers or repeated
//! 7. WebSocket Upgrade not injected
//! 8. SSE buffered instead of streamed
//! 9. real value written to the log
//! 10. panic in one connection kills the process
//!
//! A local TLS upstream (with its own test CA, trusted through a test-only
//! option) records what it receives. The test client trusts the proxy's
//! fresh CA and connects to the proxy as a guest would.

use super::*;

use base64::Engine as _;
use base64::engine::general_purpose::STANDARD as B64;
use bytes::Bytes;
use http_body_util::{BodyExt, Full, StreamBody};
use hyper::body::{Frame, Incoming};
use hyper::{Request, Response, StatusCode};
use hyper_util::rt::{TokioExecutor, TokioIo};
use rcgen::{BasicConstraints, CertificateParams, CertifiedIssuer, IsCa, KeyPair};
use std::collections::HashMap;
use std::convert::Infallible;
use std::net::SocketAddr;
use std::path::PathBuf;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Arc, Mutex};
use std::time::Duration;
use tokio::io::{AsyncRead, AsyncReadExt, AsyncWrite, AsyncWriteExt};
use tokio::net::{TcpListener, TcpStream, UnixStream};
use tokio::sync::{Notify, mpsc};

const REAL_A: &str = "sk-REAL-aaaaaaaaaaaaaaaaaaaaaaaa";
const REAL_B: &str = "sk-REAL-bbbbbbbbbbbbbbbbbbbbbbbb";
const REAL_GH: &str = "ghp_REALgithubtokenvalue000000";
const PH_A: &str = "celesto-ph-aaaaaaaaaaaaaaaaaaaa";
const PH_B: &str = "celesto-ph-bbbbbbbbbbbbbbbbbbbb";
const PH_GH: &str = "celesto-ph-gggggggggggggggggggg";
const PH_BOOM: &str = "celesto-ph-boomboomboomboomboom";

const HOST_A: &str = "a.test";
const HOST_B: &str = "b.test";
const HOST_GH: &str = "gh.test";
const HOST_LOCAL: &str = "auth.test";
const HOST_BOOM: &str = "boom.test";
const ALL_HOSTS: &[&str] = &[HOST_A, HOST_B, HOST_GH, HOST_LOCAL, HOST_BOOM];

// ---------------------------------------------------------------- upstream

#[derive(Clone, Debug)]
struct Seen {
    host: String,
    path_and_query: String,
    headers: Vec<(String, Vec<u8>)>,
    body: Vec<u8>,
}

impl Seen {
    fn header_values(&self, name: &str) -> Vec<String> {
        self.headers
            .iter()
            .filter(|(k, _)| k == name)
            .map(|(_, v)| String::from_utf8_lossy(v).into_owned())
            .collect()
    }

    fn header(&self, name: &str) -> Option<String> {
        self.header_values(name).into_iter().next()
    }

    fn all_text(&self) -> String {
        let mut s = String::new();
        s.push_str(&self.path_and_query);
        for (k, v) in &self.headers {
            s.push_str(k);
            s.push_str(&String::from_utf8_lossy(v));
        }
        s.push_str(&String::from_utf8_lossy(&self.body));
        s
    }
}

struct Upstream {
    addr: SocketAddr,
    ca_pem: String,
    seen: Arc<Mutex<Vec<Seen>>>,
    sse_gate: Arc<Notify>,
}

impl Upstream {
    fn seen(&self) -> Vec<Seen> {
        self.seen.lock().unwrap().clone()
    }

    fn last(&self) -> Seen {
        self.seen().last().cloned().expect("upstream saw a request")
    }

    fn count(&self) -> usize {
        self.seen.lock().unwrap().len()
    }
}

fn test_ca(name: &str) -> CertifiedIssuer<'static, KeyPair> {
    let mut params = CertificateParams::new(Vec::<String>::new()).unwrap();
    params.is_ca = IsCa::Ca(BasicConstraints::Unconstrained);
    params
        .distinguished_name
        .push(rcgen::DnType::CommonName, name);
    params.key_usages = vec![
        rcgen::KeyUsagePurpose::KeyCertSign,
        rcgen::KeyUsagePurpose::CrlSign,
    ];
    CertifiedIssuer::self_signed(params, KeyPair::generate().unwrap()).unwrap()
}

type TestBody = http_body_util::combinators::BoxBody<Bytes, Infallible>;

fn full(body: impl Into<Bytes>) -> TestBody {
    Full::new(body.into()).boxed()
}

async fn upstream_handle(
    mut req: Request<Incoming>,
    seen: Arc<Mutex<Vec<Seen>>>,
    gate: Arc<Notify>,
) -> Result<Response<TestBody>, Infallible> {
    let host = req
        .uri()
        .authority()
        .map(|a| a.host().to_string())
        .or_else(|| {
            req.headers()
                .get("host")
                .map(|h| h.to_str().unwrap().to_string())
        })
        .unwrap_or_default();
    let path_and_query = req
        .uri()
        .path_and_query()
        .map(|p| p.to_string())
        .unwrap_or_default();
    let headers: Vec<(String, Vec<u8>)> = req
        .headers()
        .iter()
        .map(|(k, v)| (k.as_str().to_string(), v.as_bytes().to_vec()))
        .collect();
    let is_upgrade = req.headers().contains_key("upgrade");
    let on_upgrade = if is_upgrade {
        Some(hyper::upgrade::on(&mut req))
    } else {
        None
    };
    let body = if is_upgrade {
        Vec::new()
    } else {
        req.into_body().collect().await.unwrap().to_bytes().to_vec()
    };
    seen.lock().unwrap().push(Seen {
        host,
        path_and_query: path_and_query.clone(),
        headers,
        body,
    });

    if let Some(on_upgrade) = on_upgrade {
        tokio::spawn(async move {
            let upgraded = on_upgrade.await.unwrap();
            let mut io = TokioIo::new(upgraded);
            let mut buf = [0u8; 1024];
            loop {
                let n = match io.read(&mut buf).await {
                    Ok(0) | Err(_) => break,
                    Ok(n) => n,
                };
                let mut reply = b"echo:".to_vec();
                reply.extend_from_slice(&buf[..n]);
                if io.write_all(&reply).await.is_err() {
                    break;
                }
            }
        });
        return Ok(Response::builder()
            .status(StatusCode::SWITCHING_PROTOCOLS)
            .header("connection", "upgrade")
            .header("upgrade", "websocket")
            .body(full(Bytes::new()))
            .unwrap());
    }

    if path_and_query.starts_with("/sse") {
        let (tx, rx) = mpsc::channel::<Result<Frame<Bytes>, Infallible>>(4);
        tokio::spawn(async move {
            tx.send(Ok(Frame::data(Bytes::from_static(b"data: one\n\n"))))
                .await
                .ok();
            gate.notified().await;
            tx.send(Ok(Frame::data(Bytes::from_static(b"data: two\n\n"))))
                .await
                .ok();
        });
        let stream = futures_util::stream::unfold(rx, |mut rx| async move {
            rx.recv().await.map(|item| (item, rx))
        });
        return Ok(Response::builder()
            .header("content-type", "text/event-stream")
            .body(StreamBody::new(stream).boxed())
            .unwrap());
    }

    Ok(Response::new(full("ok")))
}

async fn start_upstream() -> Upstream {
    let _ = rustls::crypto::ring::default_provider().install_default();
    let ca = test_ca("upstream test CA");
    let key = KeyPair::generate().unwrap();
    let params =
        CertificateParams::new(ALL_HOSTS.iter().map(|h| h.to_string()).collect::<Vec<_>>())
            .unwrap();
    let cert = params.signed_by(&key, &ca).unwrap();
    let mut config = rustls::ServerConfig::builder_with_provider(Arc::new(
        rustls::crypto::ring::default_provider(),
    ))
    .with_safe_default_protocol_versions()
    .unwrap()
    .with_no_client_auth()
    .with_single_cert(
        vec![cert.der().clone()],
        rustls::pki_types::PrivateKeyDer::Pkcs8(key.serialize_der().into()),
    )
    .unwrap();
    config.alpn_protocols = vec![b"h2".to_vec(), b"http/1.1".to_vec()];
    let acceptor = tokio_rustls::TlsAcceptor::from(Arc::new(config));
    let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
    let addr = listener.local_addr().unwrap();
    let seen = Arc::new(Mutex::new(Vec::new()));
    let gate = Arc::new(Notify::new());
    let (seen2, gate2) = (seen.clone(), gate.clone());
    tokio::spawn(async move {
        loop {
            let (tcp, _) = listener.accept().await.unwrap();
            let acceptor = acceptor.clone();
            let (seen, gate) = (seen2.clone(), gate2.clone());
            tokio::spawn(async move {
                let Ok(tls) = acceptor.accept(tcp).await else {
                    return;
                };
                let service = hyper::service::service_fn(move |req| {
                    upstream_handle(req, seen.clone(), gate.clone())
                });
                let _ = hyper_util::server::conn::auto::Builder::new(TokioExecutor::new())
                    .serve_connection_with_upgrades(TokioIo::new(tls), service)
                    .await;
            });
        }
    });
    Upstream {
        addr,
        ca_pem: ca.pem(),
        seen,
        sse_gate: gate,
    }
}

// ------------------------------------------------------------------- proxy

static COUNTER: AtomicUsize = AtomicUsize::new(0);

fn scratch(name: &str) -> PathBuf {
    // Unix socket paths must stay under ~104 bytes, so use a short root.
    let n = COUNTER.fetch_add(1, Ordering::SeqCst);
    let dir = PathBuf::from(format!("/tmp/ccp-{}-{n}", std::process::id()));
    std::fs::create_dir_all(&dir).unwrap();
    dir.join(name)
}

fn header_rule(header: &str, form: HeaderForm) -> HeaderRule {
    HeaderRule {
        header: header.to_string(),
        form,
    }
}

fn default_bindings() -> Vec<Binding> {
    vec![
        Binding {
            name: "KEY_A".into(),
            placeholder: PH_A.into(),
            hosts: vec![HOST_A.into()],
            headers: vec![header_rule("authorization", HeaderForm::Bearer)],
        },
        Binding {
            name: "KEY_B".into(),
            placeholder: PH_B.into(),
            hosts: vec![HOST_B.into()],
            headers: vec![header_rule("x-api-key", HeaderForm::Raw)],
        },
        Binding {
            name: "GH_TOKEN".into(),
            placeholder: PH_GH.into(),
            hosts: vec![HOST_GH.into()],
            headers: vec![header_rule("authorization", HeaderForm::BasicPassword)],
        },
        Binding {
            name: "BOOM".into(),
            placeholder: PH_BOOM.into(),
            hosts: vec![HOST_BOOM.into()],
            headers: vec![header_rule("authorization", HeaderForm::Bearer)],
        },
    ]
}

struct Harness {
    proxy: CredentialProxy,
    info: StartInfo,
    log_path: PathBuf,
    resolver_calls: Arc<Mutex<Vec<String>>>,
    handler_calls: Arc<Mutex<Vec<LocalRequest>>>,
}

impl Drop for Harness {
    fn drop(&mut self) {
        if let Some(dir) = self.log_path.parent() {
            let _ = std::fs::remove_dir_all(dir);
        }
    }
}

impl Harness {
    fn log_lines(&self) -> Vec<serde_json::Value> {
        std::fs::read_to_string(&self.log_path)
            .unwrap_or_default()
            .lines()
            .map(|l| serde_json::from_str(l).expect("log line is JSON"))
            .collect()
    }

    fn log_text(&self) -> String {
        std::fs::read_to_string(&self.log_path).unwrap_or_default()
    }
}

fn start_proxy(up: &Upstream, listen_unix: bool) -> Harness {
    let log_path = scratch("proxy.log");
    let listen = if listen_unix {
        format!("unix:{}", scratch("p.sock").display())
    } else {
        "tcp:127.0.0.1:0".to_string()
    };
    let overrides: HashMap<String, SocketAddr> =
        ALL_HOSTS.iter().map(|h| (h.to_string(), up.addr)).collect();
    let mut proxy = CredentialProxy::new(ProxyOptions {
        listen,
        log_path: log_path.clone(),
        upstream_extra_roots_pem: Some(up.ca_pem.clone()),
        upstream_addr_overrides: overrides,
    })
    .unwrap();
    proxy.set_bindings(default_bindings()).unwrap();
    proxy
        .set_local_routes(vec![LocalRoute {
            host: HOST_LOCAL.into(),
            path: "/oauth/token".into(),
            handler: "refresh".into(),
        }])
        .unwrap();
    let resolver_calls = Arc::new(Mutex::new(Vec::new()));
    let calls = resolver_calls.clone();
    proxy.set_resolver(Arc::new(move |name: &str| {
        calls.lock().unwrap().push(name.to_string());
        match name {
            "KEY_A" => Ok(Some(REAL_A.to_string())),
            "KEY_B" => Ok(Some(REAL_B.to_string())),
            "GH_TOKEN" => Ok(Some(REAL_GH.to_string())),
            "BOOM" => panic!("resolver panic for test"),
            _ => Ok(None),
        }
    }));
    let handler_calls = Arc::new(Mutex::new(Vec::new()));
    let hc = handler_calls.clone();
    proxy.set_local_handler(
        "refresh",
        Arc::new(move |req: LocalRequest| {
            if req.path.contains("panic") {
                panic!("handler panic for test");
            }
            hc.lock().unwrap().push(req.clone());
            Ok(LocalResponse {
                status: 200,
                headers: vec![("content-type".into(), "application/json".into())],
                body: br#"{"access_token":"placeholder"}"#.to_vec(),
            })
        }),
    );
    let info = proxy.start().unwrap();
    Harness {
        proxy,
        info,
        log_path,
        resolver_calls,
        handler_calls,
    }
}

// ------------------------------------------------------------------ client

trait Io: AsyncRead + AsyncWrite + Unpin + Send {}
impl<T: AsyncRead + AsyncWrite + Unpin + Send> Io for T {}

async fn raw_connect(info: &StartInfo) -> std::io::Result<Box<dyn Io>> {
    if let Some(path) = info.address.strip_prefix("unix:") {
        Ok(Box::new(UnixStream::connect(path).await?))
    } else {
        let addr = info.address.strip_prefix("tcp:").unwrap();
        Ok(Box::new(TcpStream::connect(addr).await?))
    }
}

async fn tls_connect(
    info: &StartInfo,
    sni: &str,
    alpn: &[&[u8]],
) -> std::io::Result<tokio_rustls::client::TlsStream<Box<dyn Io>>> {
    let mut roots = rustls::RootCertStore::empty();
    for cert in rustls_pemfile::certs(&mut info.ca_cert_pem.as_bytes()) {
        roots.add(cert.unwrap()).unwrap();
    }
    let mut config = rustls::ClientConfig::builder_with_provider(Arc::new(
        rustls::crypto::ring::default_provider(),
    ))
    .with_safe_default_protocol_versions()
    .unwrap()
    .with_root_certificates(roots)
    .with_no_client_auth();
    config.alpn_protocols = alpn.iter().map(|p| p.to_vec()).collect();
    let connector = tokio_rustls::TlsConnector::from(Arc::new(config));
    let io = raw_connect(info).await?;
    let name = rustls::pki_types::ServerName::try_from(sni.to_string()).unwrap();
    connector.connect(name, io).await
}

struct Reply {
    status: StatusCode,
    body: Bytes,
}

async fn send_h1(info: &StartInfo, sni: &str, req: Request<TestBody>) -> Reply {
    let tls = tls_connect(info, sni, &[b"http/1.1"]).await.unwrap();
    let (mut sender, conn) = hyper::client::conn::http1::handshake(TokioIo::new(tls))
        .await
        .unwrap();
    tokio::spawn(conn);
    let resp = tokio::time::timeout(Duration::from_secs(10), sender.send_request(req))
        .await
        .expect("proxy answered in time")
        .unwrap();
    let status = resp.status();
    let body = resp.into_body().collect().await.unwrap().to_bytes();
    Reply { status, body }
}

async fn send_h2(info: &StartInfo, sni: &str, req: Request<TestBody>) -> Reply {
    let tls = tls_connect(info, sni, &[b"h2", b"http/1.1"]).await.unwrap();
    assert_eq!(tls.get_ref().1.alpn_protocol(), Some(&b"h2"[..]));
    let (mut sender, conn) =
        hyper::client::conn::http2::handshake(TokioExecutor::new(), TokioIo::new(tls))
            .await
            .unwrap();
    tokio::spawn(conn);
    let resp = tokio::time::timeout(Duration::from_secs(10), sender.send_request(req))
        .await
        .expect("proxy answered in time")
        .unwrap();
    let status = resp.status();
    let body = resp.into_body().collect().await.unwrap().to_bytes();
    Reply { status, body }
}

fn get(host: &str, path: &str) -> hyper::http::request::Builder {
    Request::builder()
        .method("GET")
        .uri(path)
        .header("host", host)
}

fn basic(user: &str, pass: &str) -> String {
    format!("Basic {}", B64.encode(format!("{user}:{pass}")))
}

fn assert_no_secret(text: &str) {
    for real in [REAL_A, REAL_B, REAL_GH] {
        assert!(!text.contains(real), "real value leaked: {text}");
    }
}

// ------------------------------------------------------------------- tests

#[tokio::test(flavor = "multi_thread")]
async fn injects_bearer_raw_over_h1_and_h2() {
    let up = start_upstream().await;
    let h = start_proxy(&up, true);
    assert!(h.info.address.starts_with("unix:"));

    let r = send_h1(
        &h.info,
        HOST_A,
        get(HOST_A, "/v1/models")
            .header("authorization", format!("Bearer {PH_A}"))
            .body(full(""))
            .unwrap(),
    )
    .await;
    assert_eq!(r.status, 200);
    let seen = up.last();
    assert_eq!(seen.host, HOST_A);
    assert_eq!(seen.path_and_query, "/v1/models");
    assert_eq!(
        seen.header("authorization").unwrap(),
        format!("Bearer {REAL_A}")
    );

    let r = send_h2(
        &h.info,
        HOST_B,
        Request::builder()
            .method("POST")
            .uri(format!("https://{HOST_B}/v1/messages"))
            .header("x-api-key", PH_B)
            .body(full("{}"))
            .unwrap(),
    )
    .await;
    assert_eq!(r.status, 200);
    assert_eq!(up.last().header("x-api-key").unwrap(), REAL_B);
    assert_eq!(up.last().body, b"{}");

    let stats = h.proxy.stats();
    assert!(stats.connections >= 2);
    assert!(stats.last_used.contains_key("KEY_A"));
    assert!(stats.last_used.contains_key("KEY_B"));
}

#[tokio::test(flavor = "multi_thread")]
async fn fm01_placeholder_on_unbound_host_is_not_injected_and_is_logged() {
    let up = start_upstream().await;
    let h = start_proxy(&up, false);
    assert!(h.info.address.starts_with("tcp:127.0.0.1:"));

    // KEY_A is bound to a.test only; send it to b.test.
    let r = send_h1(
        &h.info,
        HOST_B,
        get(HOST_B, "/")
            .header("authorization", format!("Bearer {PH_A}"))
            .header("x-api-key", PH_A)
            .body(full(""))
            .unwrap(),
    )
    .await;
    assert_eq!(r.status, 200);
    let seen = up.last();
    assert_eq!(
        seen.header("authorization").unwrap(),
        format!("Bearer {PH_A}")
    );
    assert_eq!(seen.header("x-api-key").unwrap(), PH_A);
    assert_no_secret(&seen.all_text());
    assert!(
        !h.resolver_calls
            .lock()
            .unwrap()
            .contains(&"KEY_A".to_string())
    );
    let refusals: Vec<_> = h
        .log_lines()
        .into_iter()
        .filter(|l| l["event"] == "refuse" && l["name"] == "KEY_A")
        .collect();
    assert!(!refusals.is_empty(), "{:?}", h.log_text());
    assert_eq!(refusals[0]["host"], HOST_B);
}

#[tokio::test(flavor = "multi_thread")]
async fn fm01_unknown_sni_gets_no_certificate() {
    let up = start_upstream().await;
    let h = start_proxy(&up, true);
    let err = tls_connect(&h.info, "evil.test", &[b"http/1.1"]).await;
    assert!(
        err.is_err(),
        "proxy must not terminate TLS for an unbound host"
    );
    assert_eq!(up.count(), 0);
}

#[tokio::test(flavor = "multi_thread")]
async fn fm02_inexact_placeholder_is_never_injected() {
    let up = start_upstream().await;
    let h = start_proxy(&up, true);
    let variants = [
        format!("Bearer {PH_A}x"),
        format!("Bearer x{PH_A}"),
        format!("Bearer {}", &PH_A[..PH_A.len() - 1]),
        format!("Token {PH_A}"),
        PH_A.to_string(), // raw form on a bearer rule
        "Bearer something-else".to_string(),
    ];
    for value in &variants {
        send_h1(
            &h.info,
            HOST_A,
            get(HOST_A, "/")
                .header("authorization", value.as_str())
                .body(full(""))
                .unwrap(),
        )
        .await;
        let seen = up.last();
        assert_eq!(&seen.header("authorization").unwrap(), value);
        assert_no_secret(&seen.all_text());
    }
    // A header the binding has no rule for is left alone.
    send_h1(
        &h.info,
        HOST_A,
        get(HOST_A, "/")
            .header("x-other", format!("Bearer {PH_A}"))
            .body(full(""))
            .unwrap(),
    )
    .await;
    assert_eq!(
        up.last().header("x-other").unwrap(),
        format!("Bearer {PH_A}")
    );
    assert!(up.last().header("authorization").is_none());
    assert_no_secret(&up.last().all_text());
}

#[tokio::test(flavor = "multi_thread")]
async fn fm03_body_and_query_are_never_injected() {
    let up = start_upstream().await;
    let h = start_proxy(&up, true);
    let body = format!(r#"{{"key":"{PH_A}"}}"#);
    send_h1(
        &h.info,
        HOST_A,
        Request::builder()
            .method("POST")
            .uri(format!("/v1/echo?key={PH_A}"))
            .header("host", HOST_A)
            .header("authorization", format!("Bearer {PH_A}"))
            .body(full(body.clone()))
            .unwrap(),
    )
    .await;
    let seen = up.last();
    assert_eq!(
        seen.header("authorization").unwrap(),
        format!("Bearer {REAL_A}")
    );
    assert_eq!(seen.path_and_query, format!("/v1/echo?key={PH_A}"));
    assert_eq!(seen.body, body.as_bytes());
    assert!(!seen.path_and_query.contains(REAL_A));
    assert!(!String::from_utf8_lossy(&seen.body).contains(REAL_A));
}

#[tokio::test(flavor = "multi_thread")]
async fn fm04_host_that_disagrees_with_sni_gets_421() {
    let up = start_upstream().await;
    let h = start_proxy(&up, true);

    // HTTP/1.1 Host header fronting: TLS to b.test, Host a.test.
    let r = send_h1(
        &h.info,
        HOST_B,
        get(HOST_A, "/")
            .header("authorization", format!("Bearer {PH_A}"))
            .body(full(""))
            .unwrap(),
    )
    .await;
    assert_eq!(r.status, StatusCode::MISDIRECTED_REQUEST);

    // Missing Host.
    let r = send_h1(
        &h.info,
        HOST_A,
        Request::builder()
            .uri("/")
            .header("authorization", format!("Bearer {PH_A}"))
            .body(full(""))
            .unwrap(),
    )
    .await;
    assert_eq!(r.status, StatusCode::MISDIRECTED_REQUEST);

    // Host on another port.
    let r = send_h1(
        &h.info,
        HOST_A,
        get(&format!("{HOST_A}:8443"), "/")
            .header("authorization", format!("Bearer {PH_A}"))
            .body(full(""))
            .unwrap(),
    )
    .await;
    assert_eq!(r.status, StatusCode::MISDIRECTED_REQUEST);

    // HTTP/2 :authority fronting.
    let r = send_h2(
        &h.info,
        HOST_B,
        Request::builder()
            .uri(format!("https://{HOST_A}/"))
            .header("authorization", format!("Bearer {PH_A}"))
            .body(full(""))
            .unwrap(),
    )
    .await;
    assert_eq!(r.status, StatusCode::MISDIRECTED_REQUEST);

    // Explicit :443 and different case are the same host.
    let r = send_h1(
        &h.info,
        HOST_A,
        get("A.TEST:443", "/")
            .header("authorization", format!("Bearer {PH_A}"))
            .body(full(""))
            .unwrap(),
    )
    .await;
    assert_eq!(r.status, 200);
    assert_eq!(up.count(), 1, "only the matching request reaches upstream");
    assert_eq!(
        up.last().header("authorization").unwrap(),
        format!("Bearer {REAL_A}")
    );

    let mismatches = h
        .log_lines()
        .into_iter()
        .filter(|l| l["status"] == 421)
        .count();
    assert_eq!(mismatches, 4, "{}", h.log_text());
}

#[tokio::test(flavor = "multi_thread")]
async fn fm05_basic_password_is_decoded_swapped_and_reencoded() {
    let up = start_upstream().await;
    let h = start_proxy(&up, true);

    send_h1(
        &h.info,
        HOST_GH,
        get(HOST_GH, "/repo.git/info/refs")
            .header("authorization", basic("x-access-token", PH_GH))
            .body(full(""))
            .unwrap(),
    )
    .await;
    assert_eq!(
        up.last().header("authorization").unwrap(),
        basic("x-access-token", REAL_GH)
    );

    // Not injected: placeholder as the user name, Bearer on a Basic rule,
    // Basic in a header the rule does not name, malformed base64.
    let cases: Vec<(&str, String)> = vec![
        ("authorization", basic(PH_GH, "x")),
        ("authorization", format!("Bearer {PH_GH}")),
        ("authorization", basic("u", &format!("{PH_GH}x"))),
        ("proxy-authorization", basic("x-access-token", PH_GH)),
        ("authorization", format!("Basic {PH_GH}")),
    ];
    for (header, value) in cases {
        send_h1(
            &h.info,
            HOST_GH,
            get(HOST_GH, "/")
                .header(header, value.as_str())
                .body(full(""))
                .unwrap(),
        )
        .await;
        let seen = up.last();
        assert_eq!(seen.header(header).unwrap(), value, "header {header}");
        assert_no_secret(&seen.all_text());
        let decoded = seen
            .header(header)
            .and_then(|v| v.strip_prefix("Basic ").map(|b| B64.decode(b)))
            .and_then(Result::ok)
            .map(|b| String::from_utf8_lossy(&b).into_owned())
            .unwrap_or_default();
        assert!(!decoded.contains(REAL_GH));
    }

    // Password containing a colon keeps everything after the first colon.
    let up2 = start_upstream().await;
    let h2 = start_proxy(&up2, true);
    send_h1(
        &h2.info,
        HOST_GH,
        get(HOST_GH, "/")
            .header("authorization", basic("user:name", PH_GH))
            .body(full(""))
            .unwrap(),
    )
    .await;
    // "user:name:<ph>" splits at the first colon: password is "name:<ph>".
    assert_eq!(
        up2.last().header("authorization").unwrap(),
        basic("user:name", PH_GH)
    );
}

#[tokio::test(flavor = "multi_thread")]
async fn fm05b_token_form_is_swapped_like_gh_sends_it() {
    // gh sends `Authorization: token <t>` (D-24). One Authorization binding
    // accepts bearer, basic-password and token forms.
    let up = start_upstream().await;
    let h = start_proxy(&up, true);
    let mut bindings = default_bindings();
    for b in bindings.iter_mut().filter(|b| b.name == "GH_TOKEN") {
        b.headers = vec![
            header_rule("authorization", HeaderForm::Bearer),
            header_rule("authorization", HeaderForm::BasicPassword),
            header_rule("authorization", HeaderForm::Token),
        ];
    }
    h.proxy.set_bindings(bindings).unwrap();

    let sent = [
        (format!("token {PH_GH}"), format!("token {REAL_GH}")),
        (format!("Token {PH_GH}"), format!("token {REAL_GH}")),
        (format!("Bearer {PH_GH}"), format!("Bearer {REAL_GH}")),
        (
            basic("x-access-token", PH_GH),
            basic("x-access-token", REAL_GH),
        ),
    ];
    for (value, expected) in sent {
        send_h1(
            &h.info,
            HOST_GH,
            get(HOST_GH, "/user")
                .header("authorization", value.as_str())
                .body(full(""))
                .unwrap(),
        )
        .await;
        assert_eq!(up.last().header("authorization").unwrap(), expected);
    }

    // Not injected: no space, a longer token, or the token form on another header.
    let cases: Vec<(&str, String)> = vec![
        ("authorization", format!("token{PH_GH}")),
        ("authorization", format!("token {PH_GH}x")),
        ("x-api-key", format!("token {PH_GH}")),
    ];
    for (header, value) in cases {
        send_h1(
            &h.info,
            HOST_GH,
            get(HOST_GH, "/")
                .header(header, value.as_str())
                .body(full(""))
                .unwrap(),
        )
        .await;
        let seen = up.last();
        assert_eq!(seen.header(header).unwrap(), value, "header {header}");
        assert_no_secret(&seen.all_text());
    }
}

#[tokio::test(flavor = "multi_thread")]
async fn fm06_split_or_repeated_placeholder_is_not_injected() {
    let up = start_upstream().await;
    let h = start_proxy(&up, true);
    let half = PH_A.len() / 2;

    // Split across two headers.
    send_h1(
        &h.info,
        HOST_A,
        get(HOST_A, "/")
            .header("authorization", format!("Bearer {}", &PH_A[..half]))
            .header("authorization", PH_A[half..].to_string())
            .body(full(""))
            .unwrap(),
    )
    .await;
    assert_no_secret(&up.last().all_text());

    // Same header repeated with the full placeholder: ambiguous, refuse.
    send_h1(
        &h.info,
        HOST_A,
        get(HOST_A, "/")
            .header("authorization", format!("Bearer {PH_A}"))
            .header("authorization", format!("Bearer {PH_A}"))
            .body(full(""))
            .unwrap(),
    )
    .await;
    let seen = up.last();
    assert_eq!(seen.header_values("authorization").len(), 2);
    assert_no_secret(&seen.all_text());

    // Placeholder repeated inside one value.
    send_h1(
        &h.info,
        HOST_A,
        get(HOST_A, "/")
            .header("authorization", format!("Bearer {PH_A}{PH_A}"))
            .body(full(""))
            .unwrap(),
    )
    .await;
    assert_no_secret(&up.last().all_text());
    assert!(
        h.log_lines()
            .iter()
            .any(|l| l["event"] == "refuse" && l["name"] == "KEY_A"),
        "{}",
        h.log_text()
    );
}

#[tokio::test(flavor = "multi_thread")]
async fn fm07_websocket_upgrade_is_injected_then_piped() {
    let up = start_upstream().await;
    let h = start_proxy(&up, true);
    let tls = tls_connect(&h.info, HOST_A, &[b"http/1.1"]).await.unwrap();
    let (mut sender, conn) = hyper::client::conn::http1::handshake(TokioIo::new(tls))
        .await
        .unwrap();
    tokio::spawn(conn.with_upgrades());
    let resp = sender
        .send_request(
            get(HOST_A, "/v1/responses")
                .header("connection", "Upgrade")
                .header("upgrade", "websocket")
                .header("sec-websocket-version", "13")
                .header("sec-websocket-key", "dGhlIHNhbXBsZSBub25jZQ==")
                .header("authorization", format!("Bearer {PH_A}"))
                .body(full(""))
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(resp.status(), StatusCode::SWITCHING_PROTOCOLS);
    let seen = up.last();
    assert_eq!(
        seen.header("authorization").unwrap(),
        format!("Bearer {REAL_A}")
    );
    assert_eq!(seen.header("upgrade").unwrap(), "websocket");

    let upgraded = hyper::upgrade::on(resp).await.unwrap();
    let mut io = TokioIo::new(upgraded);
    io.write_all(b"ping").await.unwrap();
    let mut buf = [0u8; 64];
    let n = tokio::time::timeout(Duration::from_secs(5), io.read(&mut buf))
        .await
        .unwrap()
        .unwrap();
    assert_eq!(&buf[..n], b"echo:ping");
}

#[tokio::test(flavor = "multi_thread")]
async fn fm08_sse_streams_without_buffering() {
    let up = start_upstream().await;
    let h = start_proxy(&up, true);
    let tls = tls_connect(&h.info, HOST_A, &[b"http/1.1"]).await.unwrap();
    let (mut sender, conn) = hyper::client::conn::http1::handshake(TokioIo::new(tls))
        .await
        .unwrap();
    tokio::spawn(conn);
    // Headers and the first event must arrive while upstream is still
    // holding the rest of the stream.
    let resp = tokio::time::timeout(
        Duration::from_secs(5),
        sender.send_request(
            get(HOST_A, "/sse")
                .header("authorization", format!("Bearer {PH_A}"))
                .header("accept", "text/event-stream")
                .body(full(""))
                .unwrap(),
        ),
    )
    .await
    .expect("response headers arrived before upstream finished")
    .unwrap();
    assert_eq!(resp.status(), 200);
    let mut body = resp.into_body();
    // Upstream holds the second event until we release the gate, so the
    // first one only arrives here if the proxy streams.
    let first = tokio::time::timeout(Duration::from_secs(5), body.frame())
        .await
        .expect("first SSE event arrived before upstream finished")
        .unwrap()
        .unwrap();
    assert_eq!(
        first.into_data().unwrap(),
        Bytes::from_static(b"data: one\n\n")
    );
    up.sse_gate.notify_one();
    let rest = tokio::time::timeout(Duration::from_secs(5), body.collect())
        .await
        .unwrap()
        .unwrap()
        .to_bytes();
    assert_eq!(rest, Bytes::from_static(b"data: two\n\n"));
}

#[tokio::test(flavor = "multi_thread")]
async fn fm09_log_never_contains_values_or_placeholders() {
    let up = start_upstream().await;
    let h = start_proxy(&up, true);
    // A mix of injections, refusals, mismatches, local answers, and a path
    // that itself carries a placeholder.
    let requests: Vec<(&str, Request<TestBody>)> = vec![
        (
            HOST_A,
            get(HOST_A, &format!("/p/{PH_A}?key={PH_B}"))
                .header("authorization", format!("Bearer {PH_A}"))
                .body(full(""))
                .unwrap(),
        ),
        (
            HOST_B,
            get(HOST_B, "/")
                .header("authorization", format!("Bearer {PH_A}"))
                .header("x-api-key", PH_B)
                .body(full(""))
                .unwrap(),
        ),
        (
            HOST_B,
            get(HOST_A, "/")
                .header("authorization", format!("Bearer {PH_A}"))
                .body(full(""))
                .unwrap(),
        ),
        (
            HOST_GH,
            get(HOST_GH, "/")
                .header("authorization", basic("x", PH_GH))
                .body(full(""))
                .unwrap(),
        ),
        (
            HOST_LOCAL,
            Request::builder()
                .method("POST")
                .uri("/oauth/token")
                .header("host", HOST_LOCAL)
                .body(full(format!("refresh_token={PH_A}")))
                .unwrap(),
        ),
    ];
    for (sni, req) in requests {
        send_h1(&h.info, sni, req).await;
    }
    let text = h.log_text();
    assert!(!text.is_empty());
    for needle in [REAL_A, REAL_B, REAL_GH, PH_A, PH_B, PH_GH] {
        assert!(!text.contains(needle), "log contains {needle}: {text}");
    }
    let b64_real = B64.encode(format!("x:{REAL_GH}"));
    assert!(!text.contains(&b64_real));
    let lines = h.log_lines();
    for line in &lines {
        for key in ["ts", "event", "name", "host", "method", "path", "status"] {
            assert!(line.get(key).is_some(), "missing {key} in {line}");
        }
    }
    let events: Vec<_> = lines.iter().map(|l| l["event"].as_str().unwrap()).collect();
    assert!(events.contains(&"inject"));
    assert!(events.contains(&"refuse"));
    assert!(events.contains(&"local"));
    let injected: Vec<_> = lines
        .iter()
        .filter(|l| l["event"] == "inject")
        .map(|l| l["name"].as_str().unwrap().to_string())
        .collect();
    assert!(injected.contains(&"KEY_A".to_string()));
    assert!(injected.contains(&"KEY_B".to_string()));
    assert!(injected.contains(&"GH_TOKEN".to_string()));
}

#[tokio::test(flavor = "multi_thread")]
async fn fm10_panic_in_one_connection_does_not_kill_the_proxy() {
    let up = start_upstream().await;
    let h = start_proxy(&up, true);

    // The resolver panics for BOOM.
    let r = send_h1(
        &h.info,
        HOST_BOOM,
        get(HOST_BOOM, "/")
            .header("authorization", format!("Bearer {PH_BOOM}"))
            .body(full(""))
            .unwrap(),
    )
    .await;
    assert_eq!(r.status, StatusCode::BAD_GATEWAY);
    assert_eq!(
        up.count(),
        0,
        "a failed resolve must not forward the request"
    );

    // A local handler panics.
    let r = send_h1(
        &h.info,
        HOST_LOCAL,
        Request::builder()
            .method("POST")
            .uri("/oauth/token?panic=1")
            .header("host", HOST_LOCAL)
            .body(full(""))
            .unwrap(),
    )
    .await;
    assert_eq!(r.status, StatusCode::BAD_GATEWAY);

    // A connection that sends garbage instead of TLS.
    let mut raw = raw_connect(&h.info).await.unwrap();
    raw.write_all(b"\x16\x03\x01\xff\xffgarbage").await.ok();
    drop(raw);

    // The proxy still serves new connections.
    let r = send_h1(
        &h.info,
        HOST_A,
        get(HOST_A, "/")
            .header("authorization", format!("Bearer {PH_A}"))
            .body(full(""))
            .unwrap(),
    )
    .await;
    assert_eq!(r.status, 200);
    assert_eq!(
        up.last().header("authorization").unwrap(),
        format!("Bearer {REAL_A}")
    );
    assert!(h.log_lines().iter().any(|l| l["event"] == "error"));
}

#[tokio::test(flavor = "multi_thread")]
async fn resolver_none_leaves_the_placeholder() {
    let up = start_upstream().await;
    let mut h = start_proxy(&up, true);
    h.proxy.set_resolver(Arc::new(|_name: &str| Ok(None)));
    send_h1(
        &h.info,
        HOST_A,
        get(HOST_A, "/")
            .header("authorization", format!("Bearer {PH_A}"))
            .body(full(""))
            .unwrap(),
    )
    .await;
    assert_eq!(
        up.last().header("authorization").unwrap(),
        format!("Bearer {PH_A}")
    );
    h.proxy.stop();
}

#[tokio::test(flavor = "multi_thread")]
async fn local_route_is_answered_and_never_forwarded() {
    let up = start_upstream().await;
    let h = start_proxy(&up, true);
    let r = send_h1(
        &h.info,
        HOST_LOCAL,
        Request::builder()
            .method("POST")
            .uri("/oauth/token")
            .header("host", HOST_LOCAL)
            .header("content-type", "application/x-www-form-urlencoded")
            .body(full("grant_type=refresh_token"))
            .unwrap(),
    )
    .await;
    assert_eq!(r.status, 200);
    assert_eq!(
        r.body,
        Bytes::from_static(br#"{"access_token":"placeholder"}"#)
    );
    assert_eq!(up.count(), 0);
    let calls = h.handler_calls.lock().unwrap().clone();
    assert_eq!(calls.len(), 1);
    assert_eq!(calls[0].method, "POST");
    assert_eq!(calls[0].path, "/oauth/token");
    assert_eq!(calls[0].body, b"grant_type=refresh_token");
    assert!(
        calls[0]
            .headers
            .iter()
            .any(|(k, v)| k == "content-type" && v == "application/x-www-form-urlencoded")
    );
}

#[tokio::test(flavor = "multi_thread")]
async fn bindings_update_live_and_removal_stops_injection() {
    let up = start_upstream().await;
    let h = start_proxy(&up, true);
    let mut bindings = default_bindings();
    bindings.retain(|b| b.name != "KEY_A");
    h.proxy.set_bindings(bindings).unwrap();
    // a.test is no longer bound to anything: no certificate.
    assert!(tls_connect(&h.info, HOST_A, &[b"http/1.1"]).await.is_err());
    // Re-adding works without a restart.
    h.proxy.set_bindings(default_bindings()).unwrap();
    let r = send_h1(
        &h.info,
        HOST_A,
        get(HOST_A, "/")
            .header("authorization", format!("Bearer {PH_A}"))
            .body(full(""))
            .unwrap(),
    )
    .await;
    assert_eq!(r.status, 200);
    assert_eq!(
        up.last().header("authorization").unwrap(),
        format!("Bearer {REAL_A}")
    );
}

#[tokio::test(flavor = "multi_thread")]
async fn each_start_has_a_fresh_ca_and_stop_closes_the_listener() {
    let up = start_upstream().await;
    let mut h1 = start_proxy(&up, true);
    let h2 = start_proxy(&up, true);
    assert_ne!(h1.info.ca_cert_pem, h2.info.ca_cert_pem);
    assert!(
        h1.info
            .ca_cert_pem
            .starts_with("-----BEGIN CERTIFICATE-----")
    );
    assert!(!h1.info.ca_cert_pem.contains("PRIVATE KEY"));
    let path = h1.info.address.strip_prefix("unix:").unwrap().to_string();
    h1.proxy.stop();
    assert!(UnixStream::connect(&path).await.is_err());
}

#[test]
fn rejects_invalid_bindings() {
    let mut proxy = CredentialProxy::new(ProxyOptions {
        listen: "tcp:127.0.0.1:0".into(),
        log_path: scratch("x.log"),
        upstream_extra_roots_pem: None,
        upstream_addr_overrides: HashMap::new(),
    })
    .unwrap();
    let bad = |placeholder: &str, host: &str, header: &str| Binding {
        name: "N".into(),
        placeholder: placeholder.into(),
        hosts: vec![host.into()],
        headers: vec![header_rule(header, HeaderForm::Bearer)],
    };
    assert!(
        proxy
            .set_bindings(vec![bad("", HOST_A, "authorization")])
            .is_err()
    );
    assert!(
        proxy
            .set_bindings(vec![bad("short", HOST_A, "authorization")])
            .is_err()
    );
    assert!(
        proxy
            .set_bindings(vec![bad("has space in it!!", HOST_A, "authorization")])
            .is_err()
    );
    assert!(
        proxy
            .set_bindings(vec![bad(PH_A, "", "authorization")])
            .is_err()
    );
    assert!(
        proxy
            .set_bindings(vec![bad(PH_A, HOST_A, "bad header")])
            .is_err()
    );
    assert!(
        proxy
            .set_bindings(vec![bad(PH_A, HOST_A, "authorization")])
            .is_ok()
    );
    assert!(
        CredentialProxy::new(ProxyOptions {
            listen: "unix:relative.sock".into(),
            log_path: scratch("y.log"),
            upstream_extra_roots_pem: None,
            upstream_addr_overrides: HashMap::new(),
        })
        .is_err()
    );
    proxy.stop();
}

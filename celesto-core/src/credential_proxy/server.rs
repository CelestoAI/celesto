//! Guest-facing side: TLS termination, Host checks, injection, forwarding.

use super::inject::{self, Refusal};
use super::log::Event;
use super::upstream::{BoxError, ProxyBody};
use super::{Listen, LocalRoute, ProxyError, Shared};
use bytes::Bytes;
use futures_util::FutureExt as _;
use http_body_util::{BodyExt, Empty, Full, Limited};
use hyper::body::Incoming;
use hyper::header::{self, HeaderMap, HeaderName, HeaderValue};
use hyper::http::uri::Authority;
use hyper::{Request, Response, StatusCode, Uri, Version};
use hyper_util::rt::{TokioExecutor, TokioIo};
use std::collections::HashMap;
use std::convert::Infallible;
use std::panic::AssertUnwindSafe;
use std::path::PathBuf;
use std::sync::Arc;
use std::sync::atomic::Ordering;
use std::time::Duration;
use tokio::io::{AsyncRead, AsyncWrite};
use tokio::net::{TcpListener, UnixListener};
use tokio::sync::watch;
use tokio_rustls::LazyConfigAcceptor;

const HANDSHAKE_TIMEOUT: Duration = Duration::from_secs(10);
const LOCAL_BODY_LIMIT: usize = 1024 * 1024;

pub(crate) enum Listener {
    Unix(UnixListener, PathBuf),
    Tcp(TcpListener),
}

impl Listener {
    /// Bind synchronously; must run inside the proxy runtime's context.
    pub fn bind(listen: &Listen) -> Result<Self, ProxyError> {
        let io = |e: std::io::Error| ProxyError::Io(e.to_string());
        match listen {
            Listen::Unix(path) => {
                #[cfg(unix)]
                {
                    use std::os::unix::fs::FileTypeExt;
                    if let Ok(meta) = std::fs::symlink_metadata(path)
                        && meta.file_type().is_socket()
                    {
                        let _ = std::fs::remove_file(path);
                    }
                }
                let listener = UnixListener::bind(path).map_err(io)?;
                #[cfg(unix)]
                {
                    use std::os::unix::fs::PermissionsExt;
                    std::fs::set_permissions(path, std::fs::Permissions::from_mode(0o600))
                        .map_err(io)?;
                }
                Ok(Listener::Unix(listener, path.clone()))
            }
            Listen::Tcp(addr) => {
                let listener = std::net::TcpListener::bind(addr).map_err(io)?;
                listener.set_nonblocking(true).map_err(io)?;
                Ok(Listener::Tcp(TcpListener::from_std(listener).map_err(io)?))
            }
        }
    }

    pub fn address(&self) -> String {
        match self {
            Listener::Unix(_, path) => format!("unix:{}", path.display()),
            Listener::Tcp(l) => match l.local_addr() {
                Ok(addr) => format!("tcp:{addr}"),
                Err(_) => "tcp:".to_string(),
            },
        }
    }
}

pub(crate) async fn serve(
    listener: Listener,
    shared: Arc<Shared>,
    mut shutdown: watch::Receiver<bool>,
) {
    loop {
        let accepted = tokio::select! {
            _ = shutdown.changed() => return,
            accepted = accept(&listener, &shared) => accepted,
        };
        if !accepted {
            tokio::time::sleep(Duration::from_millis(50)).await;
        }
    }
}

async fn accept(listener: &Listener, shared: &Arc<Shared>) -> bool {
    match listener {
        Listener::Unix(l, _) => match l.accept().await {
            Ok((io, _)) => {
                tokio::spawn(connection(shared.clone(), io));
                true
            }
            Err(_) => false,
        },
        Listener::Tcp(l) => match l.accept().await {
            Ok((io, _)) => {
                let _ = io.set_nodelay(true);
                tokio::spawn(connection(shared.clone(), io));
                true
            }
            Err(_) => false,
        },
    }
}

struct ActiveGuard(Arc<Shared>);

impl Drop for ActiveGuard {
    fn drop(&mut self) {
        self.0.active.fetch_sub(1, Ordering::Relaxed);
    }
}

#[allow(clippy::too_many_arguments)]
fn emit(
    shared: &Shared,
    event: &str,
    name: Option<&str>,
    host: Option<&str>,
    method: Option<&str>,
    path: Option<&str>,
    status: Option<u16>,
    reason: Option<&str>,
) {
    shared.log.write(Event {
        ts: String::new(),
        event,
        name,
        host,
        method,
        path,
        status,
        reason,
    });
}

async fn connection<IO>(shared: Arc<Shared>, io: IO)
where
    IO: AsyncRead + AsyncWrite + Unpin + Send + 'static,
{
    shared.connections.fetch_add(1, Ordering::Relaxed);
    shared.active.fetch_add(1, Ordering::Relaxed);
    let _guard = ActiveGuard(shared.clone());
    // D-16: a panic ends this connection only.
    if AssertUnwindSafe(connection_inner(shared.clone(), io))
        .catch_unwind()
        .await
        .is_err()
    {
        emit(
            &shared,
            "error",
            None,
            None,
            None,
            None,
            None,
            Some("panic"),
        );
    }
}

async fn connection_inner<IO>(shared: Arc<Shared>, io: IO)
where
    IO: AsyncRead + AsyncWrite + Unpin + Send + 'static,
{
    let acceptor = LazyConfigAcceptor::new(rustls::server::Acceptor::default(), io);
    let Ok(Ok(start)) = tokio::time::timeout(HANDSHAKE_TIMEOUT, acceptor).await else {
        return;
    };
    let config = shared.config();
    let Some(sni) = start
        .client_hello()
        .server_name()
        .map(|s| s.to_ascii_lowercase())
    else {
        emit(
            &shared,
            "refuse",
            None,
            None,
            None,
            None,
            None,
            Some("no_sni"),
        );
        return;
    };
    if !config.hosts.contains(&sni) {
        let host = inject::redact(&config, &sni);
        emit(
            &shared,
            "refuse",
            None,
            Some(&host),
            None,
            None,
            None,
            Some("unknown_host"),
        );
        return;
    }
    let Some(ca) = shared.ca() else { return };
    let tls_config = match ca.server_config(&sni) {
        Ok(c) => c,
        Err(_) => {
            emit(
                &shared,
                "error",
                None,
                Some(&sni),
                None,
                None,
                None,
                Some("certificate_failed"),
            );
            return;
        }
    };
    let Ok(Ok(tls)) = tokio::time::timeout(HANDSHAKE_TIMEOUT, start.into_stream(tls_config)).await
    else {
        return;
    };
    let h2 = tls.get_ref().1.alpn_protocol() == Some(b"h2");
    let sni = Arc::new(sni);
    let service = hyper::service::service_fn(move |req| {
        let shared = shared.clone();
        let sni = sni.clone();
        async move {
            let response = AssertUnwindSafe(request(shared.clone(), &sni, req))
                .catch_unwind()
                .await
                .unwrap_or_else(|_| {
                    emit(
                        &shared,
                        "error",
                        None,
                        Some(&sni),
                        None,
                        None,
                        Some(502),
                        Some("panic"),
                    );
                    status_only(StatusCode::BAD_GATEWAY)
                });
            Ok::<_, Infallible>(response)
        }
    });
    let builder = hyper_util::server::conn::auto::Builder::new(TokioExecutor::new());
    let builder = if h2 {
        builder.http2_only()
    } else {
        builder.http1_only()
    };
    let _ = builder
        .serve_connection_with_upgrades(TokioIo::new(tls), service)
        .await;
}

fn empty() -> ProxyBody {
    Empty::<Bytes>::new()
        .map_err(|never| match never {})
        .boxed_unsync()
}

fn status_only(status: StatusCode) -> Response<ProxyBody> {
    let mut response = Response::new(empty());
    *response.status_mut() = status;
    response
}

fn normalize_authority(value: &str, sni: &str) -> bool {
    if value.contains('@') {
        return false;
    }
    let Ok(authority) = value.parse::<Authority>() else {
        return false;
    };
    if authority.port_u16().is_some_and(|p| p != 443) {
        return false;
    }
    authority.host().eq_ignore_ascii_case(sni)
}

/// `Host` (and the request target's authority, if any) must equal SNI.
fn authority_matches(req: &Request<Incoming>, sni: &str) -> bool {
    let mut candidates: Vec<&str> = Vec::new();
    if let Some(authority) = req.uri().authority() {
        candidates.push(authority.as_str());
    }
    let hosts: Vec<&HeaderValue> = req.headers().get_all(header::HOST).iter().collect();
    if hosts.len() > 1 {
        return false;
    }
    if let Some(host) = hosts.first() {
        match host.to_str() {
            Ok(h) => candidates.push(h),
            Err(_) => return false,
        }
    }
    !candidates.is_empty() && candidates.iter().all(|c| normalize_authority(c, sni))
}

const HOP_BY_HOP: &[&str] = &[
    "connection",
    "keep-alive",
    "proxy-connection",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
];

fn connection_tokens(headers: &HeaderMap) -> Vec<String> {
    headers
        .get_all(header::CONNECTION)
        .iter()
        .filter_map(|v| v.to_str().ok())
        .flat_map(|v| v.split(','))
        .map(|t| t.trim().to_ascii_lowercase())
        .filter(|t| !t.is_empty())
        .collect()
}

fn strip_hop_by_hop(headers: &mut HeaderMap, keep_upgrade: bool) {
    for token in connection_tokens(headers) {
        if keep_upgrade && token == "upgrade" {
            continue;
        }
        if let Ok(name) = HeaderName::from_bytes(token.as_bytes()) {
            headers.remove(name);
        }
    }
    let upgrade = headers.get(header::UPGRADE).cloned();
    for name in HOP_BY_HOP {
        headers.remove(*name);
    }
    if keep_upgrade && let Some(upgrade) = upgrade {
        headers.insert(header::CONNECTION, HeaderValue::from_static("upgrade"));
        headers.insert(header::UPGRADE, upgrade);
    }
}

fn is_upgrade(req: &Request<Incoming>) -> bool {
    req.version() == Version::HTTP_11
        && req.headers().contains_key(header::UPGRADE)
        && connection_tokens(req.headers())
            .iter()
            .any(|t| t == "upgrade")
}

struct Ctx<'a> {
    shared: &'a Shared,
    host: &'a str,
    method: String,
    path: String,
}

impl Ctx<'_> {
    fn emit(&self, event: &str, name: Option<&str>, status: Option<u16>, reason: Option<&str>) {
        emit(
            self.shared,
            event,
            name,
            Some(self.host),
            Some(&self.method),
            Some(&self.path),
            status,
            reason,
        );
    }

    fn fail(&self, status: StatusCode, reason: &str) -> Response<ProxyBody> {
        self.emit("error", None, Some(status.as_u16()), Some(reason));
        status_only(status)
    }
}

async fn request(
    shared: Arc<Shared>,
    sni: &str,
    mut req: Request<Incoming>,
) -> Response<ProxyBody> {
    let config = shared.config();
    let ctx = Ctx {
        shared: &shared,
        host: sni,
        method: req.method().as_str().to_string(),
        path: inject::redact(&config, req.uri().path()),
    };

    if !authority_matches(&req, sni) {
        ctx.emit("refuse", None, Some(421), Some("host_mismatch"));
        return status_only(StatusCode::MISDIRECTED_REQUEST);
    }

    if let Some(route) = config
        .routes
        .iter()
        .find(|r| r.host == sni && r.path == req.uri().path())
    {
        return local(&ctx, route, req).await;
    }

    let mut plan = inject::plan(&config, sni, req.headers(), req.uri());
    let mut values: HashMap<String, Option<String>> = HashMap::new();
    let mut injected: Vec<String> = Vec::new();
    for m in &plan.matches {
        if !values.contains_key(&m.name) {
            let value = match resolve(&shared, &m.name).await {
                Ok(v) => v,
                Err(()) => return ctx.fail(StatusCode::BAD_GATEWAY, "resolver_failed"),
            };
            values.insert(m.name.clone(), value);
        }
        match values.get(&m.name).and_then(|v| v.as_deref()) {
            Some(real) => {
                if inject::apply(req.headers_mut(), m, real).is_err() {
                    return ctx.fail(StatusCode::BAD_GATEWAY, "invalid_value");
                }
                if !injected.contains(&m.name) {
                    injected.push(m.name.clone());
                }
            }
            None => {
                if !plan.refusals.iter().any(|r| r.name == m.name) {
                    plan.refusals.push(Refusal {
                        name: m.name.clone(),
                        reason: "no_value",
                    });
                }
            }
        }
    }
    drop(values);

    forward(&ctx, sni, req, &injected, &plan.refusals).await
}

async fn resolve(shared: &Shared, name: &str) -> Result<Option<String>, ()> {
    let Some(resolver) = shared.resolver() else {
        return Ok(None);
    };
    let name = name.to_string();
    match tokio::task::spawn_blocking(move || resolver(&name)).await {
        Ok(Ok(value)) => Ok(value),
        _ => Err(()),
    }
}

async fn forward(
    ctx: &Ctx<'_>,
    sni: &str,
    mut req: Request<Incoming>,
    injected: &[String],
    refusals: &[Refusal],
) -> Response<ProxyBody> {
    let Some(upstream) = ctx.shared.upstream() else {
        return ctx.fail(StatusCode::SERVICE_UNAVAILABLE, "stopping");
    };
    let upgrade = is_upgrade(&req);
    let downstream_upgrade = upgrade.then(|| hyper::upgrade::on(&mut req));
    let (mut parts, body) = req.into_parts();
    strip_hop_by_hop(&mut parts.headers, upgrade);
    parts.headers.remove(header::HOST);
    let target = parts
        .uri
        .path_and_query()
        .map(|p| p.as_str().to_string())
        .unwrap_or_else(|| "/".to_string());
    parts.uri = match Uri::builder()
        .scheme("https")
        .authority(sni)
        .path_and_query(target)
        .build()
    {
        Ok(uri) => uri,
        Err(_) => return ctx.fail(StatusCode::BAD_REQUEST, "bad_target"),
    };
    parts.version = Version::HTTP_11;
    let body = body.map_err(|e| Box::new(e) as BoxError).boxed_unsync();
    let client = if upgrade {
        &upstream.http1
    } else {
        &upstream.any
    };
    let mut response = match client.request(Request::from_parts(parts, body)).await {
        Ok(r) => r,
        Err(_) => return ctx.fail(StatusCode::BAD_GATEWAY, "upstream_failed"),
    };
    let status = response.status().as_u16();
    for name in injected {
        ctx.shared.mark_used(name);
        ctx.emit("inject", Some(name), Some(status), None);
    }
    for refusal in refusals {
        ctx.emit(
            "refuse",
            Some(&refusal.name),
            Some(status),
            Some(refusal.reason),
        );
    }

    if let Some(downstream_upgrade) = downstream_upgrade
        && response.status() == StatusCode::SWITCHING_PROTOCOLS
    {
        let upstream_upgrade = hyper::upgrade::on(&mut response);
        tokio::spawn(async move {
            let (Ok(down), Ok(up)) = tokio::join!(downstream_upgrade, upstream_upgrade) else {
                return;
            };
            let _ =
                tokio::io::copy_bidirectional(&mut TokioIo::new(down), &mut TokioIo::new(up)).await;
        });
        let (parts, _) = response.into_parts();
        return Response::from_parts(parts, empty());
    }

    let (mut parts, body) = response.into_parts();
    strip_hop_by_hop(&mut parts.headers, false);
    parts.version = Version::HTTP_11;
    // Frames pass through as they arrive: SSE is never buffered.
    Response::from_parts(
        parts,
        body.map_err(|e| Box::new(e) as BoxError).boxed_unsync(),
    )
}

async fn local(ctx: &Ctx<'_>, route: &LocalRoute, req: Request<Incoming>) -> Response<ProxyBody> {
    let Some(handler) = ctx.shared.handler(&route.handler) else {
        return ctx.fail(StatusCode::BAD_GATEWAY, "no_handler");
    };
    let (parts, body) = req.into_parts();
    let body = match Limited::new(body, LOCAL_BODY_LIMIT).collect().await {
        Ok(b) => b.to_bytes().to_vec(),
        Err(_) => return ctx.fail(StatusCode::PAYLOAD_TOO_LARGE, "body_too_large"),
    };
    let request = super::LocalRequest {
        method: parts.method.as_str().to_string(),
        path: parts
            .uri
            .path_and_query()
            .map(|p| p.as_str().to_string())
            .unwrap_or_else(|| "/".to_string()),
        headers: parts
            .headers
            .iter()
            .filter_map(|(k, v)| {
                v.to_str()
                    .ok()
                    .map(|v| (k.as_str().to_string(), v.to_string()))
            })
            .collect(),
        body,
    };
    let reply = match tokio::task::spawn_blocking(move || handler(request)).await {
        Ok(Ok(reply)) => reply,
        _ => return ctx.fail(StatusCode::BAD_GATEWAY, "handler_failed"),
    };
    let Ok(status) = StatusCode::from_u16(reply.status) else {
        return ctx.fail(StatusCode::BAD_GATEWAY, "handler_failed");
    };
    let mut response = Response::new(
        Full::new(Bytes::from(reply.body))
            .map_err(|never| match never {})
            .boxed_unsync(),
    );
    *response.status_mut() = status;
    for (k, v) in reply.headers {
        let (Ok(k), Ok(v)) = (
            HeaderName::from_bytes(k.as_bytes()),
            HeaderValue::from_str(&v),
        ) else {
            return ctx.fail(StatusCode::BAD_GATEWAY, "handler_failed");
        };
        response.headers_mut().append(k, v);
    }
    strip_hop_by_hop(response.headers_mut(), false);
    response.headers_mut().remove(header::CONTENT_LENGTH);
    ctx.emit("local", Some(&route.handler), Some(status.as_u16()), None);
    response
}

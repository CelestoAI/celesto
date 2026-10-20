//! Connections from the proxy to the real hosts.
//!
//! The real address is resolved on the host machine, never taken from the
//! guest, and verified against standard roots: Mozilla's bundle plus the
//! host's own trust store.

use super::ProxyError;
use super::ca::provider;
use bytes::Bytes;
use futures_util::future::BoxFuture;
use http_body_util::combinators::UnsyncBoxBody;
use hyper_rustls::HttpsConnector;
use hyper_util::client::legacy::Client;
use hyper_util::client::legacy::connect::HttpConnector;
use hyper_util::client::legacy::connect::dns::{GaiResolver, Name};
use hyper_util::rt::TokioExecutor;
use std::collections::HashMap;
use std::net::SocketAddr;
use std::sync::Arc;
use std::task::{Context, Poll};
use std::time::Duration;
use tower_service::Service;

pub(crate) type BoxError = Box<dyn std::error::Error + Send + Sync>;
pub(crate) type ProxyBody = UnsyncBoxBody<Bytes, BoxError>;
type Connector = HttpsConnector<HttpConnector<Dns>>;

#[derive(Clone)]
pub(crate) struct Dns {
    overrides: Arc<HashMap<String, SocketAddr>>,
    gai: GaiResolver,
}

impl Service<Name> for Dns {
    type Response = std::vec::IntoIter<SocketAddr>;
    type Error = std::io::Error;
    type Future = BoxFuture<'static, Result<Self::Response, Self::Error>>;

    fn poll_ready(&mut self, _cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
        Poll::Ready(Ok(()))
    }

    fn call(&mut self, name: Name) -> Self::Future {
        if let Some(addr) = self.overrides.get(name.as_str()) {
            let addr = *addr;
            return Box::pin(async move { Ok(vec![addr].into_iter()) });
        }
        let mut gai = self.gai.clone();
        Box::pin(async move {
            let addrs: Vec<SocketAddr> = gai.call(name).await?.collect();
            Ok(addrs.into_iter())
        })
    }
}

pub(crate) struct Upstream {
    /// Offers h2 and http/1.1.
    pub any: Client<Connector, ProxyBody>,
    /// http/1.1 only, for WebSocket Upgrade requests.
    pub http1: Client<Connector, ProxyBody>,
}

fn roots(extra_pem: Option<&str>) -> Result<rustls::RootCertStore, ProxyError> {
    let mut roots = rustls::RootCertStore::empty();
    roots.extend(webpki_roots::TLS_SERVER_ROOTS.iter().cloned());
    for cert in rustls_native_certs::load_native_certs().certs {
        let _ = roots.add(cert);
    }
    if let Some(pem) = extra_pem {
        for cert in rustls_pemfile::certs(&mut pem.as_bytes()) {
            let cert = cert.map_err(|e| ProxyError::Tls(e.to_string()))?;
            roots
                .add(cert)
                .map_err(|e| ProxyError::Tls(e.to_string()))?;
        }
    }
    Ok(roots)
}

impl Upstream {
    pub fn new(
        extra_roots_pem: Option<&str>,
        overrides: HashMap<String, SocketAddr>,
    ) -> Result<Self, ProxyError> {
        let roots = roots(extra_roots_pem)?;
        let tls = rustls::ClientConfig::builder_with_provider(provider())
            .with_safe_default_protocol_versions()
            .map_err(|e| ProxyError::Tls(e.to_string()))?
            .with_root_certificates(roots)
            .with_no_client_auth();
        let dns = Dns {
            overrides: Arc::new(overrides),
            gai: GaiResolver::new(),
        };
        let http = || {
            let mut http = HttpConnector::new_with_resolver(dns.clone());
            http.enforce_http(false);
            http.set_nodelay(true);
            http.set_connect_timeout(Some(Duration::from_secs(15)));
            http
        };
        let any = hyper_rustls::HttpsConnectorBuilder::new()
            .with_tls_config(tls.clone())
            .https_only()
            .enable_http1()
            .enable_http2()
            .wrap_connector(http());
        let http1 = hyper_rustls::HttpsConnectorBuilder::new()
            .with_tls_config(tls)
            .https_only()
            .enable_http1()
            .wrap_connector(http());
        let client = |connector| {
            Client::builder(TokioExecutor::new())
                .pool_idle_timeout(Duration::from_secs(60))
                .build(connector)
        };
        Ok(Upstream {
            any: client(any),
            http1: client(http1),
        })
    }
}

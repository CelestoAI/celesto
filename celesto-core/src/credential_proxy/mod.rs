//! Per-sandbox credential proxy (D-08).
//!
//! The guest holds placeholders, never real secrets. Guest traffic for bound
//! hosts is routed here. The proxy terminates TLS with a leaf minted from a
//! fresh in-memory CA (D-14), checks that HTTP `Host` matches TLS SNI, swaps
//! an exact placeholder for its real value in the headers named by the
//! binding (D-05 lock 2, D-19), and forwards the request to the real host.
//!
//! The Rust API here is wrapped for Python by `python.rs` as
//! `celesto_core._ffi._CredentialProxy`.

mod ca;
mod inject;
mod log;
pub(crate) mod python;
mod server;
mod upstream;

#[cfg(test)]
mod tests;

use serde::Deserialize;
use std::collections::{HashMap, HashSet};
use std::net::SocketAddr;
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex, RwLock};
use std::time::Duration;

/// How a placeholder appears in a header.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum HeaderForm {
    /// `Bearer <placeholder>`
    Bearer,
    /// `<placeholder>`
    Raw,
    /// `Basic base64(user:<placeholder>)`
    BasicPassword,
    /// `token <placeholder>`, as the gh CLI sends it (D-24)
    Token,
}

#[derive(Clone, Debug, Deserialize)]
pub struct HeaderRule {
    pub header: String,
    pub form: HeaderForm,
}

/// One placeholder the guest may send, and where its real value may go.
#[derive(Clone, Debug, Deserialize)]
pub struct Binding {
    pub name: String,
    pub placeholder: String,
    pub hosts: Vec<String>,
    pub headers: Vec<HeaderRule>,
}

/// A request the proxy answers itself and never forwards.
#[derive(Clone, Debug, Deserialize)]
pub struct LocalRoute {
    pub host: String,
    pub path: String,
    pub handler: String,
}

#[derive(Clone, Debug)]
pub struct LocalRequest {
    pub method: String,
    /// Path and query, as the guest sent them.
    pub path: String,
    pub headers: Vec<(String, String)>,
    pub body: Vec<u8>,
}

#[derive(Clone, Debug)]
pub struct LocalResponse {
    pub status: u16,
    pub headers: Vec<(String, String)>,
    pub body: Vec<u8>,
}

/// Returns the real value for a binding name, `Ok(None)` to not inject.
pub type Resolver = Arc<dyn Fn(&str) -> Result<Option<String>, String> + Send + Sync>;
pub type LocalHandler = Arc<dyn Fn(LocalRequest) -> Result<LocalResponse, String> + Send + Sync>;

pub struct ProxyOptions {
    /// `unix:/abs/path.sock` or `tcp:IP:PORT`.
    pub listen: String,
    pub log_path: PathBuf,
    /// Test only: extra PEM roots trusted for upstream connections.
    pub upstream_extra_roots_pem: Option<String>,
    /// Test only: connect to this address instead of resolving the host.
    pub upstream_addr_overrides: HashMap<String, SocketAddr>,
}

#[derive(Clone, Debug)]
pub struct StartInfo {
    /// Same format as `listen`, with the bound port filled in for TCP.
    pub address: String,
    pub ca_cert_pem: String,
}

#[derive(Clone, Debug, Default)]
pub struct Stats {
    pub connections: u64,
    pub active: u64,
    pub last_used: HashMap<String, String>,
}

#[derive(Debug, thiserror::Error)]
pub enum ProxyError {
    #[error("{0}")]
    Invalid(String),
    #[error("{0}")]
    Io(String),
    #[error("{0}")]
    Tls(String),
}

#[derive(Clone, Debug)]
pub(crate) enum Listen {
    Unix(PathBuf),
    Tcp(SocketAddr),
}

impl Listen {
    fn parse(value: &str) -> Result<Self, ProxyError> {
        if let Some(path) = value.strip_prefix("unix:") {
            let path = PathBuf::from(path);
            if !path.is_absolute() {
                return Err(ProxyError::Invalid(format!(
                    "listen path must be absolute: {value}"
                )));
            }
            Ok(Listen::Unix(path))
        } else if let Some(addr) = value.strip_prefix("tcp:") {
            addr.parse()
                .map(Listen::Tcp)
                .map_err(|_| ProxyError::Invalid(format!("invalid listen address: {value}")))
        } else {
            Err(ProxyError::Invalid(format!(
                "listen must start with 'unix:' or 'tcp:': {value}"
            )))
        }
    }
}

/// Validated, read-only routing table. Swapped whole on every update.
#[derive(Default)]
pub(crate) struct Config {
    pub bindings: Vec<Binding>,
    pub routes: Vec<LocalRoute>,
    /// Hosts the proxy terminates TLS for.
    pub hosts: HashSet<String>,
}

impl Config {
    fn build(bindings: Vec<Binding>, routes: Vec<LocalRoute>) -> Self {
        let mut hosts = HashSet::new();
        for b in &bindings {
            hosts.extend(b.hosts.iter().cloned());
        }
        for r in &routes {
            hosts.insert(r.host.clone());
        }
        Config {
            bindings,
            routes,
            hosts,
        }
    }
}

fn valid_host(host: &str) -> bool {
    !host.is_empty()
        && host.len() <= 253
        && host
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'.')
        && !host.starts_with('.')
        && !host.ends_with('.')
}

fn validate_binding(mut b: Binding) -> Result<Binding, ProxyError> {
    let invalid = |why: &str| ProxyError::Invalid(format!("binding '{}': {why}", b.name));
    if b.name.is_empty() {
        return Err(ProxyError::Invalid("binding name is empty".into()));
    }
    if b.placeholder.len() < 16 || !b.placeholder.bytes().all(|c| c.is_ascii_graphic()) {
        return Err(invalid(
            "placeholder must be at least 16 printable characters without spaces",
        ));
    }
    if b.hosts.is_empty() {
        return Err(invalid("needs at least one host"));
    }
    for host in &mut b.hosts {
        *host = host.to_ascii_lowercase();
        if !valid_host(host) {
            return Err(invalid("invalid host"));
        }
    }
    if b.headers.is_empty() {
        return Err(invalid("needs at least one header rule"));
    }
    for rule in &mut b.headers {
        rule.header = rule.header.to_ascii_lowercase();
        if hyper::header::HeaderName::from_bytes(rule.header.as_bytes()).is_err() {
            return Err(invalid("invalid header name"));
        }
    }
    Ok(b)
}

fn validate_route(mut r: LocalRoute) -> Result<LocalRoute, ProxyError> {
    r.host = r.host.to_ascii_lowercase();
    if !valid_host(&r.host) {
        return Err(ProxyError::Invalid(format!(
            "local route has an invalid host: {}",
            r.host
        )));
    }
    if !r.path.starts_with('/') || r.handler.is_empty() {
        return Err(ProxyError::Invalid(
            "local route needs a path starting with '/' and a handler".into(),
        ));
    }
    Ok(r)
}

/// State shared between the Python-facing object and connection tasks.
pub(crate) struct Shared {
    pub config: RwLock<Arc<Config>>,
    pub resolver: RwLock<Option<Resolver>>,
    pub handlers: RwLock<HashMap<String, LocalHandler>>,
    pub ca: RwLock<Option<Arc<ca::Ca>>>,
    pub log: log::Logger,
    pub upstream: RwLock<Option<Arc<upstream::Upstream>>>,
    pub connections: AtomicU64,
    pub active: AtomicU64,
    pub last_used: Mutex<HashMap<String, String>>,
}

fn read<T: ?Sized>(lock: &RwLock<T>) -> std::sync::RwLockReadGuard<'_, T> {
    lock.read().unwrap_or_else(|e| e.into_inner())
}

fn write<T: ?Sized>(lock: &RwLock<T>) -> std::sync::RwLockWriteGuard<'_, T> {
    lock.write().unwrap_or_else(|e| e.into_inner())
}

impl Shared {
    pub fn config(&self) -> Arc<Config> {
        read(&self.config).clone()
    }

    pub fn resolver(&self) -> Option<Resolver> {
        read(&self.resolver).clone()
    }

    pub fn handler(&self, id: &str) -> Option<LocalHandler> {
        read(&self.handlers).get(id).cloned()
    }

    pub fn ca(&self) -> Option<Arc<ca::Ca>> {
        read(&self.ca).clone()
    }

    pub fn upstream(&self) -> Option<Arc<upstream::Upstream>> {
        read(&self.upstream).clone()
    }

    pub fn mark_used(&self, name: &str) {
        self.last_used
            .lock()
            .unwrap_or_else(|e| e.into_inner())
            .insert(name.to_string(), log::now_rfc3339());
    }
}

struct Running {
    runtime: tokio::runtime::Runtime,
    shutdown: tokio::sync::watch::Sender<bool>,
    socket_path: Option<PathBuf>,
}

pub struct CredentialProxy {
    listen: Listen,
    options: ProxyOptions,
    shared: Arc<Shared>,
    running: Option<Running>,
}

impl CredentialProxy {
    pub fn new(options: ProxyOptions) -> Result<Self, ProxyError> {
        let listen = Listen::parse(&options.listen)?;
        if !options.log_path.is_absolute() {
            return Err(ProxyError::Invalid("log_path must be absolute".into()));
        }
        let shared = Arc::new(Shared {
            config: RwLock::new(Arc::new(Config::default())),
            resolver: RwLock::new(None),
            handlers: RwLock::new(HashMap::new()),
            ca: RwLock::new(None),
            log: log::Logger::new(options.log_path.clone()),
            upstream: RwLock::new(None),
            connections: AtomicU64::new(0),
            active: AtomicU64::new(0),
            last_used: Mutex::new(HashMap::new()),
        });
        Ok(CredentialProxy {
            listen,
            options,
            shared,
            running: None,
        })
    }

    /// Generate a fresh CA, open the listener, and start serving.
    pub fn start(&mut self) -> Result<StartInfo, ProxyError> {
        if self.running.is_some() {
            return Err(ProxyError::Invalid(
                "credential proxy is already running".into(),
            ));
        }
        self.shared
            .log
            .open()
            .map_err(|e| ProxyError::Io(e.to_string()))?;
        let ca = Arc::new(ca::Ca::generate()?);
        let ca_cert_pem = ca.cert_pem().to_string();
        *write(&self.shared.ca) = Some(ca);

        let runtime = tokio::runtime::Builder::new_multi_thread()
            .worker_threads(2)
            .thread_name("celesto-credential-proxy")
            .enable_all()
            .build()
            .map_err(|e| ProxyError::Io(e.to_string()))?;

        let upstream = {
            let _guard = runtime.enter();
            upstream::Upstream::new(
                self.options.upstream_extra_roots_pem.as_deref(),
                self.options.upstream_addr_overrides.clone(),
            )?
        };
        *write(&self.shared.upstream) = Some(Arc::new(upstream));

        let (shutdown, shutdown_rx) = tokio::sync::watch::channel(false);
        let listener = {
            let _guard = runtime.enter();
            server::Listener::bind(&self.listen)?
        };
        let address = listener.address();
        let socket_path = match &self.listen {
            Listen::Unix(path) => Some(path.clone()),
            Listen::Tcp(_) => None,
        };
        runtime.spawn(server::serve(listener, self.shared.clone(), shutdown_rx));
        self.running = Some(Running {
            runtime,
            shutdown,
            socket_path,
        });
        Ok(StartInfo {
            address,
            ca_cert_pem,
        })
    }

    pub fn set_bindings(&self, bindings: Vec<Binding>) -> Result<(), ProxyError> {
        let bindings = bindings
            .into_iter()
            .map(validate_binding)
            .collect::<Result<Vec<_>, _>>()?;
        let mut seen = HashSet::new();
        for b in &bindings {
            if !seen.insert(b.placeholder.clone()) {
                return Err(ProxyError::Invalid(format!(
                    "binding '{}' reuses another binding's placeholder",
                    b.name
                )));
            }
        }
        let mut config = write(&self.shared.config);
        *config = Arc::new(Config::build(bindings, config.routes.clone()));
        Ok(())
    }

    pub fn set_local_routes(&self, routes: Vec<LocalRoute>) -> Result<(), ProxyError> {
        let routes = routes
            .into_iter()
            .map(validate_route)
            .collect::<Result<Vec<_>, _>>()?;
        let mut config = write(&self.shared.config);
        *config = Arc::new(Config::build(config.bindings.clone(), routes));
        Ok(())
    }

    pub fn set_resolver(&self, resolver: Resolver) {
        *write(&self.shared.resolver) = Some(resolver);
    }

    pub fn set_local_handler(&self, id: &str, handler: LocalHandler) {
        write(&self.shared.handlers).insert(id.to_string(), handler);
    }

    pub fn stats(&self) -> Stats {
        Stats {
            connections: self.shared.connections.load(Ordering::Relaxed),
            active: self.shared.active.load(Ordering::Relaxed),
            last_used: self
                .shared
                .last_used
                .lock()
                .unwrap_or_else(|e| e.into_inner())
                .clone(),
        }
    }

    /// Stop serving and drop the CA private key. Safe to call twice.
    pub fn stop(&mut self) {
        if tokio::runtime::Handle::try_current().is_ok() {
            // Called from async code (tests): blocking here would panic.
            self.stop_with(|runtime| runtime.shutdown_background());
        } else {
            self.stop_with(|runtime| runtime.shutdown_timeout(Duration::from_secs(2)));
        }
    }

    fn stop_with(&mut self, shutdown: impl FnOnce(tokio::runtime::Runtime)) {
        if let Some(running) = self.running.take() {
            let _ = running.shutdown.send(true);
            shutdown(running.runtime);
            if let Some(path) = running.socket_path {
                let _ = std::fs::remove_file(path);
            }
        }
        *write(&self.shared.ca) = None;
        *write(&self.shared.upstream) = None;
        self.shared.log.close();
    }
}

impl Drop for CredentialProxy {
    fn drop(&mut self) {
        // Never block in drop: a callback may be waiting on the caller's lock.
        self.stop_with(|runtime| runtime.shutdown_background());
    }
}

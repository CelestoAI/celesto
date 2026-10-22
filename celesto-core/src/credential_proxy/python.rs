//! PyO3 wrapper: `celesto_core._ffi._CredentialProxy`.
//!
//! Python callbacks run on proxy threads with the GIL held only while they run.

use super::{
    Binding, CredentialProxy, LocalRequest, LocalResponse, LocalRoute, ProxyError, ProxyOptions,
};
use pyo3::exceptions::{PyOSError, PyRuntimeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyDict};
use std::collections::HashMap;
use std::net::SocketAddr;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};

fn to_py(error: ProxyError) -> PyErr {
    match error {
        ProxyError::Invalid(m) => PyValueError::new_err(m),
        ProxyError::Io(m) => PyOSError::new_err(m),
        ProxyError::Tls(m) => PyRuntimeError::new_err(m),
    }
}

#[pyclass(name = "_CredentialProxy", module = "celesto_core._ffi")]
pub(crate) struct PyCredentialProxy {
    inner: Mutex<CredentialProxy>,
}

impl PyCredentialProxy {
    fn lock(&self) -> std::sync::MutexGuard<'_, CredentialProxy> {
        self.inner.lock().unwrap_or_else(|e| e.into_inner())
    }
}

#[pymethods]
impl PyCredentialProxy {
    #[new]
    #[pyo3(signature = (listen, log_path, upstream_ca_pem=None, upstream_overrides=None))]
    fn new(
        listen: String,
        log_path: String,
        upstream_ca_pem: Option<String>,
        upstream_overrides: Option<HashMap<String, String>>,
    ) -> PyResult<Self> {
        let mut overrides = HashMap::new();
        for (host, addr) in upstream_overrides.unwrap_or_default() {
            let addr: SocketAddr = addr
                .parse()
                .map_err(|_| PyValueError::new_err(format!("invalid address: {addr}")))?;
            overrides.insert(host.to_ascii_lowercase(), addr);
        }
        let proxy = CredentialProxy::new(ProxyOptions {
            listen,
            log_path: PathBuf::from(log_path),
            upstream_extra_roots_pem: upstream_ca_pem,
            upstream_addr_overrides: overrides,
        })
        .map_err(to_py)?;
        Ok(PyCredentialProxy {
            inner: Mutex::new(proxy),
        })
    }

    fn start<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let info = py.detach(|| self.lock().start()).map_err(to_py)?;
        let out = PyDict::new(py);
        out.set_item("address", info.address)?;
        out.set_item("ca_cert_pem", info.ca_cert_pem)?;
        Ok(out)
    }

    /// `bindings_json`: JSON list of Binding objects (without `source`).
    fn set_bindings(&self, py: Python<'_>, bindings_json: &str) -> PyResult<()> {
        let bindings: Vec<Binding> = serde_json::from_str(bindings_json)
            .map_err(|e| PyValueError::new_err(format!("invalid bindings: {e}")))?;
        py.detach(|| self.lock().set_bindings(bindings))
            .map_err(to_py)
    }

    fn set_local_routes(&self, py: Python<'_>, routes_json: &str) -> PyResult<()> {
        let routes: Vec<LocalRoute> = serde_json::from_str(routes_json)
            .map_err(|e| PyValueError::new_err(format!("invalid local routes: {e}")))?;
        py.detach(|| self.lock().set_local_routes(routes))
            .map_err(to_py)
    }

    fn set_resolver(&self, py: Python<'_>, func: Py<PyAny>) {
        let func = Arc::new(func);
        let resolver = Arc::new(move |name: &str| {
            Python::attach(|py| {
                let result = func
                    .call1(py, (name,))
                    .map_err(|_| "resolver raised".to_string())?;
                if result.is_none(py) {
                    Ok(None)
                } else {
                    result
                        .extract::<String>(py)
                        .map(Some)
                        .map_err(|_| "resolver returned a non-string".to_string())
                }
            })
        });
        py.detach(|| self.lock().set_resolver(resolver));
    }

    fn set_local_handler(&self, py: Python<'_>, handler_id: String, func: Py<PyAny>) {
        let func = Arc::new(func);
        let handler = Arc::new(move |req: LocalRequest| {
            Python::attach(|py| {
                let body = PyBytes::new(py, &req.body);
                let result = func
                    .call1(py, (req.method, req.path, req.headers, body))
                    .map_err(|_| "handler raised".to_string())?;
                let (status, headers, body): (u16, Vec<(String, String)>, Vec<u8>) = result
                    .extract(py)
                    .map_err(|_| "handler returned an invalid response".to_string())?;
                Ok(LocalResponse {
                    status,
                    headers,
                    body,
                })
            })
        });
        py.detach(|| self.lock().set_local_handler(&handler_id, handler));
    }

    fn stats<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let stats = py.detach(|| self.lock().stats());
        let out = PyDict::new(py);
        out.set_item("connections", stats.connections)?;
        out.set_item("active", stats.active)?;
        out.set_item("last_used", stats.last_used)?;
        Ok(out)
    }

    fn stop(&self, py: Python<'_>) {
        py.detach(|| self.lock().stop());
    }
}

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyCredentialProxy>()
}

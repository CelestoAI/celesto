use axum::Router;
#[cfg(any(test, feature = "tcp", all(feature = "vsock", target_os = "linux")))]
use std::io;
#[cfg(any(test, all(feature = "vsock", target_os = "linux")))]
use tokio::io::{AsyncRead, AsyncWrite};
#[cfg(any(test, all(feature = "vsock", target_os = "linux")))]
use tower::ServiceExt;

pub const DEFAULT_LISTEN: &str = "vsock://1024";

pub async fn serve_listen_addr(app: Router, listen: &str) {
    if let Some(port) = listen.strip_prefix("vsock://") {
        let port: u32 = port.parse().expect("vsock port must be a number");
        serve_vsock(app, port).await;
    } else if let Some(addr) = listen.strip_prefix("tcp://") {
        serve_tcp(app, addr).await;
    } else {
        eprintln!(
            "Invalid listen address: {listen}. Use vsock://PORT{}.",
            if cfg!(feature = "tcp") {
                " or tcp://HOST:PORT"
            } else {
                ""
            },
        );
        std::process::exit(1);
    }
}

#[cfg(all(feature = "vsock", target_os = "linux"))]
pub async fn serve_vsock(app: Router, port: u32) {
    use tokio_vsock::{VsockAddr, VsockListener};

    let addr = VsockAddr::new(u32::MAX, port);
    let mut listener = VsockListener::bind(addr).expect("failed to bind vsock");
    tracing::info!("Listening on vsock://{port}");

    loop {
        match listener.accept().await {
            Ok((stream, addr)) => {
                let app = app.clone();
                tokio::spawn(async move {
                    if let Err(error) = handle_vsock_stream(app, stream, addr.cid()).await {
                        tracing::error!("vsock connection error from {addr:?}: {error}");
                    }
                });
            }
            Err(error) => tracing::error!("vsock accept error: {error}"),
        }
    }
}

#[cfg(any(test, all(feature = "vsock", target_os = "linux")))]
pub(crate) fn authorize_host_peer(cid: u32) -> io::Result<()> {
    // VMADDR_CID_HOST is assigned by the kernel. Guest-local loopback and
    // other guests must never reach root operations, including on port 1025.
    if cid == 2 {
        Ok(())
    } else {
        Err(io::Error::new(
            io::ErrorKind::PermissionDenied,
            "guest control connections require the host peer",
        ))
    }
}

#[cfg(any(test, all(feature = "vsock", target_os = "linux")))]
async fn handle_vsock_stream<S>(app: Router, stream: S, peer_cid: u32) -> io::Result<()>
where
    S: AsyncRead + AsyncWrite + Unpin + Send + 'static,
{
    authorize_host_peer(peer_cid)?;
    let io = hyper_util::rt::TokioIo::new(stream);
    let service = hyper::service::service_fn(move |req| {
        let app = app.clone();
        async move { app.oneshot(req).await.map_err(|error| match error {}) }
    });
    hyper::server::conn::http1::Builder::new()
        .serve_connection(io, service)
        .await
        .map_err(io::Error::other)
}

#[cfg(not(all(feature = "vsock", target_os = "linux")))]
pub async fn serve_vsock(_app: Router, _port: u32) {
    eprintln!("vsock support is only available in Linux builds with the vsock feature enabled.");
    std::process::exit(1);
}

#[cfg(feature = "tcp")]
fn authenticated_tcp_router(app: Router, token: &str) -> io::Result<Router> {
    use axum::{
        extract::Request,
        http::StatusCode,
        middleware::{self, Next},
        response::IntoResponse,
    };
    if token.len() < 32 {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "set CELESTO_GUEST_AGENT_TCP_TOKEN to a random token of at least 32 characters before starting the TCP listener",
        ));
    }
    let expected = format!("Bearer {token}").into_bytes();
    Ok(
        app.layer(middleware::from_fn(move |request: Request, next: Next| {
            let expected = expected.clone();
            async move {
                let authorized = request.headers().get("authorization").is_some_and(|value| {
                    let supplied = value.as_bytes();
                    supplied.len() == expected.len()
                        && supplied
                            .iter()
                            .zip(&expected)
                            .fold(0u8, |difference, (left, right)| difference | (left ^ right))
                            == 0
                });
                if authorized {
                    next.run(request).await
                } else {
                    StatusCode::UNAUTHORIZED.into_response()
                }
            }
        })),
    )
}

#[cfg(feature = "tcp")]
pub async fn serve_tcp(app: Router, addr: &str) {
    let token = std::env::var("CELESTO_GUEST_AGENT_TCP_TOKEN").unwrap_or_default();
    let app = match authenticated_tcp_router(app, &token) {
        Ok(app) => app,
        Err(error) => {
            eprintln!("{error}");
            std::process::exit(1);
        }
    };
    tracing::info!("Listening on tcp://{addr}");
    let listener = tokio::net::TcpListener::bind(addr)
        .await
        .expect("failed to bind TCP listener");
    axum::serve(listener, app).await.expect("TCP server failed");
}

#[cfg(not(feature = "tcp"))]
pub async fn serve_tcp(_app: Router, _addr: &str) {
    eprintln!("TCP listener support is disabled in public Celesto guest-agent builds.");
    std::process::exit(1);
}

#[cfg(test)]
mod tests {
    use super::*;
    use tokio::io::{AsyncReadExt, AsyncWriteExt};

    #[cfg(feature = "tcp")]
    #[tokio::test]
    async fn tcp_requires_configured_token_before_routing() {
        let token = "0123456789abcdef0123456789abcdef";
        let app =
            || Router::new().route("/", axum::routing::get(|| async { "privileged operation" }));
        assert!(authenticated_tcp_router(app(), "").is_err());
        for authorization in [
            None,
            Some("Bearer wrong"),
            Some("Bearer 0123456789abcdef0123456789abcdef"),
        ] {
            let router = authenticated_tcp_router(app(), token).unwrap();
            let mut request = axum::http::Request::builder().uri("/");
            if let Some(authorization) = authorization {
                request = request.header("Authorization", authorization);
            }
            let response = router
                .oneshot(request.body(axum::body::Body::empty()).unwrap())
                .await
                .unwrap();
            let expected = if authorization == Some("Bearer 0123456789abcdef0123456789abcdef") {
                200
            } else {
                401
            };
            assert_eq!(response.status().as_u16(), expected);
        }
    }

    #[tokio::test]
    async fn only_host_cid_reaches_http_routes() {
        for cid in [0, 1, 2, 3, u32::MAX] {
            let app = Router::new().route(
                "/",
                axum::routing::get(|| async { "host request accepted" }),
            );
            let (mut client, stream) = tokio::io::duplex(4096);
            client
                .write_all(b"GET / HTTP/1.1\r\nHost: guest\r\nConnection: close\r\n\r\n")
                .await
                .unwrap();
            let result = handle_vsock_stream(app, stream, cid).await;
            let mut response = Vec::new();
            client.read_to_end(&mut response).await.unwrap();
            if cid == 2 {
                result.unwrap();
                assert!(String::from_utf8_lossy(&response).contains("host request accepted"));
            } else {
                assert_eq!(result.unwrap_err().kind(), io::ErrorKind::PermissionDenied);
                assert!(response.is_empty());
            }
        }
    }
}

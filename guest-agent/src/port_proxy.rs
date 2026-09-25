//! Host-only byte relay from vsock to a guest loopback TCP listener.
//!
//! Protocol: `CPX1` + big-endian u16 port. Port zero probes capability.
//! The guest replies with one byte: 0 ready, 1 invalid port, 2 dial failed,
//! 3 busy. After 0 for a nonzero port, both directions carry unframed bytes.

#[cfg(any(all(feature = "vsock", target_os = "linux"), test))]
use std::{io, time::Duration};

#[cfg(any(all(feature = "vsock", target_os = "linux"), test))]
use tokio::{
    io::{AsyncRead, AsyncReadExt, AsyncWrite, AsyncWriteExt, copy_bidirectional},
    net::TcpStream,
    time::timeout,
};

pub const DEFAULT_PORT: u32 = 1026;
#[cfg(any(all(feature = "vsock", target_os = "linux"), test))]
const MAGIC: &[u8; 4] = b"CPX1";
#[cfg(all(feature = "vsock", target_os = "linux"))]
const MAX_CONNECTIONS: usize = 64;
#[cfg(any(all(feature = "vsock", target_os = "linux"), test))]
const HANDSHAKE_TIMEOUT: Duration = Duration::from_secs(5);
#[cfg(any(all(feature = "vsock", target_os = "linux"), test))]
const DIAL_TIMEOUT: Duration = Duration::from_secs(5);

#[cfg(any(all(feature = "vsock", target_os = "linux"), test))]
async fn handle_stream<S>(mut stream: S) -> io::Result<()>
where
    S: AsyncRead + AsyncWrite + Unpin,
{
    let mut request = [0_u8; 6];
    timeout(HANDSHAKE_TIMEOUT, stream.read_exact(&mut request)).await??;
    if &request[..4] != MAGIC {
        return Err(io::Error::new(
            io::ErrorKind::InvalidData,
            "invalid port proxy protocol",
        ));
    }
    let port = u16::from_be_bytes([request[4], request[5]]);
    if port == 0 {
        stream.write_all(&[0]).await?;
        return Ok(());
    }
    if port < 1024 {
        stream.write_all(&[1]).await?;
        return Ok(());
    }
    let mut app = match timeout(DIAL_TIMEOUT, TcpStream::connect(("127.0.0.1", port))).await {
        Ok(Ok(app)) => app,
        _ => {
            stream.write_all(&[2]).await?;
            return Ok(());
        }
    };
    stream.write_all(&[0]).await?;
    copy_bidirectional(&mut stream, &mut app).await?;
    Ok(())
}

#[cfg(all(feature = "vsock", target_os = "linux"))]
pub async fn serve_vsock_port_proxy(port: u32) {
    use std::sync::Arc;
    use tokio::sync::Semaphore;
    use tokio_vsock::{VsockAddr, VsockListener};

    let mut listener = VsockListener::bind(VsockAddr::new(u32::MAX, port))
        .expect("failed to bind guest port proxy vsock listener");
    let permits = Arc::new(Semaphore::new(MAX_CONNECTIONS));
    tracing::info!(port, "guest port proxy listening on vsock");
    loop {
        match listener.accept().await {
            Ok((mut stream, peer)) => {
                if peer.cid() != 2 {
                    tracing::warn!(cid = peer.cid(), "rejected non-host port proxy peer");
                    continue;
                }
                let permit = permits.clone().try_acquire_owned();
                tokio::spawn(async move {
                    let Ok(_permit) = permit else {
                        let _ = stream.write_all(&[3]).await;
                        return;
                    };
                    if let Err(error) = handle_stream(stream).await {
                        tracing::debug!(%error, "guest port proxy connection ended");
                    }
                });
            }
            Err(error) => tracing::error!(%error, "guest port proxy accept failed"),
        }
    }
}

#[cfg(not(all(feature = "vsock", target_os = "linux")))]
pub async fn serve_vsock_port_proxy(_port: u32) {
    std::future::pending::<()>().await;
}

#[cfg(test)]
mod tests {
    use super::*;
    use tokio::io::duplex;
    use tokio::net::TcpListener;

    #[tokio::test]
    async fn capability_probe_does_not_open_tcp() {
        let (mut client, guest) = duplex(64);
        let task = tokio::spawn(handle_stream(guest));
        client.write_all(b"CPX1\0\0").await.unwrap();
        let mut status = [9];
        client.read_exact(&mut status).await.unwrap();
        assert_eq!(status, [0]);
        task.await.unwrap().unwrap();
    }

    #[tokio::test]
    async fn only_connects_to_guest_loopback() {
        let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
        let port = listener.local_addr().unwrap().port();
        let app = tokio::spawn(async move {
            let (mut socket, _) = listener.accept().await.unwrap();
            let mut content = [0; 5];
            socket.read_exact(&mut content).await.unwrap();
            assert_eq!(&content, b"hello");
            socket.write_all(b"world").await.unwrap();
        });
        let (mut client, guest) = duplex(64);
        let proxy = tokio::spawn(handle_stream(guest));
        let mut request = *b"CPX1\0\0";
        request[4..].copy_from_slice(&port.to_be_bytes());
        client.write_all(&request).await.unwrap();
        let mut status = [9];
        client.read_exact(&mut status).await.unwrap();
        assert_eq!(status, [0]);
        client.write_all(b"hello").await.unwrap();
        let mut response = [0; 5];
        client.read_exact(&mut response).await.unwrap();
        assert_eq!(&response, b"world");
        client.shutdown().await.unwrap();
        app.await.unwrap();
        proxy.await.unwrap().unwrap();
    }

    #[tokio::test]
    async fn rejects_privileged_tcp_port() {
        let (mut client, guest) = duplex(64);
        let task = tokio::spawn(handle_stream(guest));
        client.write_all(b"CPX1\0\x16").await.unwrap();
        let mut status = [9];
        client.read_exact(&mut status).await.unwrap();
        assert_eq!(status, [1]);
        task.await.unwrap().unwrap();
    }
}

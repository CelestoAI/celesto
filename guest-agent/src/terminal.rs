use once_cell::sync::Lazy;
use portable_pty::{CommandBuilder, NativePtySystem, PtySize, PtySystem};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::io::{self, Read, Write};
use std::os::fd::{AsRawFd, FromRawFd};
use std::path::Path;
use std::sync::mpsc as std_mpsc;
use std::sync::{
    Arc,
    atomic::{AtomicBool, Ordering},
};
use tokio::io::{AsyncRead, AsyncReadExt, AsyncWrite, AsyncWriteExt};
use tokio::sync::{Semaphore, mpsc, oneshot};

pub const DEFAULT_TERMINAL_PORT: u32 = 1025;
pub const MAX_FRAME_PAYLOAD_BYTES: usize = 1024 * 1024;
pub const MAX_CONCURRENT_TERMINALS: usize = 8;
const MAX_HANDSHAKE_BYTES: usize = 16 * 1024;
const MAX_ROWS: u16 = 1000;
const MAX_COLS: u16 = 1000;

pub const FRAME_STDIN: u8 = 1;
pub const FRAME_RESIZE: u8 = 2;
pub const FRAME_CLOSE: u8 = 3;
pub const FRAME_OUTPUT: u8 = 101;
pub const FRAME_EXIT: u8 = 102;
pub const FRAME_ERROR: u8 = 103;

static TERMINAL_SEMAPHORE: Lazy<Semaphore> = Lazy::new(|| Semaphore::new(MAX_CONCURRENT_TERMINALS));

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Frame {
    pub frame_type: u8,
    pub payload: Vec<u8>,
}

#[derive(Debug, Deserialize)]
pub struct TerminalOpenRequest {
    pub version: u32,
    pub rows: u16,
    pub cols: u16,
    #[serde(default)]
    pub term: Option<String>,
    #[serde(default)]
    pub cwd: Option<String>,
    #[serde(default)]
    pub env: HashMap<String, String>,
}

#[derive(Debug, Serialize)]
pub struct TerminalOpenResponse {
    pub ok: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pid: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct TerminalResizeRequest {
    pub rows: u16,
    pub cols: u16,
}

#[derive(Debug, Serialize)]
pub struct TerminalExit {
    pub exit_code: u32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub signal: Option<String>,
}

pub fn encode_frame(frame_type: u8, payload: &[u8]) -> Result<Vec<u8>, String> {
    if payload.len() > MAX_FRAME_PAYLOAD_BYTES {
        return Err(format!(
            "frame payload exceeds {MAX_FRAME_PAYLOAD_BYTES} bytes"
        ));
    }
    let mut frame = Vec::with_capacity(5 + payload.len());
    frame.push(frame_type);
    frame.extend_from_slice(&(payload.len() as u32).to_be_bytes());
    frame.extend_from_slice(payload);
    Ok(frame)
}

pub fn decode_frame_header(header: &[u8; 5]) -> Result<(u8, usize), String> {
    let len = u32::from_be_bytes([header[1], header[2], header[3], header[4]]) as usize;
    if len > MAX_FRAME_PAYLOAD_BYTES {
        return Err(format!(
            "frame payload exceeds {MAX_FRAME_PAYLOAD_BYTES} bytes"
        ));
    }
    Ok((header[0], len))
}

pub fn terminal_size(rows: u16, cols: u16) -> Result<PtySize, String> {
    if rows == 0 || cols == 0 {
        return Err("terminal size must be greater than zero".to_string());
    }
    if rows > MAX_ROWS || cols > MAX_COLS {
        return Err(format!(
            "terminal size must be at most {MAX_ROWS} rows and {MAX_COLS} columns"
        ));
    }
    Ok(PtySize {
        rows,
        cols,
        pixel_width: 0,
        pixel_height: 0,
    })
}

async fn read_json_line<S>(stream: &mut S) -> io::Result<Vec<u8>>
where
    S: AsyncRead + Unpin,
{
    let mut line = Vec::new();
    loop {
        if line.len() >= MAX_HANDSHAKE_BYTES {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                "terminal handshake is too large",
            ));
        }
        let byte = match stream.read_u8().await {
            Ok(byte) => byte,
            Err(error) if error.kind() == io::ErrorKind::UnexpectedEof => {
                return Err(io::Error::new(
                    io::ErrorKind::UnexpectedEof,
                    "terminal handshake ended early",
                ));
            }
            Err(error) => return Err(error),
        };
        if byte == b'\n' {
            return Ok(line);
        }
        line.push(byte);
    }
}

async fn write_json_line<S>(stream: &mut S, response: &TerminalOpenResponse) -> io::Result<()>
where
    S: AsyncWrite + Unpin,
{
    let mut line = serde_json::to_vec(response).map_err(io::Error::other)?;
    line.push(b'\n');
    stream.write_all(&line).await
}

async fn read_frame<R>(reader: &mut R) -> io::Result<Option<Frame>>
where
    R: AsyncRead + Unpin,
{
    let mut header = [0u8; 5];
    match reader.read_exact(&mut header).await {
        Ok(_) => {}
        Err(error) if error.kind() == io::ErrorKind::UnexpectedEof => return Ok(None),
        Err(error) => return Err(error),
    }
    let (frame_type, len) = decode_frame_header(&header)
        .map_err(|error| io::Error::new(io::ErrorKind::InvalidData, error))?;
    let mut payload = vec![0u8; len];
    reader.read_exact(&mut payload).await?;
    Ok(Some(Frame {
        frame_type,
        payload,
    }))
}

async fn write_frame<W>(writer: &mut W, frame_type: u8, payload: &[u8]) -> io::Result<()>
where
    W: AsyncWrite + Unpin,
{
    let frame = encode_frame(frame_type, payload)
        .map_err(|error| io::Error::new(io::ErrorKind::InvalidInput, error))?;
    writer.write_all(&frame).await
}

fn default_shell() -> &'static str {
    if Path::new("/bin/bash").exists() {
        "/bin/bash"
    } else {
        "/bin/sh"
    }
}

fn command_for_request(req: &TerminalOpenRequest) -> CommandBuilder {
    let mut cmd = CommandBuilder::new(default_shell());
    cmd.arg("-l");
    let term = req.term.as_deref().unwrap_or("xterm-256color");
    cmd.env("TERM", term);
    for (key, value) in &req.env {
        cmd.env(key, value);
    }
    if let Some(cwd) = req.cwd.as_deref().filter(|value| !value.is_empty()) {
        cmd.cwd(cwd);
    }
    cmd
}

fn parse_open_request(line: &[u8]) -> Result<TerminalOpenRequest, String> {
    let req: TerminalOpenRequest = serde_json::from_slice(line)
        .map_err(|error| format!("invalid terminal handshake: {error}"))?;
    if req.version != 1 {
        return Err("unsupported terminal protocol version".to_string());
    }
    terminal_size(req.rows, req.cols)?;
    Ok(req)
}

fn outbound_error(tx: &mpsc::UnboundedSender<Frame>, error: impl Into<String>) {
    let _ = tx.send(Frame {
        frame_type: FRAME_ERROR,
        payload: error.into().into_bytes(),
    });
}

pub async fn handle_terminal_stream<S>(mut stream: S) -> io::Result<()>
where
    S: AsyncRead + AsyncWrite + Unpin + Send + 'static,
{
    let permit = match TERMINAL_SEMAPHORE.try_acquire() {
        Ok(permit) => permit,
        Err(_) => {
            write_json_line(
                &mut stream,
                &TerminalOpenResponse {
                    ok: false,
                    pid: None,
                    error: Some("too many terminal sessions are already open".to_string()),
                },
            )
            .await?;
            return Ok(());
        }
    };

    let line = read_json_line(&mut stream).await?;
    let req = match parse_open_request(&line) {
        Ok(req) => req,
        Err(error) => {
            write_json_line(
                &mut stream,
                &TerminalOpenResponse {
                    ok: false,
                    pid: None,
                    error: Some(error),
                },
            )
            .await?;
            return Ok(());
        }
    };

    let pty_system = NativePtySystem::default();
    let pair = match pty_system.openpty(terminal_size(req.rows, req.cols).unwrap()) {
        Ok(pair) => pair,
        Err(error) => {
            write_json_line(
                &mut stream,
                &TerminalOpenResponse {
                    ok: false,
                    pid: None,
                    error: Some(format!("could not open terminal: {error}")),
                },
            )
            .await?;
            return Ok(());
        }
    };

    // Configure cancellable PTY I/O before starting a child. All descriptor
    // acquisition failures therefore happen before there is a process to reap.
    let mut pty_reader = pair.master.try_clone_reader().map_err(io::Error::other)?;
    let pty_writer = pair.master.take_writer().map_err(io::Error::other)?;
    let master_fd = pair
        .master
        .as_raw_fd()
        .ok_or_else(|| io::Error::other("terminal descriptor is unavailable"))?;
    let flags = unsafe { libc::fcntl(master_fd, libc::F_GETFL) };
    if flags < 0 || unsafe { libc::fcntl(master_fd, libc::F_SETFL, flags | libc::O_NONBLOCK) } < 0 {
        return Err(io::Error::last_os_error());
    }
    let control_fd = unsafe { libc::fcntl(master_fd, libc::F_DUPFD_CLOEXEC, 0) };
    if control_fd < 0 {
        return Err(io::Error::last_os_error());
    }
    let control = unsafe { std::fs::File::from_raw_fd(control_fd) };

    let mut child = match pair.slave.spawn_command(command_for_request(&req)) {
        Ok(child) => child,
        Err(error) => {
            write_json_line(
                &mut stream,
                &TerminalOpenResponse {
                    ok: false,
                    pid: None,
                    error: Some(format!("could not start shell: {error}")),
                },
            )
            .await?;
            return Ok(());
        }
    };
    drop(pair.slave);

    let pid = child.process_id();
    let cancelled = Arc::new(AtomicBool::new(false));
    let cleanup = TerminalCleanup(cancelled.clone());
    let (outbound_tx, mut outbound_rx) = mpsc::unbounded_channel::<Frame>();
    let (done_tx, mut done_rx) = oneshot::channel::<()>();
    let (pty_write_tx, pty_write_rx) = std_mpsc::channel::<Vec<u8>>();
    let writer_cancelled = cancelled.clone();
    let writer =
        std::thread::spawn(move || write_pty_input(pty_writer, pty_write_rx, writer_cancelled));
    let reader_cancelled = cancelled.clone();
    let output_tx = outbound_tx.clone();
    let output =
        std::thread::spawn(move || read_pty_output(&mut pty_reader, output_tx, reader_cancelled));

    let wait_tx = outbound_tx.clone();
    std::thread::spawn(move || {
        // This supervisor retains admission until the child and both PTY
        // workers are gone, including if the async handler is cancelled.
        let _permit = permit;
        let status = loop {
            if cancelled.load(Ordering::Acquire) {
                if let Some(pid) = pid {
                    unsafe {
                        let foreground = libc::tcgetpgrp(control.as_raw_fd());
                        if foreground > 0 {
                            libc::kill(-foreground, libc::SIGKILL);
                        }
                        libc::kill(-(pid as libc::pid_t), libc::SIGKILL);
                        libc::kill(pid as libc::pid_t, libc::SIGKILL);
                    }
                }
                break child.wait();
            }
            match child.try_wait() {
                Ok(Some(status)) => break Ok(status),
                Ok(None) => std::thread::sleep(std::time::Duration::from_millis(10)),
                Err(error) => {
                    let _ = child.kill();
                    let _ = child.wait();
                    break Err(error);
                }
            }
        };
        cancelled.store(true, Ordering::Release);
        let _ = writer.join();
        let _ = output.join();
        match status {
            Ok(status) => {
                let frame = TerminalExit {
                    exit_code: status.exit_code(),
                    signal: status.signal().map(ToOwned::to_owned),
                };
                match serde_json::to_vec(&frame) {
                    Ok(payload) => {
                        let _ = wait_tx.send(Frame {
                            frame_type: FRAME_EXIT,
                            payload,
                        });
                    }
                    Err(error) => {
                        outbound_error(&wait_tx, format!("could not encode shell exit: {error}"))
                    }
                }
            }
            Err(error) => outbound_error(&wait_tx, format!("shell wait failed: {error}")),
        }
        drop(control);
        drop(_permit);
        let _ = done_tx.send(());
    });

    if let Err(error) = write_json_line(
        &mut stream,
        &TerminalOpenResponse {
            ok: true,
            pid,
            error: None,
        },
    )
    .await
    {
        drop(cleanup);
        drop(pty_write_tx);
        let _ = done_rx.await;
        return Err(error);
    }

    let (mut socket_reader, mut socket_writer) = tokio::io::split(stream);
    let mut socket_writer_task = tokio::spawn(async move {
        while let Some(frame) = outbound_rx.recv().await {
            if write_frame(&mut socket_writer, frame.frame_type, &frame.payload)
                .await
                .is_err()
            {
                break;
            }
        }
    });

    let _abort_socket_writer = AbortSocketOnDrop(socket_writer_task.abort_handle());
    let mut session_error = None;
    let mut child_done = false;
    loop {
        tokio::select! {
            frame = read_frame(&mut socket_reader) => {
                let frame = match frame {
                    Ok(frame) => frame,
                    Err(error) => { session_error = Some(error); break; }
                };
                match frame {
                    Some(frame) => match frame.frame_type {
                        FRAME_STDIN => {
                            if pty_write_tx.send(frame.payload).is_err() {
                                break;
                            }
                        }
                        FRAME_RESIZE => {
                            let resize: TerminalResizeRequest = match serde_json::from_slice(&frame.payload) {
                                Ok(resize) => resize,
                                Err(error) => {
                                    outbound_error(&outbound_tx, format!("invalid resize frame: {error}"));
                                    break;
                                }
                            };
                            match terminal_size(resize.rows, resize.cols) {
                                Ok(size) => {
                                    if let Err(error) = pair.master.resize(size) {
                                        outbound_error(&outbound_tx, format!("could not resize terminal: {error}"));
                                    }
                                }
                                Err(error) => {
                                    outbound_error(&outbound_tx, error);
                                    break;
                                }
                            }
                        }
                        FRAME_CLOSE => {
                            break;
                        }
                        other => {
                            outbound_error(&outbound_tx, format!("invalid terminal frame type: {other}"));
                            break;
                        }
                    },
                    None => {
                        break;
                    }
                }
            }
            _ = &mut done_rx => {
                child_done = true;
                break;
            }
            _ = &mut socket_writer_task => {
                session_error = Some(io::Error::new(io::ErrorKind::BrokenPipe, "terminal connection closed"));
                break;
            }
        }
    }

    drop(cleanup);
    drop(pty_write_tx);
    if !child_done {
        let _ = done_rx.await;
    }
    drop(outbound_tx);
    if session_error.is_some()
        || tokio::time::timeout(std::time::Duration::from_secs(1), &mut socket_writer_task)
            .await
            .is_err()
    {
        socket_writer_task.abort();
    }
    match session_error {
        Some(error) => Err(error),
        None => Ok(()),
    }
}

struct AbortSocketOnDrop(tokio::task::AbortHandle);

impl Drop for AbortSocketOnDrop {
    fn drop(&mut self) {
        self.0.abort();
    }
}

struct TerminalCleanup(Arc<AtomicBool>);

impl Drop for TerminalCleanup {
    fn drop(&mut self) {
        self.0.store(true, Ordering::Release);
    }
}

fn read_pty_output(
    reader: &mut Box<dyn Read + Send>,
    tx: mpsc::UnboundedSender<Frame>,
    cancelled: Arc<AtomicBool>,
) {
    let mut buf = [0u8; 8192];
    let mut drain_remaining = MAX_FRAME_PAYLOAD_BYTES;
    loop {
        // Preserve already buffered output after exit, but a background
        // descendant that keeps writing cannot keep this worker alive forever.
        let draining = cancelled.load(Ordering::Acquire);
        if draining && drain_remaining == 0 {
            break;
        }
        match reader.read(&mut buf) {
            Ok(0) => break,
            Ok(n) => {
                if draining {
                    drain_remaining = drain_remaining.saturating_sub(n);
                }
                if tx
                    .send(Frame {
                        frame_type: FRAME_OUTPUT,
                        payload: buf[..n].to_vec(),
                    })
                    .is_err()
                {
                    break;
                }
            }
            Err(error) if error.kind() == io::ErrorKind::Interrupted => continue,
            Err(error) if error.kind() == io::ErrorKind::WouldBlock => {
                if cancelled.load(Ordering::Acquire) {
                    break;
                }
                std::thread::sleep(std::time::Duration::from_millis(10));
            }
            Err(error) => {
                let _ = tx.send(Frame {
                    frame_type: FRAME_ERROR,
                    payload: format!("terminal read failed: {error}").into_bytes(),
                });
                break;
            }
        }
    }
}

fn write_pty_input(
    mut writer: Box<dyn Write + Send>,
    rx: std_mpsc::Receiver<Vec<u8>>,
    cancelled: Arc<AtomicBool>,
) {
    while !cancelled.load(Ordering::Acquire) {
        let payload = match rx.recv_timeout(std::time::Duration::from_millis(10)) {
            Ok(payload) => payload,
            Err(std_mpsc::RecvTimeoutError::Timeout) => continue,
            Err(std_mpsc::RecvTimeoutError::Disconnected) => break,
        };
        let mut remaining = payload.as_slice();
        while !remaining.is_empty() && !cancelled.load(Ordering::Acquire) {
            match writer.write(remaining) {
                Ok(0) => return,
                Ok(written) => remaining = &remaining[written..],
                Err(error) if error.kind() == io::ErrorKind::Interrupted => continue,
                Err(error) if error.kind() == io::ErrorKind::WouldBlock => {
                    std::thread::sleep(std::time::Duration::from_millis(10))
                }
                Err(_) => return,
            }
        }
    }
}

#[cfg(any(test, all(feature = "vsock", target_os = "linux")))]
async fn handle_vsock_terminal_stream<S>(stream: S, peer_cid: u32) -> io::Result<()>
where
    S: AsyncRead + AsyncWrite + Unpin + Send + 'static,
{
    crate::server::authorize_host_peer(peer_cid)?;
    handle_terminal_stream(stream).await
}

#[cfg(all(feature = "vsock", target_os = "linux"))]
pub async fn serve_vsock_terminal(port: u32) {
    use tokio_vsock::{VsockAddr, VsockListener};

    let addr = VsockAddr::new(u32::MAX, port);
    let mut listener = VsockListener::bind(addr).expect("failed to bind terminal vsock");
    tracing::info!("Listening for terminals on vsock://{port}");
    loop {
        match listener.accept().await {
            Ok((stream, addr)) => {
                tokio::spawn(async move {
                    if let Err(error) = handle_vsock_terminal_stream(stream, addr.cid()).await {
                        tracing::error!("terminal connection error from {addr:?}: {error}");
                    }
                });
            }
            Err(error) => tracing::error!("terminal vsock accept error: {error}"),
        }
    }
}

#[cfg(not(all(feature = "vsock", target_os = "linux")))]
pub async fn serve_vsock_terminal(_port: u32) {
    eprintln!(
        "terminal vsock support is only available in Linux builds with the vsock feature enabled."
    );
    std::process::exit(1);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn guest_cids_cannot_open_terminal_sessions() {
        for cid in [0, 1, 3, u32::MAX] {
            let (mut client, stream) = tokio::io::duplex(4096);
            client
                .write_all(b"{\"version\":2,\"rows\":24,\"cols\":80,\"env\":{}}\n")
                .await
                .unwrap();
            let error = handle_vsock_terminal_stream(stream, cid).await.unwrap_err();
            assert_eq!(error.kind(), io::ErrorKind::PermissionDenied);
            let mut response = Vec::new();
            client.read_to_end(&mut response).await.unwrap();
            assert!(response.is_empty());
        }
    }

    #[tokio::test]
    async fn malformed_session_reaps_shell_before_returning() {
        let (mut client, server) = tokio::io::duplex(16384);
        let handler = tokio::spawn(handle_terminal_stream(server));
        client
            .write_all(b"{\"version\":1,\"rows\":24,\"cols\":80,\"env\":{}}\n")
            .await
            .unwrap();
        let response: serde_json::Value =
            serde_json::from_slice(&read_json_line(&mut client).await.unwrap()).unwrap();
        let pid = response["pid"].as_u64().unwrap() as libc::pid_t;
        let mut header = [FRAME_STDIN, 0, 0, 0, 0];
        header[1..].copy_from_slice(&((MAX_FRAME_PAYLOAD_BYTES + 1) as u32).to_be_bytes());
        client.write_all(&header).await.unwrap();
        let result = tokio::time::timeout(std::time::Duration::from_secs(5), handler)
            .await
            .unwrap()
            .unwrap();
        let alive = unsafe { libc::kill(pid, 0) } == 0;
        if alive {
            unsafe {
                libc::kill(pid, libc::SIGKILL);
            }
        }
        assert!(result.is_err());
        assert!(
            !alive,
            "terminal returned while shell {pid} was still alive"
        );
    }

    #[test]
    fn frame_round_trips_header_and_payload() {
        let frame = encode_frame(FRAME_STDIN, b"abc").unwrap();
        assert_eq!(frame[0], FRAME_STDIN);
        let (frame_type, len) = decode_frame_header(&frame[..5].try_into().unwrap()).unwrap();
        assert_eq!(frame_type, FRAME_STDIN);
        assert_eq!(len, 3);
        assert_eq!(&frame[5..], b"abc");
    }

    #[test]
    fn frame_rejects_oversized_payload() {
        let payload = vec![0u8; MAX_FRAME_PAYLOAD_BYTES + 1];
        assert!(encode_frame(FRAME_STDIN, &payload).is_err());

        let mut header = [0u8; 5];
        header[1..].copy_from_slice(&((MAX_FRAME_PAYLOAD_BYTES as u32) + 1).to_be_bytes());
        assert!(decode_frame_header(&header).is_err());
    }

    #[test]
    fn terminal_size_rejects_invalid_values() {
        assert!(terminal_size(24, 80).is_ok());
        assert!(terminal_size(0, 80).is_err());
        assert!(terminal_size(24, 0).is_err());
        assert!(terminal_size(MAX_ROWS + 1, 80).is_err());
        assert!(terminal_size(24, MAX_COLS + 1).is_err());
    }

    #[test]
    fn open_request_validates_version_and_size() {
        let valid = br#"{"version":1,"rows":24,"cols":80,"term":"xterm","cwd":null,"env":{}}"#;
        assert!(parse_open_request(valid).is_ok());

        let bad_version = br#"{"version":2,"rows":24,"cols":80,"env":{}}"#;
        assert!(parse_open_request(bad_version).is_err());

        let bad_size = br#"{"version":1,"rows":0,"cols":80,"env":{}}"#;
        assert!(parse_open_request(bad_size).is_err());
    }

    #[cfg(unix)]
    #[test]
    fn pty_spawn_echo_and_exit() {
        let pty_system = NativePtySystem::default();
        let pair = pty_system
            .openpty(PtySize {
                rows: 24,
                cols: 80,
                pixel_width: 0,
                pixel_height: 0,
            })
            .unwrap();
        let mut cmd = CommandBuilder::new("/bin/sh");
        cmd.arg("-c");
        cmd.arg("printf hello; exit 7");
        let mut child = pair.slave.spawn_command(cmd).unwrap();
        drop(pair.slave);
        let mut reader = pair.master.try_clone_reader().unwrap();
        let mut output = Vec::new();
        reader.read_to_end(&mut output).unwrap();
        let status = child.wait().unwrap();
        assert_eq!(String::from_utf8_lossy(&output), "hello");
        assert_eq!(status.exit_code(), 7);
    }
}

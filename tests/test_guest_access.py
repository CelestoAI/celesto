"""Exercise capability-gated HTTP and WebSocket delivery on real TCP sockets."""

from __future__ import annotations

import hashlib
import http.client
import json
import socket
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

_TOKEN = "a" * 64
_ROOT = Path(__file__).resolve().parents[1]


class _Upstream(BaseHTTPRequestHandler):
    server: ThreadingHTTPServer
    paths: list[str] = []

    def do_GET(self) -> None:
        self.paths.append(self.path)
        if self.headers.get("Upgrade", "").lower() == "websocket":
            import base64

            accept = base64.b64encode(
                hashlib.sha1(
                    (
                        self.headers["Sec-WebSocket-Key"] + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
                    ).encode()
                ).digest()
            ).decode()
            self.send_response(101)
            self.send_header("Upgrade", "websocket")
            self.send_header("Connection", "Upgrade")
            self.send_header("Sec-WebSocket-Accept", accept)
            self.end_headers()
            self.wfile.flush()
            self.connection.sendall(self.rfile.read(4))
            return
        content = json.dumps(
            {
                "path": self.path,
                "webSocketDebuggerUrl": f"ws://127.0.0.1:{self.server.server_port}/devtools/browser/test",
            }
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, *_args: object) -> None:
        pass


@pytest.fixture
def proxy(tmp_path: Path) -> Iterator[int]:
    _Upstream.paths = []
    upstream = ThreadingHTTPServer(("127.0.0.1", 0), _Upstream)
    thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    thread.start()
    with socket.socket() as free:
        free.bind(("127.0.0.1", 0))
        port = free.getsockname()[1]
    token_path = tmp_path / "capability"
    token_path.write_text(_TOKEN)
    token_path.chmod(0o600)
    process = subprocess.Popen(
        [
            sys.executable,
            str(_ROOT / "src/celesto/images/guest_access.py"),
            str(port),
            str(upstream.server_port),
            str(token_path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        for _ in range(100):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                    break
            except OSError:
                if process.poll() is not None:
                    raise AssertionError(process.communicate()) from None
                time.sleep(0.01)
        else:
            raise AssertionError("proxy did not listen")
        yield port
    finally:
        process.terminate()
        process.communicate(timeout=5)
        upstream.shutdown()
        upstream.server_close()
        thread.join(timeout=5)


@contextmanager
def connection(port: int) -> Iterator[http.client.HTTPConnection]:
    client = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    try:
        yield client
    finally:
        client.close()


@pytest.mark.parametrize("path", ["/json/version", "/" + "b" * 64 + "/json/version"])
def test_missing_or_wrong_capability_cannot_reach_upstream(proxy: int, path: str) -> None:
    with connection(proxy) as client:
        client.request("GET", path)
        response = client.getresponse()
        assert response.status == 403
        response.read()
    assert _Upstream.paths == []


def test_capability_http_discovery_rewrites_websocket_url(proxy: int) -> None:
    with connection(proxy) as client:
        client.request("GET", f"/{_TOKEN}/json/version")
        response = client.getresponse()
        assert response.status == 200
        payload = json.loads(response.read())
    assert payload["path"] == "/json/version"
    assert payload["webSocketDebuggerUrl"] == (
        f"ws://127.0.0.1:{proxy}/{_TOKEN}/devtools/browser/test"
    )


def test_capability_websocket_forwards_after_handshake(proxy: int) -> None:
    with socket.create_connection(("127.0.0.1", proxy), timeout=2) as client:
        client.sendall(
            (
                f"GET /{_TOKEN}/devtools/browser/test HTTP/1.1\r\n"
                f"Host: 127.0.0.1:{proxy}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n"
            ).encode()
        )
        header = bytearray()
        while not header.endswith(b"\r\n\r\n"):
            header.extend(client.recv(1))
        assert b"101 Switching Protocols" in header
        client.sendall(b"test")
        assert client.recv(4) == b"test"
    assert _Upstream.paths == ["/devtools/browser/test"]

"""Guest HTTP/WebSocket capability gateway; uses only the Python standard library.

Backing services listen on guest loopback. Only this authenticated listener is
reachable through the guest interface or host forwards. Capabilities are URL
path components so browser viewers and ordinary CDP clients can use them.
"""

from __future__ import annotations

import hmac
import http.client
import json
import re
import select
import socket
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TypeAlias, cast
from urllib.parse import urlsplit, urlunsplit

_MAX_RESPONSE = 8 * 1024 * 1024
_HOP_HEADERS = {"connection", "keep-alive", "transfer-encoding", "proxy-connection"}
_JSONValue: TypeAlias = (
    None | bool | int | float | str | list["_JSONValue"] | dict[str, "_JSONValue"]
)


class AccessServer(ThreadingHTTPServer):
    capability: str
    target_port: int


class AccessHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server: AccessServer

    def setup(self) -> None:
        self.request.settimeout(10)
        super().setup()

    def log_message(self, *_args: object) -> None:
        # Request paths contain credentials and must never appear in logs.
        pass

    def do_GET(self) -> None:
        self._request()

    def do_HEAD(self) -> None:
        self._request()

    def _request(self) -> None:
        self.close_connection = True
        parts = urlsplit(self.path)
        prefix, separator, suffix = parts.path.removeprefix("/").partition("/")
        if (
            parts.scheme
            or parts.netloc
            or not separator
            or not hmac.compare_digest(prefix, self.server.capability)
        ):
            self.send_error(403, "Connection capability required")
            return
        if self.headers.get("Transfer-Encoding") or self.headers.get("Content-Length", "0") != "0":
            self.send_error(400)
            return
        host = self.headers.get("Host", "")
        # Host is used only in returned CDP URLs, never to choose the upstream.
        if not re.fullmatch(r"(?:[A-Za-z0-9.-]+|\[[0-9a-fA-F:]+\])(?::[0-9]{1,5})?", host):
            self.send_error(400)
            return
        path = urlunsplit(("", "", "/" + suffix, parts.query, ""))
        try:
            if self.headers.get("Upgrade", "").lower() == "websocket":
                self._websocket(path)
            else:
                self._http(path, host)
        except (OSError, http.client.HTTPException, ValueError):
            # Do not include exception details or upstream URLs in errors.
            self.close_connection = True

    def _http(self, path: str, host: str) -> None:
        upstream = http.client.HTTPConnection("127.0.0.1", self.server.target_port, timeout=10)
        try:
            upstream.request(self.command, path, headers={"Connection": "close"})
            response = upstream.getresponse()
            body = response.read(_MAX_RESPONSE + 1)
            if len(body) > _MAX_RESPONSE:
                self.send_error(502, "Response too large")
                return
            if "application/json" in response.getheader("Content-Type", "") and body:
                payload = cast(_JSONValue, json.loads(body))

                def rewrite(value: _JSONValue) -> None:
                    if isinstance(value, dict):
                        for key, item in value.items():
                            if key == "webSocketDebuggerUrl" and isinstance(item, str):
                                ws = urlsplit(item)
                                value[key] = urlunsplit(
                                    (
                                        "ws",
                                        host,
                                        f"/{self.server.capability}" + ws.path,
                                        ws.query,
                                        "",
                                    )
                                )
                            else:
                                rewrite(item)
                    elif isinstance(value, list):
                        for item in value:
                            rewrite(item)

                rewrite(payload)
                body = json.dumps(payload).encode()
            self.send_response(response.status)
            for key, value in response.getheaders():
                if key.lower() not in _HOP_HEADERS | {"content-length", "cache-control"}:
                    self.send_header(key, value)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
        finally:
            upstream.close()

    def _websocket(self, path: str) -> None:
        with socket.create_connection(
            ("127.0.0.1", self.server.target_port), timeout=10
        ) as upstream:
            headers = [f"GET {path} HTTP/1.1", f"Host: 127.0.0.1:{self.server.target_port}"]
            # Forward only WebSocket handshake headers, never proxy credentials.
            for key, value in self.headers.items():
                if key.lower() in {"upgrade", "connection", "origin"} or key.lower().startswith(
                    "sec-websocket-"
                ):
                    headers.append(f"{key}: {value}")
            upstream.sendall(("\r\n".join(headers) + "\r\n\r\n").encode("latin-1"))
            response = bytearray()
            while not response.endswith(b"\r\n\r\n"):
                chunk = upstream.recv(1)
                if not chunk or len(response) >= 65536:
                    return
                response.extend(chunk)
            self.connection.sendall(response)
            if b" 101 " not in response.split(b"\r\n", 1)[0]:
                return
            self.connection.settimeout(None)
            upstream.settimeout(None)
            sockets = [self.connection, upstream]
            while True:
                readable, _, _ = select.select(sockets, [], [], 300)
                if not readable:
                    return
                for source in readable:
                    data = source.recv(65536)
                    if not data:
                        return
                    (upstream if source is self.connection else self.connection).sendall(data)


def serve(port: int | str, target_port: int | str, token_path: str | Path) -> None:
    capability = Path(token_path).read_text().strip()
    if not re.fullmatch("[0-9a-f]{64}", capability):
        raise ValueError("invalid capability")
    server = AccessServer(("0.0.0.0", int(port)), AccessHandler)
    server.daemon_threads = True
    server.capability = capability
    server.target_port = int(target_port)
    server.serve_forever()


if __name__ == "__main__":
    serve(*sys.argv[1:])

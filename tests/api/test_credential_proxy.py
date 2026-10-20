"""Credential proxy through its Python API (D-08, D-18, D-19).

Drives ``celesto_core.credential_proxy.CredentialProxy`` the way the per-VM
launcher will: Unix-socket listener, a Python resolver, a Python local handler.
A local TLS upstream records what it receives. The test writes
``artifacts/credential-proxy/upstream-headers.json`` with every header the
upstream saw, with sentinel values replaced by labels so the artifact itself
holds no secret.
"""

from __future__ import annotations

import base64
import json
import shutil
import socket
import ssl
import subprocess
import tempfile
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import pytest

credential_proxy = pytest.importorskip("celesto_core.credential_proxy")

REAL_OPENAI = "sk-SENTINEL-openai-0000000000000000"
REAL_GH = "ghp_SENTINELgithub000000000000000"
PH_OPENAI = "celesto-ph-openai-1111111111111111"
PH_GH = "celesto-ph-github-2222222222222222"
HOSTS = ("api.openai.test", "github.test", "auth.openai.test")
ARTIFACT = (
    Path(__file__).resolve().parents[2] / "artifacts" / "credential-proxy" / "upstream-headers.json"
)


def _openssl(*args: str, cwd: Path) -> None:
    subprocess.run(["openssl", *args], cwd=cwd, check=True, capture_output=True)


def _make_upstream_certs(directory: Path) -> tuple[Path, Path, str]:
    """Test CA plus a leaf for HOSTS. Returns (leaf cert, leaf key, CA PEM)."""
    _openssl(
        "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "2",
        "-keyout", "ca.key", "-out", "ca.pem", "-subj", "/CN=celesto test upstream CA",
        "-addext", "basicConstraints=critical,CA:TRUE",
        "-addext", "keyUsage=critical,keyCertSign,cRLSign",
        cwd=directory,
    )  # fmt: skip
    _openssl(
        "req", "-newkey", "rsa:2048", "-nodes", "-keyout", "leaf.key",
        "-out", "leaf.csr", "-subj", f"/CN={HOSTS[0]}",
        cwd=directory,
    )  # fmt: skip
    (directory / "leaf.ext").write_text(
        "subjectAltName=" + ",".join(f"DNS:{h}" for h in HOSTS) + "\nextendedKeyUsage=serverAuth\n"
    )
    _openssl(
        "x509", "-req", "-in", "leaf.csr", "-CA", "ca.pem", "-CAkey", "ca.key",
        "-CAcreateserial", "-days", "2", "-out", "leaf.pem", "-extfile", "leaf.ext",
        cwd=directory,
    )  # fmt: skip
    return directory / "leaf.pem", directory / "leaf.key", (directory / "ca.pem").read_text()


class _Recorder(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    seen: list[dict[str, Any]] = []

    def _record(self) -> None:
        length = int(self.headers.get("content-length") or 0)
        body = self.rfile.read(length) if length else b""
        type(self).seen.append(
            {
                "method": self.command,
                "path": self.path,
                "headers": [[k.lower(), v] for k, v in self.headers.items()],
                "body": body.decode("utf-8", "replace"),
            }
        )
        self.send_response(200)
        self.send_header("content-length", "2")
        self.end_headers()
        self.wfile.write(b"ok")

    def do_GET(self) -> None:  # noqa: N802
        self._record()

    def do_POST(self) -> None:  # noqa: N802
        self._record()

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return


@pytest.fixture
def short_dir() -> Iterator[Path]:
    # Unix socket paths must stay under ~104 bytes on macOS.
    path = Path(tempfile.mkdtemp(prefix="ccp-", dir="/tmp"))
    yield path
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def upstream(short_dir: Path) -> Iterator[tuple[str, str]]:
    if shutil.which("openssl") is None:
        pytest.skip("openssl is needed to create the test upstream certificate")
    cert, key, ca_pem = _make_upstream_certs(short_dir)
    _Recorder.seen = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Recorder)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert, key)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"127.0.0.1:{server.server_address[1]}", ca_pem
    server.shutdown()
    server.server_close()


def _guest_request(address: str, ca_pem: str, sni: str, raw: bytes) -> bytes:
    """Send one HTTP/1.1 request as the guest would and return the reply."""
    context = ssl.create_default_context(cadata=ca_pem)
    context.set_alpn_protocols(["http/1.1"])
    if address.startswith("unix:"):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(address.removeprefix("unix:"))
    else:
        host, port = address.removeprefix("tcp:").rsplit(":", 1)
        sock = socket.create_connection((host, int(port)))
    sock.settimeout(10)
    with context.wrap_socket(sock, server_hostname=sni) as tls:
        tls.sendall(raw)
        chunks = []
        while chunk := tls.recv(65536):
            chunks.append(chunk)
    return b"".join(chunks)


def _status(reply: bytes) -> int:
    return int(reply.split(b" ", 2)[1])


def _label(text: str) -> str:
    replacements = {
        REAL_OPENAI: "<REAL:OPENAI_API_KEY>",
        REAL_GH: "<REAL:GITHUB_TOKEN>",
        PH_OPENAI: "<PLACEHOLDER:OPENAI_API_KEY>",
        PH_GH: "<PLACEHOLDER:GITHUB_TOKEN>",
    }
    for value, label in replacements.items():
        text = text.replace(value, label)
    if text.startswith("Basic "):
        decoded = base64.b64decode(text.removeprefix("Basic ")).decode()
        text = f"Basic base64({_label(decoded)})"
    return text


def test_proxy_injects_through_python_api_and_writes_artifact(
    short_dir: Path, upstream: tuple[str, str]
) -> None:
    upstream_addr, upstream_ca = upstream
    log_path = short_dir / "credentials.log"
    proxy = credential_proxy.CredentialProxy(
        listen=f"unix:{short_dir / 'proxy.sock'}",
        log_path=str(log_path),
        _upstream_ca_pem=upstream_ca,
        _upstream_hosts=dict.fromkeys(HOSTS, upstream_addr),
    )
    proxy.set_bindings(
        [
            {
                "name": "OPENAI_API_KEY",
                "placeholder": PH_OPENAI,
                "hosts": ("api.openai.test",),
                "headers": ({"header": "authorization", "form": "bearer"},),
                "source": "env:OPENAI_API_KEY",
            },
            {
                "name": "GITHUB_TOKEN",
                "placeholder": PH_GH,
                "hosts": ["github.test"],
                "headers": [
                    {"header": "Authorization", "form": "basic_password"},
                    {"header": "authorization", "form": "bearer"},
                ],
            },
        ]
    )
    proxy.set_local_routes(
        [{"host": "auth.openai.test", "path": "/oauth/token", "handler": "codex-refresh"}]
    )
    resolved: list[str] = []

    def resolver(name: str) -> str | None:
        resolved.append(name)
        return {"OPENAI_API_KEY": REAL_OPENAI, "GITHUB_TOKEN": REAL_GH}.get(name)

    handled: list[tuple[str, str, list[tuple[str, str]], bytes]] = []

    def refresh(
        method: str, path: str, headers: list[tuple[str, str]], body: bytes
    ) -> tuple[int, list[tuple[str, str]], bytes]:
        handled.append((method, path, headers, body))
        return 200, [("content-type", "application/json")], b'{"access_token":"placeholder"}'

    proxy.set_resolver(resolver)
    proxy.set_local_handler("codex-refresh", refresh)
    started = proxy.start()
    try:
        assert started["address"] == f"unix:{short_dir / 'proxy.sock'}"
        assert started["ca_cert_pem"].startswith("-----BEGIN CERTIFICATE-----")
        address, ca = started["address"], started["ca_cert_pem"]

        reply = _guest_request(
            address,
            ca,
            "api.openai.test",
            (
                f"POST /v1/responses?key={PH_OPENAI} HTTP/1.1\r\nHost: api.openai.test\r\n"
                f"Authorization: Bearer {PH_OPENAI}\r\nContent-Length: {len(PH_OPENAI)}\r\n"
                f"Connection: close\r\n\r\n{PH_OPENAI}"
            ).encode(),
        )
        assert _status(reply) == 200
        git = base64.b64encode(f"x-access-token:{PH_GH}".encode()).decode()
        reply = _guest_request(
            address,
            ca,
            "github.test",
            (
                f"GET /o/r.git/info/refs HTTP/1.1\r\nHost: github.test\r\n"
                f"Authorization: Basic {git}\r\nConnection: close\r\n\r\n"
            ).encode(),
        )
        assert _status(reply) == 200
        reply = _guest_request(
            address,
            ca,
            "github.test",
            (
                f"GET /user HTTP/1.1\r\nHost: github.test\r\n"
                f"Authorization: Bearer {PH_OPENAI}\r\nConnection: close\r\n\r\n"
            ).encode(),
        )
        assert _status(reply) == 200
        reply = _guest_request(
            address,
            ca,
            "auth.openai.test",
            (
                b"POST /oauth/token HTTP/1.1\r\nHost: auth.openai.test\r\n"
                b"Content-Length: 24\r\nConnection: close\r\n\r\ngrant_type=refresh_token"
            ),
        )
        assert _status(reply) == 200
        assert reply.endswith(b'{"access_token":"placeholder"}')
        reply = _guest_request(
            address,
            ca,
            "api.openai.test",
            b"GET / HTTP/1.1\r\nHost: github.test\r\nConnection: close\r\n\r\n",
        )
        assert _status(reply) == 421

        stats = proxy.stats()
    finally:
        proxy.stop()

    seen = _Recorder.seen
    assert len(seen) == 3, "local route and Host mismatch never reach upstream"
    openai, git_refs, wrong_host = seen
    openai_headers = dict(openai["headers"])
    assert openai_headers["authorization"] == f"Bearer {REAL_OPENAI}"
    assert openai["path"] == f"/v1/responses?key={PH_OPENAI}"
    assert openai["body"] == PH_OPENAI
    assert dict(git_refs["headers"])["authorization"] == (
        "Basic " + base64.b64encode(f"x-access-token:{REAL_GH}".encode()).decode()
    )
    assert dict(wrong_host["headers"])["authorization"] == f"Bearer {PH_OPENAI}"
    assert sorted(set(resolved)) == ["GITHUB_TOKEN", "OPENAI_API_KEY"]
    assert handled and handled[0][0] == "POST" and handled[0][1] == "/oauth/token"
    assert handled[0][3] == b"grant_type=refresh_token"
    assert stats["connections"] == 5
    assert set(stats["last_used"]) == {"OPENAI_API_KEY", "GITHUB_TOKEN"}

    log_text = log_path.read_text()
    for secret in (REAL_OPENAI, REAL_GH, PH_OPENAI, PH_GH):
        assert secret not in log_text
    events = [json.loads(line) for line in log_text.splitlines()]
    summary = [(e["event"], e["name"], e["host"], e["status"]) for e in events]
    assert ("inject", "OPENAI_API_KEY", "api.openai.test", 200) in summary
    assert ("inject", "GITHUB_TOKEN", "github.test", 200) in summary
    assert ("refuse", "OPENAI_API_KEY", "github.test", 200) in summary
    assert ("local", "codex-refresh", "auth.openai.test", 200) in summary
    assert ("refuse", None, "api.openai.test", 421) in summary

    artifact = {
        "test": "tests/api/test_credential_proxy.py",
        "upstream_requests": [
            {
                "method": r["method"],
                "path": _label(r["path"]),
                "headers": [[k, _label(v)] for k, v in r["headers"]],
                "body": _label(r["body"]),
            }
            for r in seen
        ],
        "log": [{k: v for k, v in e.items() if k != "ts"} for e in events],
    }
    text = json.dumps(artifact, indent=2, sort_keys=True)
    for secret in (REAL_OPENAI, REAL_GH, PH_OPENAI, PH_GH):
        assert secret not in text
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(text + "\n")


def test_proxy_rejects_bad_listen_and_bindings(short_dir: Path) -> None:
    with pytest.raises(ValueError):
        credential_proxy.CredentialProxy(
            listen="unix:relative.sock", log_path=str(short_dir / "x.log")
        )
    proxy = credential_proxy.CredentialProxy(
        listen="tcp:127.0.0.1:0", log_path=str(short_dir / "x.log")
    )
    with pytest.raises(ValueError):
        proxy.set_bindings(
            [{"name": "X", "placeholder": "short", "hosts": ["a.test"], "headers": []}]
        )
    with pytest.raises(ValueError):
        proxy.set_bindings(
            [
                {
                    "name": "X",
                    "placeholder": PH_OPENAI,
                    "hosts": ["a.test"],
                    "headers": [{"header": "authorization", "form": "cookie"}],
                }
            ]
        )
    started = proxy.start()
    assert started["address"].startswith("tcp:127.0.0.1:")
    second = credential_proxy.CredentialProxy(
        listen="tcp:127.0.0.1:0", log_path=str(short_dir / "y.log")
    )
    try:
        assert second.start()["ca_cert_pem"] != started["ca_cert_pem"]
    finally:
        second.stop()
        proxy.stop()
        proxy.stop()

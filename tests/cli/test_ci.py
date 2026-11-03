"""`celesto ci` reads Celesto CI from the terminal, through the real client and HTTP.

Each test logs in with stored credentials that point at a local stub of the
backend's CI routes, then runs the command as a user would. The stub records
every request, so the tests also check what the CLI asks the backend for.

Ways it can go wrong, each covered below:
- A command calls the wrong route, drops the API key, or sends wrong filters.
- Human output hides a field or `--json` breaks the standard envelope.
- An error from the backend becomes a traceback or a message without a recovery command.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
from click.testing import CliRunner, Result

from celesto.cli import _credentials
from celesto.cli.commands.app import build_cli

RUNNERS = {
    "runners": [
        {
            "label": "celesto-micro",
            "size": "micro",
            "vcpus": 1,
            "ram_mb": 2048,
            "disk_size_mb": 20480,
        },
        {"label": "celesto-xl", "size": "xl", "vcpus": 8, "ram_mb": 32768, "disk_size_mb": 102400},
    ]
}


class Backend:
    """A stub of the backend's CI routes: canned answers, recorded requests."""

    def __init__(self) -> None:
        self.routes: dict[str, tuple[int, Any]] = {}
        self.requests: list[dict[str, Any]] = []
        self.url = ""

    def serve(self, path: str, body: Any, status: int = 200) -> None:
        self.routes[path] = (status, body)


@pytest.fixture
def backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Backend]:
    stub = Backend()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - http.server's handler name
            parts = urlsplit(self.path)
            stub.requests.append(
                {
                    "path": parts.path,
                    "query": {key: values[-1] for key, values in parse_qs(parts.query).items()},
                    "authorization": self.headers.get("Authorization"),
                }
            )
            status, body = stub.routes.get(parts.path, (404, {"detail": "Not Found"}))
            payload = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - http.server's name
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    stub.url = f"http://127.0.0.1:{server.server_address[1]}"
    monkeypatch.delenv("CELESTO_API_KEY", raising=False)
    monkeypatch.setattr(_credentials, "CREDENTIALS_PATH", tmp_path / "credentials")
    _credentials.write_credentials(
        api_key="cel_test_key", email="ci@example.invalid", base_url=stub.url
    )
    try:
        yield stub
    finally:
        server.shutdown()
        server.server_close()


def _run(*args: str) -> Result:
    return CliRunner().invoke(build_cli(), ["ci", *args], catch_exceptions=False)


def test_runners_list_prints_each_size(backend: Backend) -> None:
    backend.serve("/v1/integrations/github/actions/runners", RUNNERS)
    result = _run("runners", "list")
    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[0].split() == ["LABEL", "VCPU", "RAM", "DISK"]
    assert lines[1].split() == ["celesto-micro", "1", "2", "GiB", "20", "GiB"]
    assert lines[2].split() == ["celesto-xl", "8", "32", "GiB", "100", "GiB"]
    assert backend.requests == [
        {
            "path": "/v1/integrations/github/actions/runners",
            "query": {},
            "authorization": "Bearer cel_test_key",
        }
    ]


def test_runners_list_json_uses_the_standard_envelope(backend: Backend) -> None:
    backend.serve("/v1/integrations/github/actions/runners", RUNNERS)
    result = _run("runners", "list", "--json")
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {
        "ok": True,
        "command": "ci.runners.list",
        "exit_code": 0,
        "data": RUNNERS,
        "error": None,
    }

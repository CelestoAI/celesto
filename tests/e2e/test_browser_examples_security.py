"""Real Chromium regressions for the runnable browser agent's domain boundary."""

from __future__ import annotations

import gzip
import importlib.util
import json
import os
import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from playwright.sync_api import APIResponse, Route, WebSocketRoute

import pytest

pytestmark = pytest.mark.e2e


def _load_example() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "examples/agent_tools/computer_use_browser.py"
    spec = importlib.util.spec_from_file_location("computer_use_security_example", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "scenario",
    [
        "allowed",
        "allowed-redirect",
        "redirect",
        "redirect-chain",
        "redirect-backslash",
        "popup",
        "popup-redirect",
        "recovery",
        "subresource",
        "iframe",
        "websocket",
        "worker",
        "compressed",
        "oversized",
    ],
)
def test_computer_use_blocks_excluded_destinations_before_requests(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, scenario: str
) -> None:
    playwright = pytest.importorskip("playwright.sync_api")
    module = _load_example()
    requests = []
    host_fetches = []
    host_websockets = []
    original_fetch = playwright.Route.fetch

    def record_host_fetch(route: Route, **kwargs: Any) -> APIResponse:
        host_fetches.append(route.request.url)
        return cast("APIResponse", original_fetch(route, **kwargs))

    monkeypatch.setattr(playwright.Route, "fetch", record_host_fetch)
    original_connect = playwright.WebSocketRoute.connect_to_server

    def record_host_websocket(route: WebSocketRoute) -> WebSocketRoute:
        host_websockets.append(route.url)
        return cast("WebSocketRoute", original_connect(route))

    monkeypatch.setattr(playwright.WebSocketRoute, "connect_to_server", record_host_websocket)

    class Handler(BaseHTTPRequestHandler):
        server: ThreadingHTTPServer

        def do_GET(self) -> None:
            requests.append((self.headers["Host"], self.path))
            if scenario in {"compressed", "oversized"}:
                body = (
                    gzip.compress(
                        b'<a>Open</a><script>document.body.dataset.rendered="yes"</script>'
                    )
                    if scenario == "compressed"
                    else b"x" * (8 * 1024 * 1024 + 1)
                )
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(body)))
                if scenario == "compressed":
                    self.send_header("Content-Encoding", "gzip")
                self.end_headers()
                with suppress(BrokenPipeError, ConnectionResetError):
                    self.wfile.write(body)
                return
            if self.path == "/worker.js":
                self.send_response(302)
                self.send_header("Location", f"http://localhost:{self.server.server_port}/secret")
                self.end_headers()
                return
            if self.path == "/redirect-backslash":
                self.send_response(302)
                self.send_header("Location", f"\\\\localhost:{self.server.server_port}/secret")
                self.end_headers()
                return
            if self.path == "/allowed-redirect":
                self.send_response(302)
                self.send_header("Location", "/landing")
                self.end_headers()
                return
            if self.path == "/redirect-chain":
                self.send_response(302)
                self.send_header("Location", "/redirect")
                self.end_headers()
                return
            if self.path == "/redirect":
                self.send_response(302)
                self.send_header("Location", f"http://localhost:{self.server.server_port}/secret")
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            popup_url = (
                f"http://127.0.0.1:{self.server.server_port}/redirect"
                if scenario == "popup-redirect"
                else f"http://localhost:{self.server.server_port}/secret"
            )
            self.wfile.write(
                f'<a style="display:block;width:500px;height:500px" target="_blank" '
                f'href="{popup_url}">Open</a>'.encode()
            )
            if scenario == "subresource":
                self.wfile.write(b'<img src="/redirect">')
            if scenario == "iframe":
                self.wfile.write(
                    f'<iframe src="http://frame.test:{self.server.server_port}/redirect"></iframe>'.encode()
                )
            if scenario == "websocket":
                self.wfile.write(
                    f'<script>new WebSocket("ws://127.0.0.1:{self.server.server_port}/socket")</script>'.encode()
                )
            if scenario == "worker":
                self.wfile.write(
                    b"<script>let attempts=0; "
                    b'try { attempts++; new Worker("/worker.js"); } catch {} '
                    b"try { attempts++; new Worker(URL.createObjectURL(new Blob(["
                    b'"fetch(location.origin + \'/worker-fetch\')"], {type:"text/javascript"})))'
                    b"; } catch {} try { attempts++; "
                    b"new SharedWorker(URL.createObjectURL(new Blob(["
                    b"\"fetch(location.origin + '/shared-worker-fetch')\"], "
                    b'{type:"text/javascript"})))'
                    b"; } catch {} document.body.dataset.workerAttempts=String(attempts);"
                    b"</script>"
                )

        def log_message(self, *_args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    start = f"http://127.0.0.1:{server.server_port}"
    config = module.ComputerUseConfig(
        task="Test domain policy",
        start_url=start
        + (
            "/redirect-backslash"
            if scenario == "redirect-backslash"
            else "/allowed-redirect"
            if scenario == "allowed-redirect"
            else "/redirect-chain"
            if scenario == "redirect-chain"
            else "/redirect"
            if scenario in {"redirect", "recovery"}
            else "/"
        ),
        allowed_domains=("127.0.0.1", "frame.test"),
        browser_mode="headless",
        viewport_width=800,
        viewport_height=600,
        max_steps=3,
        model="unused",
    )
    try:
        with playwright.sync_playwright() as runtime:
            browser = runtime.chromium.launch(
                executable_path=os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"),
                headless=True,
                args=["--host-resolver-rules=MAP frame.test 127.0.0.1", "--no-proxy-server"],
            )
            try:
                if scenario == "recovery":
                    context = browser.new_context(service_workers="block")
                    # The recovery helper owns installation too: callers must not be
                    # able to reopen an unguarded browser when every page was closed.
                    with suppress(Exception):
                        module._enforce_allowed_pages(context, None, config)
                else:

                    @contextmanager
                    def session(**_kwargs: object) -> Iterator[SimpleNamespace]:
                        yield SimpleNamespace(
                            session_id="browser-test",
                            cdp_url="http://unused",
                            viewer_url=None,
                            display_url=None,
                            artifacts_dir=None,
                            connect_playwright=lambda: browser,
                        )

                    class Responses:
                        count = 0

                        def create(self, **_kwargs: object) -> SimpleNamespace:
                            self.count += 1
                            if scenario in {"popup", "popup-redirect"} and self.count == 1:
                                action = SimpleNamespace(
                                    type="click", x=20, y=20, button="left", keys=[]
                                )
                                call = SimpleNamespace(
                                    type="computer_call", call_id="test", actions=[action]
                                )
                                return SimpleNamespace(output=[call], id="first")
                            return SimpleNamespace(output=[], output_text="Done", id="final")

                    responses = Responses()
                    monkeypatch.setattr(module, "Celesto", SimpleNamespace(browser=session))
                    monkeypatch.setattr(
                        module,
                        "_require_dependency",
                        lambda *_args: lambda: SimpleNamespace(responses=responses),
                    )
                    # Blocking an unauthorized navigation may terminate the run.
                    if scenario in {
                        "allowed",
                        "allowed-redirect",
                        "subresource",
                        "iframe",
                        "websocket",
                        "worker",
                        "compressed",
                    }:
                        result = module._run_task(config)
                        assert result.page_url == start + (
                            "/landing" if scenario == "allowed-redirect" else "/"
                        )
                        browser.contexts[0].pages[0].wait_for_timeout(400)
                        assert "Open" in browser.contexts[0].pages[0].locator("body").inner_text()
                        if scenario == "worker":
                            assert (
                                browser.contexts[0]
                                .pages[0]
                                .locator("body")
                                .get_attribute("data-worker-attempts")
                                == "3"
                            )
                        if scenario == "compressed":
                            assert (
                                browser.contexts[0]
                                .pages[0]
                                .locator("body")
                                .get_attribute("data-rendered")
                                == "yes"
                            )
                    elif scenario == "oversized":
                        with pytest.raises(playwright.Error):
                            module._run_task(config)
                        assert responses.count == 0
                    else:
                        with suppress(Exception):
                            module._run_task(config)
                    if scenario in {"popup", "popup-redirect"}:
                        assert responses.count == 2
                assert not any(path == "/secret" for _host, path in requests), requests
                assert any(host.startswith("127.0.0.1:") for host, _path in requests), requests
                assert not host_fetches, (
                    "Page requests must stay in Chromium, not the host API client"
                )
                assert not host_websockets, "WebSocket connections must not be relayed by the host"
                assert not any(path == "/socket" for _host, path in requests), requests
                assert not any(path == "/worker-fetch" for _host, path in requests), requests
                assert not any(path == "/shared-worker-fetch" for _host, path in requests), requests
                if scenario == "iframe":
                    assert not any(host.startswith("frame.test:") for host, _path in requests), (
                        requests
                    )
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
        (tmp_path / "domain-policy-evidence.json").write_text(
            json.dumps(
                {
                    "requests": requests,
                    "host_fetches": host_fetches,
                    "host_websockets": host_websockets,
                },
                indent=2,
            )
        )

"""Exercise the built dashboard and its capability over real browser transports."""

from __future__ import annotations

import json
import os
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from starlette.routing import Mount

from celesto.types import VMInfo

pytestmark = pytest.mark.e2e


@pytest.mark.parametrize("stream_available", [True, False])
def test_dashboard_login_authenticates_ui_without_cross_port_cookies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stream_available: bool
) -> None:
    playwright = pytest.importorskip("playwright.sync_api")
    uvicorn = pytest.importorskip("uvicorn")
    from celesto.dashboard import server
    from celesto.dashboard.connection_manager import ConnectionManager

    dist = Path(__file__).resolve().parents[2] / "ui/dist"
    if not (dist / "index.html").is_file():
        pytest.skip("Build the dashboard first with npm run build in ui/.")

    class Inventory:
        def list_vms(self, *_args: object) -> list[VMInfo]:
            return []

    monkeypatch.setattr(server.app.state, "auth_token", "browser-owner-token")
    monkeypatch.setattr(server, "_get_state_manager", lambda _app: Inventory())
    monkeypatch.setattr(server, "_get_sdk", lambda _app: object())
    monkeypatch.setattr(server, "_get_conn_manager", lambda _app: ConnectionManager())
    monkeypatch.setattr(server, "_ui_dist", dist)
    for route in server.app.routes:
        if isinstance(route, Mount) and route.name == "ui":
            monkeypatch.setattr(route.app, "directory", dist)
            monkeypatch.setattr(route.app, "all_directories", [dist])

    received = []

    class OtherService(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            received.append(
                {"cookie": self.headers.get("Cookie"), "auth": self.headers.get("Authorization")}
            )
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Other local service")

        def log_message(self, *_args: object) -> None:
            pass

    other = ThreadingHTTPServer(("127.0.0.1", 0), OtherService)
    other_thread = threading.Thread(target=other.serve_forever, daemon=True)
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    origin = f"http://127.0.0.1:{listener.getsockname()[1]}"
    runtime = uvicorn.Server(uvicorn.Config(server.app, lifespan="off", log_level="warning"))
    thread = threading.Thread(target=lambda: runtime.run(sockets=[listener]), daemon=True)
    snapshots = []
    browser_errors = []
    api_responses = []
    try:
        other_thread.start()
        thread.start()
        deadline = time.monotonic() + 10
        while not runtime.started and time.monotonic() < deadline:
            time.sleep(0.02)
        assert runtime.started
        with playwright.sync_playwright() as engine:
            browser = engine.chromium.launch(
                executable_path=os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"), headless=True
            )
            try:
                context = browser.new_context()
                if not stream_available:
                    context.add_init_script(
                        "window.WebSocket = class { constructor() { "
                        "throw new DOMException('Stream unavailable', 'SecurityError'); } };"
                    )
                page = context.new_page()
                page.set_default_timeout(5000)
                page.on("pageerror", lambda error: browser_errors.append(str(error)))
                page.on(
                    "console",
                    lambda message: (
                        browser_errors.append(message.text) if message.type == "error" else None
                    ),
                )
                page.on(
                    "websocket",
                    lambda ws: ws.on("framereceived", lambda frame: snapshots.append(frame)),
                )
                page.on(
                    "response",
                    lambda response: (
                        api_responses.append((response.url, response.status))
                        if "/api/" in response.url
                        else None
                    ),
                )
                page.goto(origin + "/login#token=browser-owner-token")
                page.wait_for_url(origin + "/")
                field = page.get_by_placeholder("type command or search fleet...")
                field.fill("list")
                page.get_by_role("button", name="Run command").click()
                page.wait_for_function(
                    "document.querySelector('[role=status]').textContent || "
                    "document.querySelector('[role=alert]').textContent"
                )
                assert page.get_by_role("alert").inner_text() == ""
                page.get_by_role("status").filter(has_text="Found 0 computers.").wait_for()
                if stream_available:
                    deadline = time.monotonic() + 5
                    while not snapshots and time.monotonic() < deadline:
                        page.wait_for_timeout(50)
                    assert any(
                        json.loads(frame).get("type") == "snapshot" for frame in snapshots
                    ), browser_errors
                assert not browser_errors
                assert all(
                    status == 200 or url.endswith("/api/session") for url, status in api_responses
                )
                assert not context.cookies()
                page.goto(f"http://127.0.0.1:{other.server_port}/")
                assert received and all(not row["cookie"] and not row["auth"] for row in received)
                assert page.evaluate("sessionStorage.getItem('celesto-dashboard-token')") is None
                (tmp_path / "dashboard-browser-evidence.json").write_text(
                    json.dumps(
                        {
                            "api_responses": api_responses,
                            "websocket_snapshots": len(snapshots),
                            "stream_available": stream_available,
                            "other_service": received,
                        },
                        indent=2,
                    )
                )
            finally:
                browser.close()
    finally:
        runtime.should_exit = True
        thread.join(timeout=10)
        listener.close()
        other.shutdown()
        other.server_close()
        other_thread.join(timeout=10)

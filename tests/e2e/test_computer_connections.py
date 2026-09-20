"""Real connections: run with --with playwright --with websockets, no browser download needed."""

import platform
import shutil
import struct
import time
from contextlib import suppress

import pytest
from _util import require_backend_available, selected_backend

from celesto import Computer

pytestmark = pytest.mark.e2e


class RFBClient:
    """Minimal real VNC client that deliberately sends input in both modes."""

    def __init__(self, ws):
        self.ws = ws
        self.buffer = bytearray()
        assert self.read(12).startswith(b"RFB 003.")
        ws.send(b"RFB 003.008\n")
        count = self.read(1)[0]
        assert 1 in self.read(count)  # Gateway/loopback authenticates; RFB auth is None.
        ws.send(b"\x01")
        assert self.read(4) == b"\0\0\0\0"
        ws.send(b"\x01")  # Shared desktop.
        init = self.read(24)
        self.read(struct.unpack(">I", init[20:24])[0])

    def read(self, size):
        while len(self.buffer) < size:
            chunk = self.ws.recv(timeout=10)
            assert isinstance(chunk, bytes)
            self.buffer.extend(chunk)
        result = bytes(self.buffer[:size])
        del self.buffer[:size]
        return result

    def type_a(self):
        self.ws.send(struct.pack(">BBHI", 4, 1, 0, ord("a")))
        self.ws.send(struct.pack(">BBHI", 4, 0, 0, ord("a")))

    def click(self):
        self.ws.send(struct.pack(">BBHH", 5, 1, 100, 150))
        self.ws.send(struct.pack(">BBHH", 5, 0, 100, 150))

    def clipboard(self, text):
        data = text.encode()
        self.ws.send(struct.pack(">B3xI", 6, len(data)) + data)


def exercise_connections(computer):
    playwright = pytest.importorskip("playwright.sync_api")
    websocket = pytest.importorskip("websockets.sync.client")
    browser_info = computer.browser()
    with playwright.sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(browser_info.url)
        try:
            page = browser.contexts[0].new_page()
            page.goto("file:///tmp/connection-test")
            assert "connection-test" in page.locator("body").inner_text()
            html = (
                '<input id="input" autofocus><script>window.clicks=0;'
                'document.addEventListener("mousedown",()=>window.clicks++)</script>'
            )
            page.route(
                "http://localhost/connection-smoke",
                lambda route: route.fulfill(body=html, content_type="text/html"),
            )
            browser.contexts[0].grant_permissions(
                ["clipboard-read", "clipboard-write"], origin="http://localhost"
            )
            page.goto("http://localhost/connection-smoke")
            page.bring_to_front()
            page.locator("input").focus()
            readonly = computer.display()
            writable = computer.display(mode="read_write")
            with (
                websocket.connect(readonly.url, proxy=None) as ro_ws,
                websocket.connect(writable.url, proxy=None) as rw_ws,
            ):
                ro, rw = RFBClient(ro_ws), RFBClient(rw_ws)
                page.evaluate("navigator.clipboard.writeText('baseline')")
                ro.clipboard("forbidden")
                ro.type_a()
                ro.click()
                time.sleep(0.3)
                assert page.locator("input").input_value() == ""
                assert page.evaluate("window.clicks") == 0
                assert page.evaluate("navigator.clipboard.readText()") == "baseline"
                rw.type_a()
                page.wait_for_function("document.querySelector('input').value === 'a'")
                rw.click()
                page.wait_for_function("window.clicks > 0")
                rw.clipboard("accepted")
                page.wait_for_function("navigator.clipboard.readText().then(t => t === 'accepted')")
            # Credential refresh must not restart the browser or lose its page.
            computer.browser()
            assert page.locator("input").input_value() == "a"
            return browser_info
        finally:
            browser.close()


def test_local_computer_connections(request, tmp_path):
    if selected_backend(request.config) not in ("all", "qemu"):
        pytest.skip("This graphical connection smoke uses QEMU.")
    if platform.system() == "Darwin":
        if not shutil.which("qemu-system-aarch64"):
            pytest.skip("Install QEMU to run the graphical connection smoke.")
    else:
        require_backend_available("qemu", request.config, sandbox_name="computer-connections")
    pytest.importorskip("playwright.sync_api")
    pytest.importorskip("websockets.sync.client")
    with Computer(
        local=True, template_id="browser-agent", backend="qemu", data_dir=tmp_path
    ) as computer:
        computer.run("printf connection-test > /tmp/connection-test")
        info = exercise_connections(computer)
        assert info.expires_at is None
        attached = Computer.get(computer.id, local=True, data_dir=tmp_path)
        try:
            assert attached.run("cat /tmp/connection-test").stdout == "connection-test"
            assert attached.browser().url.startswith("ws://127.0.0.1:")
        finally:
            # Releasing test-owned local forwards must not delete the attached VM.
            with suppress(Exception):
                attached._vm._cleanup_local_forwards()
            attached._vm.close()

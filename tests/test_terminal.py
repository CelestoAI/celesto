"""Terminal connection validation and bounded synchronous I/O."""

import io
import json
import logging
import os
import threading
import time
from collections import deque
from urllib.parse import parse_qs, urlsplit

import pytest
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from celesto._terminal import _TERMINAL_WEBSOCKET_LOGGER, cloud_terminal_connection
from celesto.exceptions import CelestoError


class PipeInput:
    def __init__(self, fd: int) -> None:
        self.buffer = self
        self.fd = fd

    def fileno(self) -> int:
        return self.fd


class FakeWebSocket:
    def __init__(self, messages=(), *, abnormal_close=False, normal_close=False) -> None:
        self.messages = deque(messages)
        self.abnormal_close = abnormal_close
        self.normal_close = normal_close
        self.closed = threading.Event()
        self.sent = []
        self.close_calls = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.closed.set()

    def send(self, message):
        self.sent.append(message)

    def recv(self, timeout=None):
        if self.messages:
            return self.messages.popleft()
        if self.abnormal_close:
            raise ConnectionClosedError(None, None)
        if self.normal_close:
            raise ConnectionClosedOK(None, None)
        if self.closed.wait(timeout):
            raise ConnectionClosedOK(None, None)
        raise TimeoutError

    def close(self, code=1000, reason=""):
        self.close_calls.append((code, reason))
        self.closed.set()


def make_connection():
    return cloud_terminal_connection(
        terminal_id="term_test123",
        gateway_url="wss://gateway.example/connect?region=us&token=old",
        token="token with spaces",
        expires_at="2026-09-19T12:00:00Z",
    )


def attach_with_pipe(monkeypatch, websocket, data=b"\x1d", output=None):
    read_fd, write_fd = os.pipe()
    os.write(write_fd, data)
    os.close(write_fd)
    output = io.BytesIO() if output is None else output
    captured = {}

    def connect(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return websocket

    monkeypatch.setattr("websockets.sync.client.connect", connect)
    monkeypatch.setattr("celesto._terminal.sys.stdin", PipeInput(read_fd))
    monkeypatch.setattr("celesto._terminal.sys.stdout", output)
    monkeypatch.setattr("celesto._terminal.os.isatty", lambda _fd: False)
    try:
        make_connection().attach()
    finally:
        os.close(read_fd)
    return captured, output


def test_cloud_terminal_forwards_input_output_and_detaches_without_closing_shell(monkeypatch):
    websocket = FakeWebSocket([b"ready\r\n"])

    captured, output = attach_with_pipe(monkeypatch, websocket, b"echo hello\n\x1dignored")

    query = parse_qs(urlsplit(captured["url"]).query)
    assert query == {"region": ["us"], "token": ["token with spaces"]}
    assert captured["kwargs"] == {
        "open_timeout": 10,
        "close_timeout": 5,
        "compression": None,
        "max_size": 1024 * 1024,
        "max_queue": 16,
        "logger": _TERMINAL_WEBSOCKET_LOGGER,
    }
    assert _TERMINAL_WEBSOCKET_LOGGER.getEffectiveLevel() == logging.WARNING
    assert json.loads(websocket.sent[0]) == {"type": "resize", "cols": 80, "rows": 24}
    assert websocket.sent[1:] == [b"echo hello\n"]
    assert output.getvalue() == b"ready\r\n"
    assert websocket.close_calls == [(1000, "client detached")]
    assert not any(
        '"type": "close"' in message for message in websocket.sent if isinstance(message, str)
    )


def test_cloud_terminal_preserves_json_shaped_shell_output(monkeypatch):
    output_text = json.dumps({"type": "error", "message": "shell output"})
    websocket = FakeWebSocket([output_text], normal_close=True)

    _, output = attach_with_pipe(monkeypatch, websocket)

    assert output.getvalue() == output_text.encode()


def test_cloud_terminal_reports_abnormal_close(monkeypatch):
    websocket = FakeWebSocket(abnormal_close=True)

    with pytest.raises(CelestoError, match="ended unexpectedly"):
        attach_with_pipe(monkeypatch, websocket)


def test_cloud_terminal_accepts_text_output_and_normal_remote_close(monkeypatch):
    websocket = FakeWebSocket(["hello"], normal_close=True)

    _, output = attach_with_pipe(monkeypatch, websocket)

    assert output.getvalue() == b"hello"


def test_cloud_terminal_keeps_receiving_after_stdin_eof(monkeypatch):
    class CommandWebSocket(FakeWebSocket):
        def __init__(self):
            super().__init__()
            self.command_sent = threading.Event()
            self.output_sent = False

        def send(self, message):
            super().send(message)
            if message == b"echo hello\n":
                self.command_sent.set()

        def recv(self, timeout=None):
            if not self.command_sent.wait(timeout):
                raise TimeoutError
            if not self.output_sent:
                self.output_sent = True
                return b"hello\r\n"
            raise ConnectionClosedOK(None, None)

    websocket = CommandWebSocket()

    _, output = attach_with_pipe(monkeypatch, websocket, b"echo hello\n")

    assert output.getvalue() == b"hello\r\n"


def test_cloud_terminal_forwards_resize_and_restores_signal_handler(monkeypatch):
    websocket = FakeWebSocket()
    sizes = iter([(24, 80), (30, 100)])
    handlers = []
    select_calls = 0

    def fake_signal(_signal, handler):
        handlers.append(handler)

    def fake_select(readers, _writers, _errors, _timeout):
        nonlocal select_calls
        select_calls += 1
        if select_calls == 1:
            handlers[-1](0, None)
            return [], [], []
        return readers, [], []

    monkeypatch.setattr("celesto._terminal._terminal_size", lambda _fd: next(sizes))
    monkeypatch.setattr("celesto._terminal.signal.getsignal", lambda _signal: "old-handler")
    monkeypatch.setattr("celesto._terminal.signal.signal", fake_signal)
    monkeypatch.setattr("celesto._terminal.select.select", fake_select)

    attach_with_pipe(monkeypatch, websocket)

    resize_messages = [json.loads(message) for message in websocket.sent]
    assert resize_messages == [
        {"type": "resize", "cols": 80, "rows": 24},
        {"type": "resize", "cols": 100, "rows": 30},
    ]
    assert handlers[-1] == "old-handler"


def test_cloud_terminal_normalizes_handshake_failure(monkeypatch):
    read_fd, write_fd = os.pipe()
    os.close(write_fd)
    monkeypatch.setattr("celesto._terminal.sys.stdin", PipeInput(read_fd))
    monkeypatch.setattr(
        "websockets.sync.client.connect", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError())
    )
    try:
        with pytest.raises(CelestoError, match="request fresh terminal details"):
            make_connection().attach()
    finally:
        os.close(read_fd)


def test_cloud_terminal_requires_input_file_descriptor(monkeypatch):
    monkeypatch.setattr("celesto._terminal.sys.stdin", object())

    with pytest.raises(CelestoError, match="real terminal or pipe"):
        make_connection().attach()


def test_cloud_terminal_normalizes_initial_send_failure(monkeypatch):
    class SendFailureWebSocket(FakeWebSocket):
        def send(self, message):
            raise OSError("wss://gateway.example/connect?token=do-not-print")

    with pytest.raises(CelestoError) as exc:
        attach_with_pipe(monkeypatch, SendFailureWebSocket())

    assert "do-not-print" not in str(exc.value)


def test_cloud_terminal_forwards_non_utf8_input_as_bytes(monkeypatch):
    websocket = FakeWebSocket()

    attach_with_pipe(monkeypatch, websocket, b"\xff\xfe\x1d")

    assert websocket.sent[1:] == [b"\xff\xfe"]


def test_cloud_terminal_rejects_unsafe_urls_without_exposing_token():
    for url in (
        "https://gateway.example/connect",
        "ws://gateway.example/connect",
        "wss://user@gateway.example/connect",
        "wss://gateway.example/connect#token",
        "wss://gateway.example/connect?" + "&".join(f"x{i}=1" for i in range(101)),
    ):
        with pytest.raises(CelestoError) as exc:
            cloud_terminal_connection(
                terminal_id="term_test123",
                gateway_url=url,
                token="do-not-print",
                expires_at="2026-09-19T12:00:00Z",
            )
        assert "do-not-print" not in str(exc.value)


@pytest.mark.parametrize(
    "overrides",
    [
        {"gateway_url": "wss://gateway.example/" + "x" * 4096},
        {"token": "x" * (16 * 1024 + 1)},
        {"expires_at": "2" * 101},
        {"expires_at": object()},
    ],
)
def test_cloud_terminal_rejects_oversized_or_invalid_connection_fields(overrides):
    values = {
        "terminal_id": "term_test123",
        "gateway_url": "wss://gateway.example/connect",
        "token": "token",
        "expires_at": "2026-09-19T12:00:00Z",
    }
    values.update(overrides)

    with pytest.raises(CelestoError, match="invalid terminal connection details"):
        cloud_terminal_connection(**values)


def test_cloud_terminal_normalizes_stdout_write_failure(monkeypatch):
    class BrokenOutput:
        def write(self, _payload):
            raise OSError("do not expose")

        def flush(self):
            raise AssertionError("write should fail first")

    with pytest.raises(CelestoError, match="fix stdout and attach again"):
        attach_with_pipe(monkeypatch, FakeWebSocket([b"output"]), output=BrokenOutput())


def test_cloud_terminal_normalizes_unexpected_receiver_failure(monkeypatch):
    class BrokenWebSocket(FakeWebSocket):
        def recv(self, timeout=None):
            raise RuntimeError("do not expose")

    with pytest.raises(CelestoError, match="connection failed; attach again"):
        attach_with_pipe(monkeypatch, BrokenWebSocket())


def test_cloud_terminal_attach_works_without_signal_handler_in_worker_thread(monkeypatch):
    websocket = FakeWebSocket()
    errors = []

    def worker():
        try:
            attach_with_pipe(monkeypatch, websocket)
        except Exception as exc:  # pragma: no cover - asserted below
            errors.append(exc)

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(timeout=2)

    assert not thread.is_alive()
    assert errors == []


def test_cloud_terminal_waits_for_receiver_cleanup(monkeypatch):
    websocket = FakeWebSocket()

    started = time.monotonic()
    attach_with_pipe(monkeypatch, websocket)

    assert time.monotonic() - started < 1

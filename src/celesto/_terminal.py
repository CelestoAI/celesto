"""Public terminal handle and private local/cloud attachment transports."""

from __future__ import annotations

import json
import os
import re
import select
import signal
import sys
import threading
from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from celesto.exceptions import CelestoError

_TERMINAL_ID_PATTERN = re.compile(r"^term_[A-Za-z0-9_-]+$")
_MAX_TERMINAL_ID_CHARS = 160
_MAX_GATEWAY_URL_CHARS = 4096
_MAX_TOKEN_CHARS = 16 * 1024
_MAX_GATEWAY_MESSAGE_BYTES = 1024 * 1024


class TerminalConnection:
    """An interactive terminal attachment for a local or cloud computer.

    Call :meth:`attach` to connect the process's stdin and stdout. Cloud
    connections expose a durable ``terminal_id`` for later reattachment. Secret
    connection credentials are deliberately absent from the public object.
    """

    __slots__ = ("_attach", "expires_at", "terminal_id")

    def __init__(
        self,
        *,
        terminal_id: str | None,
        expires_at: datetime | None,
        _attach: Callable[[], None],
    ) -> None:
        self.terminal_id = terminal_id
        self.expires_at = expires_at
        self._attach = _attach

    def attach(self) -> None:
        """Attach this process's terminal until the shell exits or the user detaches.

        Press Ctrl+] to detach from a cloud terminal without ending its shell.
        """
        self._attach()

    def __repr__(self) -> str:
        return (
            f"TerminalConnection(terminal_id={self.terminal_id!r}, expires_at={self.expires_at!r})"
        )


def validate_terminal_id(terminal_id: str | None) -> None:
    """Validate a public terminal ID before provisioning or network access."""
    if terminal_id is None:
        return
    if (
        not isinstance(terminal_id, str)
        or len(terminal_id) > _MAX_TERMINAL_ID_CHARS
        or _TERMINAL_ID_PATTERN.fullmatch(terminal_id) is None
    ):
        raise ValueError(
            "terminal_id must start with 'term_' and contain only letters, numbers, '_' or '-'."
        )


def local_terminal_connection(attach: Callable[[], int]) -> TerminalConnection:
    """Wrap the existing local fast-shell attachment in the public type."""

    def attach_without_result() -> None:
        attach()

    return TerminalConnection(terminal_id=None, expires_at=None, _attach=attach_without_result)


def cloud_terminal_connection(
    *,
    terminal_id: object,
    gateway_url: object,
    token: object,
    expires_at: object,
) -> TerminalConnection:
    """Validate cloud connection data and hide its credential in an attach callback."""
    if not isinstance(terminal_id, str):
        raise _invalid_cloud_terminal_response()
    try:
        validate_terminal_id(terminal_id)
    except ValueError:
        raise _invalid_cloud_terminal_response() from None
    if not isinstance(gateway_url, str) or not isinstance(token, str) or not token:
        raise _invalid_cloud_terminal_response()
    if len(token) > _MAX_TOKEN_CHARS:
        raise _invalid_cloud_terminal_response()

    authenticated_url = _authenticated_gateway_url(gateway_url, token)
    expiry = _parse_expiry(expires_at)
    return TerminalConnection(
        terminal_id=terminal_id,
        expires_at=expiry,
        _attach=lambda: _attach_cloud_terminal(authenticated_url),
    )


def _invalid_cloud_terminal_response() -> CelestoError:
    return CelestoError(
        "Cloud returned invalid terminal connection details; attach again to request fresh details."
    )


def _parse_expiry(value: object) -> datetime:
    if not isinstance(value, str) or len(value) > 100:
        raise _invalid_cloud_terminal_response()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise _invalid_cloud_terminal_response() from None
    if parsed.tzinfo is None:
        raise _invalid_cloud_terminal_response()
    return parsed.astimezone(UTC)


def _authenticated_gateway_url(gateway_url: str, token: str) -> str:
    if len(gateway_url) > _MAX_GATEWAY_URL_CHARS:
        raise _invalid_cloud_terminal_response()
    try:
        parts = urlsplit(gateway_url)
        local_ws = parts.scheme == "ws" and parts.hostname in {"localhost", "127.0.0.1", "::1"}
        if (
            not parts.hostname
            or (parts.scheme != "wss" and not local_ws)
            or parts.username
            or parts.password
            or parts.fragment
        ):
            raise ValueError
        query = [
            (key, value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True, max_num_fields=100)
            if key != "token"
        ]
    except ValueError:
        raise _invalid_cloud_terminal_response() from None
    query.append(("token", token))
    return urlunsplit(parts._replace(query=urlencode(query)))


def _terminal_size(fd: int) -> tuple[int, int]:
    try:
        size = os.get_terminal_size(fd)
    except OSError:
        return 24, 80
    return max(1, size.lines), max(1, size.columns)


def _write_terminal_output(stdout: Any, payload: bytes) -> None:
    try:
        stdout.write(payload)
    except TypeError:
        stdout.write(payload.decode("utf-8", errors="replace"))
    stdout.flush()


def _attach_cloud_terminal(url: str) -> None:
    try:
        from websockets.exceptions import ConnectionClosed, ConnectionClosedError
        from websockets.sync.client import connect
    except ImportError as exc:  # pragma: no cover - packaging regression guard
        raise CelestoError("Install Celesto again to enable cloud terminal connections.") from exc

    stdin = getattr(sys.stdin, "buffer", sys.stdin)
    stdout = getattr(sys.stdout, "buffer", sys.stdout)
    try:
        stdin_fd = stdin.fileno()
    except (AttributeError, OSError) as exc:
        raise CelestoError("Terminal attachment needs a real terminal or pipe for input.") from exc

    old_attrs: Any = None
    old_winch: Any = None
    resize_pending = False
    stdin_open = True
    done = threading.Event()
    failures: list[CelestoError] = []
    receiver: threading.Thread | None = None

    def mark_resize(_signum: int, _frame: object) -> None:
        nonlocal resize_pending
        resize_pending = True

    try:
        try:
            websocket = connect(
                url,
                open_timeout=10,
                close_timeout=5,
                compression=None,
                max_size=_MAX_GATEWAY_MESSAGE_BYTES,
                max_queue=16,
            )
        except Exception:
            raise CelestoError(
                "Could not attach to the cloud terminal; request fresh terminal "
                "details and try again."
            ) from None

        with websocket:
            rows, cols = _terminal_size(stdin_fd)
            websocket.send(json.dumps({"type": "resize", "cols": cols, "rows": rows}))

            if os.isatty(stdin_fd):
                import termios
                import tty

                old_attrs = termios.tcgetattr(stdin_fd)
                tty.setraw(stdin_fd)
            if hasattr(signal, "SIGWINCH"):
                try:
                    old_winch = signal.getsignal(signal.SIGWINCH)
                    signal.signal(signal.SIGWINCH, mark_resize)
                except ValueError:
                    old_winch = None

            def receive() -> None:
                try:
                    while not done.is_set():
                        try:
                            message = websocket.recv(timeout=0.25)
                        except TimeoutError:
                            continue
                        if isinstance(message, str):
                            payload = message.encode("utf-8")
                        else:
                            payload = bytes(message)
                        _write_terminal_output(stdout, payload)
                except ConnectionClosedError:
                    failures.append(
                        CelestoError(
                            "Cloud terminal connection ended unexpectedly; "
                            "attach again to reconnect."
                        )
                    )
                except ConnectionClosed:
                    pass
                except OSError:
                    failures.append(
                        CelestoError(
                            "Could not write cloud terminal output; fix stdout and attach again."
                        )
                    )
                except Exception:
                    failures.append(
                        CelestoError("Cloud terminal connection failed; attach again to reconnect.")
                    )
                finally:
                    done.set()

            receiver = threading.Thread(target=receive, name="celesto-terminal-output", daemon=True)
            receiver.start()

            try:
                while not done.is_set():
                    if resize_pending:
                        resize_pending = False
                        rows, cols = _terminal_size(stdin_fd)
                        websocket.send(json.dumps({"type": "resize", "cols": cols, "rows": rows}))
                    if not stdin_open:
                        done.wait(0.1)
                        continue
                    readable, _, _ = select.select([stdin_fd], [], [], 0.1)
                    if not readable:
                        continue
                    data = os.read(stdin_fd, 65536)
                    if not data:
                        stdin_open = False
                        continue
                    detach_at = data.find(b"\x1d")
                    if detach_at >= 0:
                        data = data[:detach_at]
                    if data:
                        websocket.send(data)
                    if detach_at >= 0:
                        break
            except ConnectionClosed:
                pass
            except KeyboardInterrupt:
                pass
            finally:
                done.set()
                with suppress(Exception):
                    websocket.close(1000, "client detached")
                if receiver is not None:
                    receiver.join(timeout=2)
                    if receiver.is_alive():
                        failures.append(
                            CelestoError(
                                "Cloud terminal did not disconnect cleanly; "
                                "attach again to reconnect."
                            )
                        )
    except CelestoError:
        raise
    except Exception:
        raise CelestoError("Cloud terminal connection failed; attach again to reconnect.") from None
    finally:
        if old_attrs is not None:
            with suppress(Exception):
                import termios

                termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_attrs)
        if old_winch is not None:
            with suppress(Exception):
                signal.signal(signal.SIGWINCH, old_winch)

    if failures:
        raise failures[0]

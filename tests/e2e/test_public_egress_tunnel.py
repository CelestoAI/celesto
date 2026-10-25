"""Real relay/proxy streams must survive a quiet browser session."""

from __future__ import annotations

import json
import select
import socket
import subprocess
import sys
from contextlib import ExitStack
from pathlib import Path

import pytest

from celesto.host import _public_egress_relay
from celesto.host._public_egress_proxy import PublicEgressProxy
from tests.host.test_public_egress_proxy import (
    SocketPairConnector,
    StaticResolver,
    _recv_until,
)

pytestmark = pytest.mark.e2e


def test_quiet_connect_and_websocket_survive_relay_and_proxy(tmp_path: Path) -> None:
    """Value: an established browser stream survives more than 30 seconds idle.

    Either old 30s timeout closes the real subprocess/proxy path. Existing proxy
    tests exchange data immediately and never launch the standalone QEMU relay.
    Uses actual sockets and time; DNS and remote servers use existing fixtures.
    """
    evidence: dict[str, dict[str, object]] = {}
    streams: list[tuple[str, socket.socket, subprocess.Popen[bytes], SocketPairConnector]] = []
    with ExitStack() as stack:
        try:
            for kind in ("connect", "websocket"):
                record: dict[str, object] = {}
                evidence[kind] = record

                def upstream(
                    sock: socket.socket, kind: str = kind, record: dict[str, object] = record
                ) -> None:
                    sock.settimeout(45)
                    if kind == "websocket":
                        record["upgrade"] = _recv_until(sock, b"\r\n\r\n").decode()
                        sock.sendall(
                            b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\n\r\n"
                        )
                    record["before"] = _recv_until(sock, b"\n").decode()
                    sock.sendall(b"ready\n")
                    after = _recv_until(sock, b"\n")
                    record["after"] = after.decode()
                    if after:
                        sock.sendall(b"ack:" + after)

                connector = SocketPairConnector(upstream)
                proxy = stack.enter_context(
                    PublicEgressProxy(
                        f"quiet-{kind}", resolver=StaticResolver(["1.1.1.1"]), connector=connector
                    )
                )
                guest, relay_io = socket.socketpair()
                stack.enter_context(guest)
                guest.settimeout(10)
                with relay_io:
                    process = subprocess.Popen(
                        [
                            sys.executable,
                            "-I",
                            _public_egress_relay.__file__,
                            str(proxy.endpoint.port),
                        ],
                        stdin=relay_io.fileno(),
                        stdout=relay_io.fileno(),
                        stderr=subprocess.PIPE,
                    )

                def stop_relay(process: subprocess.Popen[bytes] = process) -> None:
                    if process.poll() is None:
                        process.terminate()
                    process.wait(timeout=5)
                    assert process.stderr is not None
                    process.stderr.close()

                stack.callback(stop_relay)
                streams.append((kind, guest, process, connector))
                request = (
                    b"CONNECT public.test:443 HTTP/1.1\r\nHost: public.test:443\r\n\r\n"
                    if kind == "connect"
                    else b"GET http://public.test/socket HTTP/1.1\r\nHost: public.test\r\n"
                    b"Connection: Upgrade\r\nUpgrade: websocket\r\n\r\n"
                )
                guest.sendall(request)
                handshake = _recv_until(guest, b"\r\n\r\n")
                assert handshake.startswith(
                    b"HTTP/1.1 200" if kind == "connect" else b"HTTP/1.1 101"
                )
                guest.sendall(b"before-idle\n")
                assert _recv_until(guest, b"\n") == b"ready\n"

            # This wall-clock quiet period is the product contract under test:
            # both legacy stream timeouts expire at 30s, with no heartbeats.
            readable, _, _ = select.select([stream[1] for stream in streams], (), (), 32)
            assert not readable, "An idle relay/proxy stream closed before browsing resumed"
            for kind, guest, process, connector in streams:
                guest.sendall(b"after-idle\n")
                reply = _recv_until(guest, b"\n")
                assert reply == b"ack:after-idle\n"
                assert guest.recv(1) == b""
                assert process.wait(timeout=5) == 0
                assert process.stderr is not None and process.stderr.read() == b""
                connector.join()
                evidence[kind]["reply"] = reply.decode()
                evidence[kind]["relay_exit"] = process.returncode
                assert evidence[kind]["before"] == "before-idle\n"
                assert evidence[kind]["after"] == "after-idle\n"
        finally:
            (tmp_path / "quiet-egress-streams.json").write_text(json.dumps(evidence, indent=2))

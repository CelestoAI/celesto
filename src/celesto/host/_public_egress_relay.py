"""Bridge one QEMU guestfwd connection to its already-owned loopback proxy.

QEMU starts this standalone stdlib-only program for each TCP connection. A
shared chardev would mix concurrent streams and cannot reconnect after EOF.
The command contains only the installed script path and the assigned port;
guest bytes are never interpreted as arguments or shell input.
"""

from __future__ import annotations

import os
import select
import socket
import sys

_BUFFER_LIMIT = 64 * 1024


def relay(port: int) -> None:
    with socket.create_connection(("127.0.0.1", port), timeout=10) as upstream:
        upstream.setblocking(False)
        os.set_blocking(0, False)
        os.set_blocking(1, False)
        to_proxy = bytearray()
        to_guest = bytearray()
        input_open = True
        upstream_open = True
        write_open = True
        while upstream_open or to_guest:
            readers: list[int | socket.socket] = []
            writers: list[int | socket.socket] = []
            if input_open and len(to_proxy) < _BUFFER_LIMIT:
                readers.append(0)
            if upstream_open and len(to_guest) < _BUFFER_LIMIT:
                readers.append(upstream)
            if to_proxy:
                writers.append(upstream)
            if to_guest:
                writers.append(1)
            readable, writable, _ = select.select(readers, writers, [], 30)
            if not readable and not writable:
                return
            if 0 in readable:
                chunk = os.read(0, _BUFFER_LIMIT - len(to_proxy))
                input_open = bool(chunk)
                to_proxy.extend(chunk)
            if upstream in readable:
                chunk = upstream.recv(_BUFFER_LIMIT - len(to_guest))
                upstream_open = bool(chunk)
                to_guest.extend(chunk)
            if upstream in writable:
                del to_proxy[: upstream.send(to_proxy)]
            if 1 in writable:
                del to_guest[: os.write(1, to_guest)]
            if not input_open and not to_proxy and write_open:
                upstream.shutdown(socket.SHUT_WR)
                write_open = False


if __name__ == "__main__":
    port = int(sys.argv[1])
    if not 1 <= port <= 65535:
        raise SystemExit(1)
    try:
        relay(port)
    except OSError:
        # Guest EOF, a stopped proxy, or an idle upstream closes this stream.
        # Never log request data from this private transport.
        raise SystemExit(1) from None

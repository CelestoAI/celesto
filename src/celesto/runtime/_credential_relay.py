# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""Relay one guest connection to this sandbox's credential proxy socket.

QEMU's slirp ``guestfwd=...-cmd:`` starts this once per guest connection to
the proxy address, with the guest connection on stdin/stdout (and stderr).
It copies bytes both ways to the proxy's Unix socket and exits.

Standard library only; QEMU runs it as ``python -I -S <this file> <socket>``.
Nothing is written to stderr, because stderr is the guest connection too.
If the proxy is not running, the guest connection is simply closed.
"""

from __future__ import annotations

import os
import select
import socket
import sys

_CHUNK = 65536


def _relay(guest_in: int, guest_out: int, upstream: socket.socket) -> None:
    upstream_fd = upstream.fileno()
    open_fds = {guest_in, upstream_fd}
    while open_fds:
        readable, _, _ = select.select(list(open_fds), [], [])
        for fd in readable:
            if fd == guest_in:
                data = os.read(guest_in, _CHUNK)
                if not data:
                    open_fds.discard(guest_in)
                    try:
                        upstream.shutdown(socket.SHUT_WR)
                    except OSError:
                        return
                    continue
                upstream.sendall(data)
            else:
                data = upstream.recv(_CHUNK)
                if not data:
                    return
                view = memoryview(data)
                while view:
                    written = os.write(guest_out, view)
                    view = view[written:]


def main(argv: list[str]) -> int:
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 2)
    if len(argv) != 2:
        return 2
    upstream = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        upstream.connect(argv[1])
    except OSError:
        return 1
    try:
        _relay(0, 1, upstream)
    except OSError:
        return 1
    finally:
        upstream.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

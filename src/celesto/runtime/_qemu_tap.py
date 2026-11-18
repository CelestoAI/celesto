"""Open an existing TAP before entering the per-VM QEMU role."""

from __future__ import annotations

import os
import re
import socket
import struct

from celesto.exceptions import CelestoError


def open_qemu_tap(name: str) -> int:
    """Attach the trusted launcher's handle to its existing Linux TAP.

    Opening by name remains outside the confined QEMU process. The pool creates
    the interface under its existing network ownership contract first; this
    function does not configure addresses, routes, persistence or ownership.
    """
    import fcntl

    if not re.fullmatch(r"[A-Za-z0-9_-]{1,15}", name):
        raise CelestoError("Invalid QEMU network interface identity.")
    original_index = socket.if_nametoindex(name)
    fd = os.open("/dev/net/tun", os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        # Linux TUNSETIFF, IFF_TAP | IFF_NO_PI. A nonprivileged pool user can
        # attach only to a persistent TAP whose existing owner permits it.
        request = struct.pack("16sH22x", name.encode("ascii"), 0x0002 | 0x1000)
        result = fcntl.ioctl(fd, 0x400454CA, request)
        actual_name = result[:16].split(b"\0", 1)[0].decode("ascii")
        if actual_name != name or socket.if_nametoindex(name) != original_index:
            raise CelestoError("QEMU network interface changed during launch.")
        return fd
    except BaseException:
        os.close(fd)
        raise

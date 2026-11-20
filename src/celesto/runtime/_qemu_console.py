"""Retain the boot identity window and bounded recent QEMU console bytes.

The first 4 MiB stay at their original offsets; only later bytes rotate.
The minimum cap is 8 MiB, and the configured cap is never increased.

The pool launches this stdlib-only relay with an already validated private log
descriptor and a clean environment. It survives agent restart and exits on EOF;
it never opens paths or interprets customer log content. On isolated pool VMs,
the launch shim joins the same VM cgroup before this code executes, so relay
CPU, memory, tasks and log I/O share the existing per-VM resource ceilings.
"""

from __future__ import annotations

import os
import stat
import sys

# Keep exactly the byte window consumed by ssh_trust, including malformed or
# incomplete first markers. Moving later guest bytes into it could change trust.
BOOT_IDENTITY_WINDOW_BYTES = 4 * 1024**2
MIN_CONSOLE_LIMIT_BYTES = 2 * BOOT_IDENTITY_WINDOW_BYTES
_MARKER = b"\n[Celesto: older console output truncated]\n"


def _write(fd: int, data: bytes, offset: int) -> int:
    while data:
        count = os.pwrite(fd, data, offset)
        if count <= 0:
            raise OSError("Console write made no progress")
        offset += count
        data = data[count:]
    return offset


def main() -> None:
    fd, limit, ready = (int(value) for value in sys.argv[1:])
    info = os.fstat(fd)
    if limit < MIN_CONSOLE_LIMIT_BYTES or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ValueError("Invalid bounded console descriptor or limit")
    position = info.st_size
    if position > limit:
        retained = min(
            1024 * 1024,
            position - BOOT_IDENTITY_WINDOW_BYTES,
            limit - BOOT_IDENTITY_WINDOW_BYTES - len(_MARKER),
        )
        tail = os.pread(fd, retained, position - retained)
        position = _write(fd, _MARKER + tail, BOOT_IDENTITY_WINDOW_BYTES)
        os.ftruncate(fd, position)
    os.write(ready, b"1")
    os.close(ready)
    while chunk := os.read(0, min(64 * 1024, limit // 2)):
        if position + len(chunk) > limit:
            retained = min(
                1024 * 1024,
                position - BOOT_IDENTITY_WINDOW_BYTES,
                limit - BOOT_IDENTITY_WINDOW_BYTES - len(_MARKER) - len(chunk),
            )
            tail = os.pread(fd, retained, position - retained)
            position = _write(fd, _MARKER + tail, BOOT_IDENTITY_WINDOW_BYTES)
            os.ftruncate(fd, position)
        position = _write(fd, chunk, position)
    os.close(fd)


if __name__ == "__main__":
    main()

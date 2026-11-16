"""Retain bounded recent console bytes while the owning QEMU pipe is open.

The pool launches this stdlib-only relay with an already validated private log
descriptor and a clean environment. It survives agent restart and exits on EOF;
it never opens paths or interprets customer log content. Its bounded memory and
CPU run against the separate host control reserve, outside the QEMU cgroup.
"""

from __future__ import annotations

import os
import stat
import sys

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
    if limit < 1024 or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ValueError("Invalid bounded console descriptor or limit")
    position = info.st_size
    if position > limit:
        tail = os.pread(fd, limit - len(_MARKER), position - (limit - len(_MARKER)))
        position = _write(fd, _MARKER + tail, 0)
        os.ftruncate(fd, position)
    os.write(ready, b"1")
    os.close(ready)
    while chunk := os.read(0, min(64 * 1024, limit // 2)):
        if position + len(chunk) > limit:
            retained = min(1024 * 1024, position, limit - len(_MARKER) - len(chunk))
            tail = os.pread(fd, retained, position - retained)
            position = _write(fd, _MARKER + tail, 0)
            os.ftruncate(fd, position)
        position = _write(fd, chunk, position)
    os.close(fd)


if __name__ == "__main__":
    main()

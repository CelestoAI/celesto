"""Exercise terminal paste through the real CLI and OpenSSH, retaining a transcript."""

import os
import platform
import pty
import select
import signal
import sys
import time
from collections.abc import Iterator
from contextlib import suppress
from pathlib import Path
from typing import Literal

import pytest
from _util import BOOT_TIMEOUT, require_backend_available, selected_backend

from celesto import Celesto

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def paste_sandbox(request: pytest.FixtureRequest) -> Iterator[str]:
    # An explicit existing sandbox supports reproducing terminal bugs on macOS.
    existing = os.environ.get("CELESTO_TEST_SSH_SANDBOX")
    if existing:
        yield existing
        return
    selected = selected_backend(request.config)
    backend: Literal["qemu", "firecracker"] = "firecracker" if selected == "firecracker" else "qemu"
    if platform.system() != "Darwin":
        require_backend_available(backend, request.config, sandbox_name="ssh-paste")
    sandbox = Celesto(os="ubuntu", backend=backend, comm_channel="ssh")
    try:
        sandbox.start(boot_timeout=BOOT_TIMEOUT)
        yield sandbox.vm_id
    finally:
        sandbox.delete()


@pytest.mark.parametrize("term", ["xterm-ghostty", "xterm-kitty", "xterm-256color"])
def test_ssh_multiline_paste(paste_sandbox: str, term: str, tmp_path: Path) -> None:
    pid, fd = pty.fork()
    if pid == 0:
        os.environ["TERM"] = term
        os.execv(
            sys.executable,
            [
                sys.executable,
                "-c",
                "from celesto.cli.main import main; main()",
                "sandbox",
                "ssh",
                paste_sandbox,
            ],
        )
    transcript = bytearray()

    def read_until(expected: bytes, timeout: float = 60) -> None:
        start = len(transcript)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if select.select([fd], [], [], 0.1)[0]:
                transcript.extend(os.read(fd, 65536))
                if expected in transcript[start:]:
                    return
        pytest.fail(f"Missing {expected!r}; see {tmp_path / 'ssh-paste.log'}")

    try:
        read_until(b"\x1b[?2004h")
        # The terminal sends these delimiters only after Bash requests paste mode.
        block = b"sleep 0.2\ncat <<EOF\npaste-$(printf '%s' completed)\nEOF\n"
        os.write(fd, b"\x1b[200~" + block + b"\x1b[201~")
        deadline = time.monotonic() + 0.5
        while time.monotonic() < deadline:
            if select.select([fd], [], [], 0.05)[0]:
                transcript.extend(os.read(fd, 65536))
        assert b"paste-completed\r\n" not in transcript
        os.write(fd, b"\r")
        read_until(b"paste-completed\r\n", timeout=10)
        os.write(fd, b"exit\r")
    finally:
        (tmp_path / "ssh-paste.log").write_bytes(transcript)
        os.close(fd)
        with suppress(ProcessLookupError):
            os.kill(pid, signal.SIGTERM)
        os.waitpid(pid, 0)

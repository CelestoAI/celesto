"""Actual process/pipe contracts for the Android console retention ceiling.

Failure cases designed before implementation: unbounded console growth, losing
recent diagnostics on rollover, inheriting an agent credential, stopping when
the pool agent exits, and retaining a writer after QEMU EOF. These fixtures use
small byte limits; they do not qualify hostile-load control-plane headroom.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

RELAY = Path(__file__).resolve().parents[2] / "src/celesto/runtime/_qemu_console.py"


@pytest.mark.skipif(sys.platform != "linux", reason="Android host launcher is Linux-only")
def test_console_is_bounded_retains_recent_output_and_survives_agent_exit(tmp_path: Path) -> None:
    log = tmp_path / "console.log"
    limit = 4096
    fd = os.open(log, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
    read_fd, write_fd = os.pipe()
    parent = r"""
import os, subprocess, sys
ready_read, ready_write = os.pipe()
p = subprocess.Popen(
    [sys.executable, '-I', sys.argv[1], sys.argv[2], sys.argv[4], str(ready_write)],
    stdin=int(sys.argv[3]), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    close_fds=True, pass_fds=(int(sys.argv[2]), ready_write), start_new_session=True,
    env={'PATH': os.defpath, 'LANG': 'C.UTF-8'},
)
os.close(ready_write)
assert os.read(ready_read, 1) == b'1'
os.close(ready_read)
print(p.pid, flush=True)
"""
    try:
        agent = subprocess.run(
            [sys.executable, "-I", "-c", parent, str(RELAY), str(fd), str(read_fd), str(limit)],
            pass_fds=(fd, read_fd),
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert agent.returncode == 0, agent.stderr
        relay_pid = int(agent.stdout.strip())
        os.close(read_fd)
        read_fd = -1
        # The parent has exited before any console bytes arrive.
        os.kill(relay_pid, 0)
        for index in range(32):
            os.write(write_fd, bytes([65 + index % 26]) * 2048)
            assert log.stat().st_size <= limit
        sentinel = b"\nlatest diagnostic after parent exit\n"
        os.write(write_fd, sentinel)
        os.close(write_fd)
        write_fd = -1
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            data = log.read_bytes()
            if data.endswith(sentinel):
                break
            time.sleep(0.01)
        assert data.endswith(sentinel)
        assert b"older console output truncated" in data
        assert len(data) <= limit
        receipt = tmp_path / "receipt.txt"
        receipt.write_text(
            f"parent-exited=true\nrelay-pid={relay_pid}\nretained={len(data)}\nlimit={limit}\n"
        )
    finally:
        os.close(fd)
        if read_fd >= 0:
            os.close(read_fd)
        if write_fd >= 0:
            os.close(write_fd)

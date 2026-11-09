"""A VM process killed by one manager must be reaped even if another manager started it.

The Celesto Cloud pool agent builds one CelestoManager per command. Manager A
starts QEMU and keeps the Popen handle; manager B later stops the VM. Before
this fix B only saw the zombie through ps, called the VM stopped, and nothing
reaped it: the zombie stayed for hours and made a host release roll back.

Failure modes covered:
- a zombie child held by another manager's handle stays unreaped after kill
  and wait (QEMU stop path);
- it stays unreaped after kill alone (Firecracker stop path calls only
  kill_process);
- the child exits between the first reap attempt and the ps zombie check;
- a still-live child is reported dead;
- the starting manager's handle raises after another manager reaps the child.

Each test checks waitpid before any other _is_process_running call, because
that call could reap the leftover itself and hide a failure.
"""

import os
import signal
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import suppress
from pathlib import Path
from unittest.mock import patch

import pytest

from celesto.vm import CelestoManager


def _manager(root: Path) -> CelestoManager:
    return CelestoManager(data_dir=root / "data", socket_dir=root / "sock", backend="firecracker")


def _assert_reaped(pid: int) -> None:
    """The kernel no longer holds an exit status for *pid* (it was reaped)."""
    with pytest.raises(ChildProcessError):
        os.waitpid(pid, os.WNOHANG)


@pytest.fixture
def started_elsewhere(tmp_path: Path) -> Iterator[tuple[CelestoManager, subprocess.Popen[bytes]]]:
    """A live child whose Popen handle belongs to a different manager."""
    starter = _manager(tmp_path / "starter")
    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    starter._process_handles[process.pid] = process
    try:
        yield starter, process
    finally:
        if process.poll() is None:
            process.kill()
        with suppress(subprocess.TimeoutExpired):
            process.wait(timeout=2.0)


def test_kill_and_wait_by_another_manager_reaps_the_child(
    tmp_path: Path, started_elsewhere: tuple[CelestoManager, subprocess.Popen[bytes]]
) -> None:
    starter, process = started_elsewhere
    stopper = _manager(tmp_path / "stopper")
    # A live child without a handle here is still reported running.
    assert stopper._is_process_running(process.pid) is True

    stopper._kill_process(process.pid)
    stopper._wait_for_process(process.pid, timeout=5.0)

    _assert_reaped(process.pid)
    assert stopper._is_process_running(process.pid) is False
    # The starter's handle copes with a child someone else reaped.
    assert starter._is_process_running(process.pid) is False


def test_kill_alone_by_another_manager_reaps_the_child(
    tmp_path: Path, started_elsewhere: tuple[CelestoManager, subprocess.Popen[bytes]]
) -> None:
    """The Firecracker stop path calls only kill_process after its liveness check."""
    _starter, process = started_elsewhere
    stopper = _manager(tmp_path / "stopper")

    stopper._kill_process(process.pid)

    _assert_reaped(process.pid)


def test_child_exiting_during_the_check_is_reaped(
    tmp_path: Path, started_elsewhere: tuple[CelestoManager, subprocess.Popen[bytes]]
) -> None:
    """The child is alive at the first reap attempt and a zombie at the ps check."""
    _starter, process = started_elsewhere
    stopper = _manager(tmp_path / "stopper")
    real_kill = os.kill

    def kill_then_probe(pid: int, sig: int) -> None:
        # Make the child exit right after the first waitpid saw it alive.
        if sig == 0 and pid == process.pid:
            real_kill(pid, signal.SIGKILL)
            deadline = time.monotonic() + 5.0
            while time.monotonic() < deadline and not stopper._is_zombie_process(pid):
                time.sleep(0.01)
        real_kill(pid, sig)

    with patch("celesto.vm.os.kill", side_effect=kill_then_probe):
        assert stopper._is_process_running(process.pid) is False

    _assert_reaped(process.pid)

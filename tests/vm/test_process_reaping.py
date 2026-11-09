"""A VM process killed by one manager must be reaped even if another manager started it.

The Celesto Cloud pool agent builds one CelestoManager per command. Manager A
starts QEMU and keeps the Popen handle; manager B later stops the VM. Before
this fix B only saw the zombie through ps, called the VM stopped, and nothing
reaped it: the zombie stayed for hours and made a host release roll back.

Failure modes covered:
- a zombie child held by another manager's handle stays unreaped;
- a still-live child is reported dead;
- the starting manager's handle raises after another manager reaps the child.
"""

import os
import subprocess
import sys
from contextlib import suppress
from pathlib import Path

import pytest

from celesto.vm import CelestoManager


def _manager(root: Path) -> CelestoManager:
    return CelestoManager(data_dir=root / "data", socket_dir=root / "sock", backend="firecracker")


def test_kill_by_another_manager_reaps_the_child(tmp_path: Path) -> None:
    starter = _manager(tmp_path / "starter")
    stopper = _manager(tmp_path / "stopper")
    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    starter._process_handles[process.pid] = process
    try:
        # A live child without a handle here is still reported running.
        assert stopper._is_process_running(process.pid) is True

        stopper._kill_process(process.pid)
        stopper._wait_for_process(process.pid, timeout=5.0)

        assert stopper._is_process_running(process.pid) is False
        # Reaped: the kernel no longer holds an exit status for this pid.
        with pytest.raises(ChildProcessError):
            os.waitpid(process.pid, os.WNOHANG)
        # The starter's handle copes with a child someone else reaped.
        assert starter._is_process_running(process.pid) is False
    finally:
        if process.poll() is None:
            process.kill()
        with suppress(subprocess.TimeoutExpired):
            process.wait(timeout=2.0)

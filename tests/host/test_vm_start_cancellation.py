"""Cancelled startup retains ownership of a non-public QEMU process."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

import pytest

from celesto.exceptions import CelestoError
from celesto.runtime.qemu import QemuRuntimeAdapter
from celesto.types import NetworkConfig, VMConfig, VMState
from celesto.vm import CelestoManager


@pytest.mark.asyncio
@pytest.mark.parametrize("cancel_count", [1, 2])
@pytest.mark.parametrize("fail_stop", [False, True])
@pytest.mark.parametrize("cancel_during_stop", [False, True])
async def test_cancelled_non_public_start_retains_process_until_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cancel_count: int,
    fail_stop: bool,
    cancel_during_stop: bool,
) -> None:
    """Hold readiness after a real child starts, then interrupt its caller.

    Public-egress cancellation tests miss the direct-await branch. Assert that
    cancellation cannot release the operation claim or lose the PID, including
    repeated cancellation during launch/stop and a failed stop that remains retryable.
    """
    kernel, disk = tmp_path / "kernel", tmp_path / "disk"
    kernel.touch()
    disk.touch()
    manager = CelestoManager(data_dir=tmp_path / "state", backend="qemu")
    config = VMConfig(
        vm_id="cancel-private",
        backend="qemu",
        kernel_path=kernel,
        rootfs_path=disk,
    )
    manager.state.create_vm(config)
    manager.state.update_vm(
        config.vm_id,
        network=NetworkConfig(
            guest_ip="10.0.2.15",
            gateway_ip="10.0.2.2",
            tap_device="usernet",
            guest_mac="52:54:00:12:34:56",
        ),
    )
    children: list[subprocess.Popen[bytes]] = []
    starting, finish = threading.Event(), threading.Event()
    stopping, finish_stop = threading.Event(), threading.Event()
    if not cancel_during_stop:
        finish_stop.set()
    real_popen = subprocess.Popen
    real_stop = QemuRuntimeAdapter.stop
    termination_denied = fail_stop

    def launch(command: list[str], **kwargs: Any) -> subprocess.Popen[bytes]:
        if command[0] != sys.executable:
            return real_popen(command, **kwargs)
        process = real_popen([sys.executable, "-c", "import time; time.sleep(30)"], **kwargs)
        children.append(process)
        return process

    def wait_for_runtime(_self: object, *_args: object) -> None:
        starting.set()
        assert finish.wait(timeout=5), "test did not release startup"

    def stop(self: QemuRuntimeAdapter, *args: Any, **kwargs: Any) -> None:
        stopping.set()
        assert finish_stop.wait(timeout=5), "test did not release stop"
        if termination_denied:
            raise RuntimeError("test termination denied")
        real_stop(self, *args, **kwargs)

    monkeypatch.setattr(manager, "_find_qemu_binary", lambda: Path(sys.executable))
    monkeypatch.setattr("celesto.vm.subprocess.Popen", launch)
    monkeypatch.setattr(QemuRuntimeAdapter, "_wait_for_runtime", wait_for_runtime)
    monkeypatch.setattr(QemuRuntimeAdapter, "stop", stop)
    task = asyncio.create_task(manager.async_start(config.vm_id))
    try:
        assert await asyncio.to_thread(starting.wait, 5), "runtime did not launch"
        assert len(children) == 1
        assert not manager._public_egress
        for _ in range(cancel_count):
            task.cancel()
            await asyncio.sleep(0)
            assert not task.done(), "cancelled caller abandoned the startup worker"
            with pytest.raises(CelestoError, match="busy"):
                manager.start(config.vm_id)
        assert children[0].poll() is None

        finish.set()
        if cancel_during_stop:
            assert await asyncio.to_thread(stopping.wait, 5), "cleanup did not start"
            task.cancel()
            await asyncio.sleep(0)
            assert not task.done(), "cancelled caller abandoned the stop worker"
            with pytest.raises(CelestoError, match="busy"):
                manager.start(config.vm_id)
            finish_stop.set()
        if fail_stop:
            with pytest.raises(RuntimeError, match="termination denied"):
                await task
            retained = manager.get(config.vm_id)
            assert retained.pid == children[0].pid
            assert retained.status == VMState.RUNNING
            assert children[0].poll() is None
            termination_denied = False
            await manager.async_stop(config.vm_id)
        else:
            with pytest.raises(asyncio.CancelledError):
                await task
        assert manager.get(config.vm_id).status == VMState.STOPPED
        assert manager.get(config.vm_id).pid is None
        children[0].wait(timeout=5)
        (tmp_path / "cancelled-non-public-start.json").write_text(
            json.dumps(
                {
                    "cancel_count": cancel_count,
                    "termination_initially_denied": fail_stop,
                    "cancel_during_stop": cancel_during_stop,
                    "pid": children[0].pid,
                    "returncode": children[0].returncode,
                    "status": manager.get(config.vm_id).status.value,
                }
            )
        )
    finally:
        finish.set()
        finish_stop.set()
        termination_denied = False
        await asyncio.gather(task, return_exceptions=True)
        for process in children:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=5)
        manager.close()

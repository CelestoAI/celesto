# Copyright 2026 Celesto AI
"""Shutdown completion before another operation reuses guest resources.

Failure modes designed before repair: forced stop returns before process exit;
a failed kill reports success and removes its recovery socket; an already dead
VM receives unnecessary signals. These controlled runtime-context cases cover
slow/failed shutdown that cannot be reliably injected into the live KVM suite.
The real identity/restore E2E test is the live Linux verification boundary.
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from celesto.exceptions import CelestoError
from celesto.runtime.base import RuntimeContext
from celesto.runtime.firecracker import FirecrackerRuntimeAdapter
from celesto.types import VMConfig, VMInfo, VMState


def _context(tmp_path: Path) -> RuntimeContext:
    return RuntimeContext(
        data_dir=tmp_path,
        socket_dir=tmp_path,
        firmware_dir=tmp_path / "firmware",
        log_files={},
        process_handles={},
        resolve_boot_args=lambda info: info.config.boot_args,
        start_firecracker=MagicMock(),
        start_qemu=MagicMock(),
        unlink_socket=MagicMock(),
        kill_process=MagicMock(),
        wait_for_process=MagicMock(),
        is_process_running=MagicMock(),
        find_qemu_binary=MagicMock(),
    )


def _info(tmp_path: Path) -> VMInfo:
    kernel, disk, control = tmp_path / "kernel", tmp_path / "disk.ext4", tmp_path / "fc.sock"
    for path in (kernel, disk, control):
        path.touch()
    return VMInfo(
        vm_id="fc-stop",
        pid=12345,
        status=VMState.PAUSED,
        control_socket_path=control,
        config=VMConfig(
            vm_id="fc-stop", kernel_path=kernel, rootfs_path=disk, backend="firecracker"
        ),
    )


def test_forced_stop_waits_for_exit_before_removing_control_socket(tmp_path: Path) -> None:
    context, info = _context(tmp_path), _info(tmp_path)
    events: list[str] = []
    exited = False

    def wait(pid: int, timeout: float) -> None:
        nonlocal exited
        events.append("wait")
        exited = True

    context.is_process_running = lambda pid: not exited
    context.kill_process = lambda pid: events.append("kill")
    context.wait_for_process = wait
    context.unlink_socket = lambda path: events.append("unlink")

    FirecrackerRuntimeAdapter(context).stop(info, timeout=3.0)

    assert events == ["kill", "wait", "unlink"]
    assert exited


def test_failed_forced_stop_preserves_recovery_socket(tmp_path: Path) -> None:
    context, info = _context(tmp_path), _info(tmp_path)
    context.is_process_running = lambda pid: True
    with pytest.raises(CelestoError, match="celesto sandbox stop fc-stop"):
        FirecrackerRuntimeAdapter(context).stop(info, timeout=3.0)
    context.unlink_socket.assert_not_called()
    assert info.control_socket_path is not None and info.control_socket_path.exists()


def test_stopping_an_exited_vm_only_removes_its_socket(tmp_path: Path) -> None:
    context, info = _context(tmp_path), _info(tmp_path)
    context.is_process_running = lambda pid: False
    FirecrackerRuntimeAdapter(context).stop(info, timeout=3.0)
    context.kill_process.assert_not_called()
    context.wait_for_process.assert_not_called()
    context.unlink_socket.assert_called_once_with(info.control_socket_path)

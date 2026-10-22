# Copyright 2026 Celesto AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0

"""A finished lifecycle call must hand its lock back to other processes at once.

Ways this can fail, and what the tests check:

- Release raises after the work is done, so the caller gets an error instead
  of the result (seen when the lock file's ``name`` was a file descriptor).
- Release never unlocks, so another process waits 30 seconds and gives up.
- The thread keeps a stale lock record, so a second call on the same thread
  never really releases either.

Each test writes ``lock-release-report.json`` to its temporary directory.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest

from celesto.types import VMConfig, VMState
from celesto.vm import CelestoManager

pytest.importorskip("fcntl")

# Another process tries the lock once, without waiting.
_TRY_LOCK = """
import fcntl, sys
with open(sys.argv[1], "a") as f:
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("busy")
    else:
        print("free")
"""


def _other_process_can_lock(path: Path) -> bool:
    out = subprocess.run(
        [sys.executable, "-I", "-c", _TRY_LOCK, str(path)],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    return out.stdout.strip() == "free"


def _manager_with_created_vm(tmp_path: Path) -> tuple[CelestoManager, str]:
    manager = CelestoManager(data_dir=tmp_path / "data", socket_dir=tmp_path / "sockets")
    vm_id = "lock-release"
    rootfs = tmp_path / "rootfs.ext4"
    kernel = tmp_path / "vmlinux"
    rootfs.touch()
    kernel.touch()
    manager.state.create_vm(VMConfig(vm_id=vm_id, kernel_path=kernel, rootfs_path=rootfs))
    return manager, vm_id


def _write_report(tmp_path: Path, report: dict[str, object]) -> None:
    (tmp_path / "lock-release-report.json").write_text(json.dumps(report, indent=2))


def test_stop_releases_lifecycle_lock_for_other_processes(tmp_path: Path) -> None:
    manager, vm_id = _manager_with_created_vm(tmp_path)
    lock_path = manager.data_dir / "locks" / manager._lifecycle_lock_name(vm_id)

    first = manager.stop(vm_id)
    free_after_first = _other_process_can_lock(lock_path)
    second = manager.stop(vm_id)
    free_after_second = _other_process_can_lock(lock_path)

    _write_report(
        tmp_path,
        {
            "first_status": first.status.value,
            "second_status": second.status.value,
            "free_after_first": free_after_first,
            "free_after_second": free_after_second,
        },
    )
    assert first.status is VMState.CREATED
    assert free_after_first
    assert second.status is VMState.CREATED
    assert free_after_second


def test_async_stop_releases_lifecycle_lock_for_other_processes(tmp_path: Path) -> None:
    manager, vm_id = _manager_with_created_vm(tmp_path)
    lock_path = manager.data_dir / "locks" / manager._lifecycle_lock_name(vm_id)

    info = asyncio.run(manager.async_stop(vm_id))
    free = _other_process_can_lock(lock_path)

    _write_report(tmp_path, {"status": info.status.value, "free_after_async_stop": free})
    assert info.status is VMState.CREATED
    assert free

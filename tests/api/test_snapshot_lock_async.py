# Copyright 2026 Celesto AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Async stop and delete wait for a snapshot without stalling the event loop.

The end-to-end suite (``tests/e2e/test_snapshot_locks.py``) drives the sync
CLI path only. These isolated tests cover the async SDK path, which it cannot
reach. Ways the async locking can fail:

1. ``async_delete`` of a running sandbox takes the snapshot lock, then calls a
   stop that takes it again, so it hangs forever.
2. ``async_stop`` or ``async_delete`` skip the lock and run mid-snapshot.
3. The blocking ``flock`` runs on the event loop thread, freezing every other
   coroutine until the snapshot finishes.
4. The wait notice never fires while waiting, or fires when nothing waits.

Cancellation while waiting is not covered: it matches the existing create
lock, whose worker thread keeps the lock until its file is garbage collected.
"""

from __future__ import annotations

import asyncio
import fcntl
import threading
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from celesto.exceptions import VMNotFoundError
from celesto.types import VMConfig, VMState
from celesto.vm import CelestoManager

VM_ID = "sbx-einstein"


@pytest.fixture
def manager(tmp_path: Path) -> CelestoManager:
    """A manager with one running QEMU sandbox and a stubbed runtime."""
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.ext4"
    kernel.touch()
    rootfs.touch()
    vm_manager = CelestoManager(data_dir=tmp_path / "data", socket_dir=tmp_path / "sockets")
    vm_manager.state.create_vm(
        VMConfig(vm_id=VM_ID, kernel_path=kernel, rootfs_path=rootfs, backend="qemu")
    )
    vm_manager.state.update_vm(VM_ID, status=VMState.RUNNING, pid=99999)

    adapter = MagicMock()
    adapter.async_stop = AsyncMock()
    vm_manager._runtime_adapter_for_backend = MagicMock(return_value=adapter)  # type: ignore[method-assign]
    vm_manager._async_cleanup_resources = AsyncMock()  # type: ignore[method-assign]
    return vm_manager


def _hold_snapshot_lock(manager: CelestoManager, seconds: float) -> threading.Event:
    """Hold the sandbox's snapshot lock from another thread, like a snapshot would."""
    acquired = threading.Event()
    lock_path = manager.data_dir / "locks" / f"{VM_ID}.snapshot.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    def hold() -> None:
        with lock_path.open("w") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            acquired.set()
            threading.Event().wait(seconds)
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    threading.Thread(target=hold, daemon=True).start()
    assert acquired.wait(5)
    return acquired


@pytest.mark.asyncio
async def test_async_delete_of_running_sandbox_does_not_deadlock(
    manager: CelestoManager,
) -> None:
    notices: list[str] = []

    await asyncio.wait_for(
        manager.async_delete(VM_ID, on_snapshot_wait=lambda: notices.append("waiting")),
        timeout=5,
    )

    with pytest.raises(VMNotFoundError):
        manager.state.get_vm(VM_ID)
    assert notices == []


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["async_stop", "async_delete"])
async def test_async_action_waits_for_snapshot_without_blocking_event_loop(
    manager: CelestoManager,
    action: str,
) -> None:
    notices: list[str] = []
    _hold_snapshot_lock(manager, seconds=0.6)

    task = asyncio.create_task(
        getattr(manager, action)(VM_ID, on_snapshot_wait=lambda: notices.append("waiting"))
    )
    loop = asyncio.get_running_loop()
    started = loop.time()
    await asyncio.sleep(0.2)

    # A blocked loop would only wake after the 0.6s hold, with the task done.
    assert loop.time() - started < 0.5, "the event loop stalled while waiting"
    assert not task.done(), f"{action} ran while the snapshot still held the lock"
    assert notices == ["waiting"]

    await asyncio.wait_for(task, timeout=5)
    if action == "async_stop":
        assert manager.state.get_vm(VM_ID).status == VMState.STOPPED
    else:
        with pytest.raises(VMNotFoundError):
            manager.state.get_vm(VM_ID)

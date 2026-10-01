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

"""Cancelling an async fork while it copies disks.

A caller can cancel ``async_fork()`` at any await, for example with
``asyncio.wait_for``. The disk copies run in worker threads, which a
cancellation can't stop, so the fork must wait for them before it gives up.
A real run can't cancel at an exact moment, so these tests hold one copy
open and cancel while it runs. Failure modes, written before the code:

1. Cancelling while the source's disk is copied releases the source's
   snapshot lock while the copy still runs, so ``stop`` or ``delete`` of the
   source can run in the middle of it (D6).
2. Cancelling while the source's disk is copied leaves the finished
   generation behind once the copy completes (D12).
3. Cancelling while a child's disk is copied removes the child's record
   while the copy is still writing its disk, leaving a disk no record owns.
4. Cancelling while a child's disk is copied deletes the generation while
   the copy still reads from it.
5. A child whose copy finished but who was never started is left behind.
6. The fork returns before its worker threads finish, or swallows the
   cancellation instead of raising it.

The copy step (``_copy_with_reflink``) is the boundary held open; the fork's
lock, generation, child records and cleanup are real.
"""

from __future__ import annotations

import asyncio
import fcntl
import threading
from pathlib import Path
from typing import Any

import pytest

from celesto.types import VMState
from celesto.vm import CelestoManager
from tests.vm.test_fork_children import _SOURCE, _World, world  # noqa: F401 - fixture

_REAL_ASYNC_CREATE_FROM_DISK = CelestoManager._async_create_from_disk
_REAL_DELETE_UNLOCKED = CelestoManager._delete_unlocked


class _Gate:
    """Holds one disk copy open, after it has read its source."""

    def __init__(self, held: Any) -> None:
        self.held = held
        self.entered = threading.Event()
        self.release = threading.Event()
        self.finished = threading.Event()

    def copy(self, source_path: Path, target_path: Path) -> None:
        data = source_path.read_bytes()
        if not self.held(target_path):
            target_path.write_bytes(data)
            return
        self.entered.set()
        assert self.release.wait(10), "the test never released the copy"
        target_path.write_bytes(data)
        self.finished.set()


def _lock_is_free(world: _World) -> bool:  # noqa: F811
    path = world.manager.data_dir / "locks" / f"{_SOURCE}.snapshot.lock"
    with path.open("w") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        return True


async def _cancel_while_held(world: _World, gate: _Gate) -> tuple[bool, bool]:  # noqa: F811
    """Cancel the fork while *gate* holds a copy; report what was true meanwhile."""
    source = world.add_source("firecracker", VMState.STOPPED)
    task = asyncio.ensure_future(source._async_fork_many(1, boot_timeout=30))
    assert await asyncio.to_thread(gate.entered.wait, 10), "the copy never started"
    task.cancel()
    await asyncio.sleep(0.3)
    returned_early = task.done()
    lock_free = _lock_is_free(world)
    gate.release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    copy_running_after_return = not gate.finished.is_set()
    # Let a copy that outlived the fork finish before the test inspects disks.
    await asyncio.to_thread(gate.finished.wait, 10)
    await asyncio.sleep(0.3)
    return returned_early or copy_running_after_return, lock_free


@pytest.fixture
def gated(world: _World, monkeypatch: pytest.MonkeyPatch) -> _World:  # noqa: F811
    # Real child records and disks, so a disk no record owns is visible.
    monkeypatch.setattr(CelestoManager, "_async_create_from_disk", _REAL_ASYNC_CREATE_FROM_DISK)
    monkeypatch.setattr(CelestoManager, "_delete_unlocked", _REAL_DELETE_UNLOCKED)
    # Userspace networking: no host network devices are made for children.
    monkeypatch.setattr(
        CelestoManager, "_uses_host_tap_networking", staticmethod(lambda config, backend: False)
    )
    return world


def test_cancelling_during_the_source_copy_waits_and_removes_the_generation(
    gated: _World, monkeypatch: pytest.MonkeyPatch
) -> None:
    gate = _Gate(held=lambda target: target.is_relative_to(gated.manager.snapshot_dir))
    monkeypatch.setattr(CelestoManager, "_copy_with_reflink", staticmethod(gate.copy))

    returned_early, lock_free = asyncio.run(_cancel_while_held(gated, gate))

    assert not returned_early, "the fork returned while the source was still being copied"
    assert not lock_free, "stop or delete of the source could run in the middle of the copy"
    assert gated.generations() == []
    assert [vm.vm_id for vm in gated.state.list_vms()] == ["src"]


def test_cancelling_during_a_child_copy_leaves_no_child_or_generation(
    gated: _World, monkeypatch: pytest.MonkeyPatch
) -> None:
    gate = _Gate(held=lambda target: target.name.startswith("src-1"))
    monkeypatch.setattr(CelestoManager, "_copy_with_reflink", staticmethod(gate.copy))

    returned_early, _ = asyncio.run(_cancel_while_held(gated, gate))

    assert not returned_early, "the fork returned while a child's disk was still being copied"
    assert [vm.vm_id for vm in gated.state.list_vms()] == ["src"]
    assert gated.manager._instance_disk_paths_for_id("src-1") == []
    assert gated.generations() == []

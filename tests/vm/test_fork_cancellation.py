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

"""Interrupting a fork while it copies disks or starts children.

A caller can cancel ``async_fork()`` at any await, for example with
``asyncio.wait_for``, and a CLI user can press Ctrl+C during
``celesto sandbox fork``, which raises ``KeyboardInterrupt`` in the sync fork.
The disk copies run in worker threads, which neither can stop, so the fork
must wait for them before it gives up, then remove what it made. A real run
can't interrupt at an exact moment, so these tests hold one step open and
interrupt while it runs. Failure modes, written before the code:

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
7. Cancelling while the generation is deleted, after every child was
   copied, raises before the children start and leaves them all behind,
   copied but never started.
8. Cancelling while the source's snapshot lock is released, right after the
   capture, raises before the generation's cleanup is armed, so the
   generation is left behind; or the cancelled release leaves the lock held.
9. Cancelling while children start leaves behind the children still waiting
   their turn and the child being started, or removes a child that had
   already started and passed its identity check before the cancellation.
10. Ctrl+C during a sync fork's child copies waits for every queued copy,
    then leaves every copied child behind, never started; or keeps copying
    children whose copy had not begun.
11. Ctrl+C during a sync fork's starts leaves the children not yet started
    behind, or removes a child that had already started and passed its check.
12. After Ctrl+C the generation is left behind, the source's snapshot lock
    stays held, or the ``KeyboardInterrupt`` is swallowed instead of raised.

The step held open is a boundary (the disk copy, a delete, the lock release,
opening a child, the hypervisor start); the fork's lock, generation, child
records and cleanup are real.
"""

from __future__ import annotations

import asyncio
import fcntl
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from celesto.facade import Celesto
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
    await asyncio.wait({task})
    with pytest.raises(asyncio.CancelledError):
        task.result()
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


class _Hold:
    """Holds one call open in its worker thread until the test lets it go."""

    def __init__(self) -> None:
        self.entered = threading.Event()
        self.release = threading.Event()
        self.finished = threading.Event()

    def wait_here(self) -> None:
        self.entered.set()
        assert self.release.wait(10), "the test never let the held call go"
        self.finished.set()


async def _cancel_while(hold: _Hold, fork: Any) -> bool:
    """Cancel *fork* while *hold* keeps one of its steps open, then await it."""
    task = asyncio.ensure_future(fork)
    assert await asyncio.to_thread(hold.entered.wait, 10), "the held step never ran"
    task.cancel()
    # Let the cancellation reach the fork before the held step finishes.
    await asyncio.sleep(0)
    returned_early = task.done()
    hold.release.set()
    await asyncio.wait({task})
    with pytest.raises(asyncio.CancelledError):
        task.result()
    return returned_early or not hold.finished.is_set()


def _rows(world: _World) -> list[tuple[str, VMState]]:  # noqa: F811
    return sorted((vm.vm_id, vm.status) for vm in world.state.list_vms())


def test_cancelling_while_the_generation_is_deleted_removes_the_copied_children(
    world: _World,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hold = _Hold()
    real_delete_snapshot = CelestoManager.delete_snapshot

    def held_delete_snapshot(self: CelestoManager, snapshot_id: str) -> None:
        if snapshot_id.startswith("fork-"):
            hold.wait_here()
        real_delete_snapshot(self, snapshot_id)

    monkeypatch.setattr(CelestoManager, "delete_snapshot", held_delete_snapshot)
    source = world.add_source("firecracker", VMState.STOPPED)

    asyncio.run(_cancel_while(hold, source._async_fork_many(2, boot_timeout=30)))

    assert _rows(world) == [("src", VMState.STOPPED)]
    assert world.generations() == []


def test_cancelling_while_the_snapshot_lock_is_released_still_removes_the_generation(
    world: _World,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hold = _Hold()
    real_release = CelestoManager._release_vm_create_lock

    def held_release(lock: Any) -> None:
        _, lock_file = lock
        is_source_lock = lock_file is not None and lock_file.name.endswith(
            f"{_SOURCE}.snapshot.lock"
        )
        if is_source_lock and not hold.entered.is_set():
            hold.wait_here()
        real_release(lock)

    monkeypatch.setattr(CelestoManager, "_release_vm_create_lock", staticmethod(held_release))
    source = world.add_source("firecracker", VMState.STOPPED)

    asyncio.run(_cancel_while(hold, source._async_fork_many(1, boot_timeout=30)))

    assert _lock_is_free(world), "the cancelled fork kept the source's snapshot lock"
    assert world.generations() == []
    assert _rows(world) == [("src", VMState.STOPPED)]


def test_cancelling_while_children_start_keeps_started_children_and_removes_the_rest(
    world: _World,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hold = _Hold()
    real_handle = Celesto._fork_child_handle

    def held_handle(self: Celesto, plan: Any, name: str) -> Celesto:
        if name == "src-2":
            hold.wait_here()
        return real_handle(self, plan, name)

    monkeypatch.setattr(Celesto, "_fork_child_handle", held_handle)
    source = world.add_source("firecracker", VMState.STOPPED)

    # One at a time: src-1 starts and passes its check, src-2 is held while
    # it opens, and src-3 is still waiting its turn.
    asyncio.run(_cancel_while(hold, source._async_fork_many(3, parallel=1, boot_timeout=30)))

    assert _rows(world) == [("src", VMState.STOPPED), ("src-1", VMState.RUNNING)]
    assert world.generations() == []
    assert _lock_is_free(world)


def test_cancelling_during_child_start_waits_for_start_to_finish() -> None:
    from celesto.facade import _ForkPlan

    hold = _Hold()
    child: Any = SimpleNamespace()

    def start(**_kwargs: Any) -> None:
        hold.wait_here()

    async def async_start(**_kwargs: Any) -> None:
        await asyncio.to_thread(start)

    child.start = start
    child.async_start = async_start
    child.close = lambda: None
    facade: Any = Celesto.__new__(Celesto)
    facade._fork_child_handle = lambda *_args: child
    facade._confirm_fork_child = lambda *_args: SimpleNamespace(
        name="src-1", ok=True, sandbox=child
    )
    plan = _ForkPlan(
        source=cast(Any, object()),
        identity=cast(Any, object()),
        shared_base=None,
        names=["src-1"],
        boot_timeout=30,
    )

    returned_early = asyncio.run(_cancel_while(hold, facade._async_start_fork_child(plan, "src-1")))

    assert not returned_early, "cancellation escaped while the child start was still running"


def test_cancelling_during_child_handle_creation_closes_handle_after_thread_finishes() -> None:
    from celesto.facade import _ForkPlan

    hold = _Hold()
    opened: list[SimpleNamespace] = []

    def held_handle(*_args: Any) -> SimpleNamespace:
        child = SimpleNamespace(closed=False)

        def close() -> None:
            child.closed = True

        child.close = close
        opened.append(child)
        hold.wait_here()
        return child

    facade: Any = Celesto.__new__(Celesto)
    facade._fork_child_handle = held_handle
    plan = _ForkPlan(
        source=cast(Any, object()),
        identity=cast(Any, object()),
        shared_base=None,
        names=["src-1"],
        boot_timeout=30,
    )

    returned_early = asyncio.run(_cancel_while(hold, facade._async_start_fork_child(plan, "src-1")))

    assert not returned_early, "cancellation escaped while the handle factory was still running"
    assert len(opened) == 1
    assert opened[0].closed


def test_sync_fork_deletes_generation_if_snapshot_lock_exit_is_interrupted(
    tmp_path: Path,
) -> None:
    import contextlib
    from types import TracebackType

    from celesto.facade import _ForkPlan

    class InterruptOnExit:
        def __enter__(self) -> None:
            return None

        def __exit__(
            self,
            _exc_type: type[BaseException] | None,
            _exc: BaseException | None,
            _traceback: TracebackType | None,
        ) -> bool:
            raise KeyboardInterrupt("interrupted while releasing snapshot lock")

    class SDK:
        @staticmethod
        def _fork_names_lock(*_args: Any, **_kwargs: Any) -> Any:
            return contextlib.nullcontext()

        @staticmethod
        def _vm_snapshot_lock(*_args: Any, **_kwargs: Any) -> InterruptOnExit:
            return InterruptOnExit()

    generation_path = tmp_path / "generation.qcow2"
    sandbox: Any = Celesto.__new__(Celesto)
    sandbox._vm_id = "src"
    sandbox._sdk = SDK()
    plan = _ForkPlan(
        source=cast(Any, object()),
        identity=cast(Any, object()),
        shared_base=None,
        names=["src-1"],
        boot_timeout=30,
    )
    sandbox._plan_fork = lambda *_args, **_kwargs: plan
    sandbox._claim_fork_names = lambda current, _name: current
    deleted: list[Path] = []

    def capture(_notify: Any, **_kwargs: Any) -> tuple[Any, tuple[str, ...]]:
        generation_path.write_bytes(b"captured generation")
        return SimpleNamespace(path=generation_path), ()

    def delete_generation(generation: Any) -> tuple[str, ...]:
        deleted.append(generation.path)
        generation.path.unlink()
        return ()

    sandbox._capture_fork_generation = capture
    sandbox._delete_fork_generation = delete_generation

    with pytest.raises(KeyboardInterrupt, match="interrupted while releasing"):
        sandbox._fork_many(1, boot_timeout=30)

    assert len(deleted) == 1
    assert deleted == [generation_path]
    assert not generation_path.exists()


@pytest.mark.parametrize("step", ["copy", "start"])
def test_ctrl_c_during_a_sync_fork_removes_unstarted_children_and_raises(
    world: _World,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    step: str,
) -> None:
    # A KeyboardInterrupt from inside a worker reaches the fork exactly where
    # a Ctrl+C would: while it waits for that child's step to finish.
    if step == "copy":

        def create_from_disk(self: CelestoManager, *args: Any, **kwargs: Any) -> Any:
            if args[2] == "src-2":
                raise KeyboardInterrupt
            return world.create_from_disk(*args, **kwargs)

        monkeypatch.setattr(CelestoManager, "_create_from_disk", create_from_disk)
    else:

        def start(self: CelestoManager, vm_id: str, boot_timeout: float = 30.0) -> Any:
            if vm_id == "src-2":
                raise KeyboardInterrupt
            return world.start(vm_id)

        monkeypatch.setattr(CelestoManager, "start", start)
    source = world.add_source("firecracker", VMState.STOPPED)

    with pytest.raises(KeyboardInterrupt):
        source._fork_many(3, parallel=1, boot_timeout=30)

    if step == "copy":
        # src-1 was copied and removed; src-3's copy never began.
        assert world.created == ["src-1"]
        assert _rows(world) == [("src", VMState.STOPPED)]
    else:
        # src-1 had started and passed its check before the interrupt.
        assert _rows(world) == [("src", VMState.STOPPED), ("src-1", VMState.RUNNING)]
    assert world.generations() == []
    assert _lock_is_free(world)

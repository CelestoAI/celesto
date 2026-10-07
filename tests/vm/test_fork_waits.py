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

"""What waits for a fork of the same source, and what it tells the user (D6).

The e2e tests race real commands, so whether one actually waited depends on
timing. Here the first fork is held at a known point (copying children, or
saving the generation) with the real file locks, so the race is
deterministic. Failure modes, written before the tests:

1. A second fork of the same source waits silently, so the command looks
   stuck, or shows the waiting notice more than once.
2. The waiting notice names another sandbox, or is shown by a fork that
   didn't wait.
3. ``stop`` or ``delete`` of the source runs while a fork is saving its
   copy, so the copy is cut short.
4. ``stop`` or ``delete`` waits silently (its ``on_snapshot_wait`` callback
   is never called), or keeps waiting after the copy is saved, while the
   children are still being copied.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

import pytest

from celesto.facade import Celesto
from celesto.types import VMInfo, VMState
from celesto.vm import CelestoManager
from tests.vm.test_fork_children import _World, world  # noqa: F401 - fixture

_WAITING = "Waiting for the current snapshot or fork of src"
_TIMEOUT = 10.0


def _handle(world: _World) -> Celesto:  # noqa: F811
    return Celesto.from_id("src", state_manager=world.state, data_dir=world.manager.data_dir)


class _Run(threading.Thread):
    """Runs one call in a thread and keeps its result or exception."""

    def __init__(self, call: Any) -> None:
        super().__init__(daemon=True)
        self._call = call
        self.result: Any = None
        self.error: Exception | None = None
        self.finished_at: float | None = None

    def run(self) -> None:
        try:
            self.result = self._call()
        except Exception as exc:  # noqa: BLE001 - checked by the test
            self.error = exc
        self.finished_at = time.monotonic()


def _wait_for(condition: Any, what: str) -> None:
    deadline = time.monotonic() + _TIMEOUT
    while not condition():
        if time.monotonic() > deadline:
            pytest.fail(f"timed out waiting for {what}")
        time.sleep(0.01)


def test_a_second_fork_shows_the_waiting_notice_once_then_continues(
    world: _World,  # noqa: F811
) -> None:
    world.add_source("firecracker", VMState.STOPPED)
    copying = threading.Event()
    release = threading.Event()
    original_copy = world.create_from_disk

    def held_copy(source: VMInfo, disk_path: Path, name: str, **kwargs: Any) -> VMInfo:
        if name == "src-1":
            # The first fork holds the names lock while it copies children.
            copying.set()
            assert release.wait(_TIMEOUT)
        return original_copy(source, disk_path, name, **kwargs)

    world.create_from_disk = held_copy  # type: ignore[method-assign]
    first_notices: list[str] = []
    second_notices: list[str] = []
    first = _Run(
        lambda: _handle(world)._fork_many(2, boot_timeout=30, on_notice=first_notices.append)
    )
    first.start()
    assert copying.wait(_TIMEOUT)
    second = _Run(
        lambda: _handle(world)._fork_many(2, boot_timeout=30, on_notice=second_notices.append)
    )
    second.start()
    _wait_for(lambda: second_notices, "the second fork's waiting notice")
    # Still waiting: nothing of its own was copied yet.
    assert second.is_alive()
    assert not {"src-3", "src-4"} & set(world.created), world.created

    release.set()
    first.join(_TIMEOUT)
    second.join(_TIMEOUT)

    assert first.error is None and second.error is None, (first.error, second.error)
    assert first_notices == []
    assert len(second_notices) == 1, second_notices
    assert second_notices[0].startswith(_WAITING), second_notices
    assert [c.name for c in first.result.children] == ["src-1", "src-2"]
    assert [c.name for c in second.result.children] == ["src-3", "src-4"]
    assert world.generations() == []


class _Race:
    """A fork held while it saves its copy, raced by ``stop`` or ``delete``."""

    def __init__(self, world: _World, monkeypatch: pytest.MonkeyPatch, action: str) -> None:  # noqa: F811
        self.saving = threading.Event()
        self.release = threading.Event()
        self.action_done = threading.Event()
        self.saved_at: list[float] = []
        self.copy_saw_action_done: list[bool] = []
        self.waits: list[str] = []
        original_capture = CelestoManager._capture_stopped_disk
        original_copy = world.create_from_disk

        def held_capture(manager: CelestoManager, *args: Any, **kwargs: Any) -> Any:
            # Called with the source's snapshot lock held.
            self.saving.set()
            assert self.release.wait(_TIMEOUT)
            result = original_capture(manager, *args, **kwargs)
            self.saved_at.append(time.monotonic())
            return result

        def held_copy(source: VMInfo, disk_path: Path, name: str, **kwargs: Any) -> VMInfo:
            # The child's copy waits for the stop or delete, which must not
            # wait for the children in turn.
            self.copy_saw_action_done.append(self.action_done.wait(_TIMEOUT))
            return original_copy(source, disk_path, name, **kwargs)

        monkeypatch.setattr(CelestoManager, "_capture_stopped_disk", held_capture)
        world.create_from_disk = held_copy  # type: ignore[method-assign]
        self.fork = _Run(lambda: _handle(world)._fork_many(1, boot_timeout=30))
        call = getattr(_handle(world), action)

        def act() -> None:
            try:
                call(on_snapshot_wait=lambda: self.waits.append(action))
            finally:
                self.action_done.set()

        self.other = _Run(act)


@pytest.mark.parametrize("action", ["stop", "delete"])
def test_stop_and_delete_wait_while_a_fork_saves_its_copy(
    world: _World,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    action: str,
) -> None:
    world.add_source("firecracker", VMState.STOPPED)
    race = _Race(world, monkeypatch, action)
    race.fork.start()
    assert race.saving.wait(_TIMEOUT)

    race.other.start()
    _wait_for(lambda: race.waits, f"{action} to report that it waits")
    time.sleep(0.2)
    # Still waiting for the copy: the source is untouched.
    assert race.other.is_alive()
    assert world.deleted == []
    assert world.state.get_vm("src").status == VMState.STOPPED

    race.release.set()
    race.other.join(_TIMEOUT)
    race.fork.join(_TIMEOUT)

    assert race.other.error is None, race.other.error
    assert race.waits == [action]
    assert race.saved_at and race.other.finished_at is not None
    assert race.other.finished_at >= race.saved_at[0]
    # It went ahead once the copy was saved, while the child was still copying.
    assert race.copy_saw_action_done == [True]
    if action == "delete":
        assert world.deleted == ["src"]
    else:
        assert race.fork.error is None, race.fork.error
        assert [(c.name, c.ok) for c in race.fork.result.children] == [("src-1", True)]


def test_a_fork_whose_source_is_deleted_after_its_copy_still_reports_its_child(
    world: _World,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    world.add_source("firecracker", VMState.STOPPED)
    race = _Race(world, monkeypatch, "delete")
    race.fork.start()
    assert race.saving.wait(_TIMEOUT)
    race.other.start()
    _wait_for(lambda: race.waits, "delete to report that it waits")
    race.release.set()
    race.other.join(_TIMEOUT)
    race.fork.join(_TIMEOUT)

    assert world.deleted == ["src"]
    assert sorted(vm.vm_id for vm in world.state.list_vms()) == ["src-1"]
    assert race.fork.error is None, race.fork.error
    assert [(c.name, c.ok) for c in race.fork.result.children] == [("src-1", True)]
    # The source is gone, so its state is reported as unknown rather than raising.
    assert race.fork.result.source_state is None

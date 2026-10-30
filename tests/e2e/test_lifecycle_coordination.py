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

"""Overlapping lifecycle operations on real computers (issue #661).

Each test forces one competing order with a timing gate placed on a real
operation (disk copy, resource setup, leftover scan), then checks the
outcome against the real guest, disk and inventory. No hypervisor, disk or
process operation returns a mocked result.

Ways each case can fail, written before the fix:

1. Snapshot deletion during restore: deletion removes the snapshot disk while
   restore waits to read it; restore fails and leaves the computer in error.
2. Deletion during creation: deletion removes the disk and row before
   networking finishes; creation fails with a foreign-key error, or deletion
   leaves resources behind.
3. Start through a stale handle: a handle that cached "running" treats start
   as a no-op while the computer is stopped (sync and async).
4. Stale health check: a check for an old process marks the computer's newer
   runtime as failed and clears its process ID.
5. Prune after the disk changes owner: prune deletes a disk that a recreated
   computer with the same name now uses.
6. Cancelling an async start after QEMU launched: the lifecycle lock is
   released while the launch is still running, the row keeps no process ID,
   and the guest keeps running untracked. A later start then fights it for
   the disk.
7. Cancelling an async stop: the lock is released while QEMU is still
   stopping, and the row still says "running" with a dead process ID.
8. Cancelling an async delete: the lock is released while files are still
   being removed, and the row survives with its disk gone.
9. Stopping during a snapshot: the snapshot finishes afterwards and marks the
   stopped computer "paused" with no process, so it can no longer start.

Every test writes a JSON report of what happened, in order, to
``$CELESTO_E2E_ARTIFACT_DIR`` (or pytest's temporary folder), and checks that
no runtime process started by the test is left running.
"""

from __future__ import annotations

import asyncio
import json
import os
import platform
import signal
import subprocess
import tempfile
import threading
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from _util import BOOT_TIMEOUT, _qemu_binary_available, require_backend_available, selected_backend

from celesto import Celesto
from celesto.cli._sqlite import SQLiteStateManager
from celesto.exceptions import CelestoError, VMNotFoundError
from celesto.facade import _build_auto_config
from celesto.runtime.backends import BACKEND_QEMU
from celesto.runtime.qemu import QemuRuntimeAdapter
from celesto.types import SnapshotType, VMConfig, VMState
from celesto.vm import CelestoManager

pytestmark = pytest.mark.e2e

ARTIFACT_DIR_ENV = "CELESTO_E2E_ARTIFACT_DIR"
# How long a waiting operation must stay blocked to count as "waited".
BLOCKED_SECONDS = 3.0
GATE_TIMEOUT = 120.0


def _require_qemu(config: pytest.Config, sandbox_name: str) -> None:
    """Skip unless this host can boot a real QEMU guest.

    macOS runs QEMU on Hypervisor.framework, so it needs only the binary.
    """
    selected = selected_backend(config)
    if selected not in ("all", BACKEND_QEMU):
        pytest.skip(
            f"End-to-end tests for 'qemu' are skipped because this run selected "
            f"'{selected}'; rerun with: pytest tests/e2e --e2e-backend qemu."
        )
    if platform.system() == "Darwin":
        if _qemu_binary_available():
            return
        message = (
            "End-to-end tests for 'qemu' cannot run because QEMU is not installed; "
            f"run 'brew install qemu' and rerun tests in sandbox '{sandbox_name}'."
        )
        if selected == BACKEND_QEMU:
            pytest.fail(message)
        pytest.skip(message)
    require_backend_available(BACKEND_QEMU, config, sandbox_name=sandbox_name)


@dataclass
class Report:
    """Ordered record of one race, written as the test's artifact."""

    case: str
    started: float = field(default_factory=time.monotonic)
    events: list[dict[str, Any]] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)

    def event(self, name: str, **details: Any) -> None:
        self.events.append(
            {"t": round(time.monotonic() - self.started, 3), "event": name, **details}
        )

    def write(self, directory: Path, name: str) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{name}.json"
        payload = {"case": self.case, "events": self.events, "facts": self.facts}
        path.write_text(json.dumps(payload, indent=2, default=str) + "\n")
        return path


@dataclass
class LiveCase:
    """An isolated inventory and the handles a test needs."""

    name: str
    data_dir: Path
    manager: CelestoManager
    state: SQLiteStateManager
    config: VMConfig
    handle_kwargs: dict[str, Any]
    report: Report

    def handle(self) -> Celesto:
        return Celesto.from_id(self.name, **self.handle_kwargs)


def _runtime_processes(data_dir: Path) -> list[str]:
    """Return command lines of running processes that use *data_dir*."""
    result = subprocess.run(
        ["ps", "-Awwo", "pid=,args="], capture_output=True, text=True, check=False
    )
    return [
        line.strip()
        for line in result.stdout.splitlines()
        if str(data_dir) in line and "ps -Awwo" not in line
    ]


@pytest.fixture
def live_case(request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[LiveCase]:
    _require_qemu(request.config, "lifecycle-coordination")
    name = f"e2e-lc-{uuid.uuid4().hex[:8]}"
    data = Path(tempfile.mkdtemp(prefix="lc-data-"))
    # UNIX socket paths must stay short on macOS regardless of pytest's cwd.
    sockets = Path(tempfile.mkdtemp(prefix="lc-", dir="/tmp"))
    state = SQLiteStateManager(data / "celesto.db")
    manager = CelestoManager(data_dir=data, socket_dir=sockets, state_manager=state)
    config, ssh_key = _build_auto_config(vm_name=name, os="alpine", backend=BACKEND_QEMU)
    kwargs = {
        "data_dir": data,
        "socket_dir": sockets,
        "state_manager": state,
        "ssh_key_path": ssh_key,
    }
    report = Report(case=request.node.name)
    report.facts["computer"] = name
    case = LiveCase(name, data, manager, state, config, kwargs, report)
    try:
        yield case
    finally:
        for info in state.list_vms():
            with suppress(Exception):
                manager.delete(info.vm_id)
        for snapshot in manager.list_snapshots():
            with suppress(Exception):
                manager.delete_snapshot(snapshot.snapshot_id)
        leftover_processes = _runtime_processes(data)
        report.facts["runtime_processes_after_cleanup"] = leftover_processes
        # Fail below, but never leave a stray guest running on this machine.
        for line in leftover_processes:
            with suppress(ValueError, OSError):
                os.kill(int(line.split(maxsplit=1)[0]), signal.SIGKILL)
        artifact_dir = Path(os.environ.get(ARTIFACT_DIR_ENV) or tmp_path)
        artifact = report.write(artifact_dir, f"{request.node.name}-{name}")
        print(f"lifecycle coordination report: {artifact}")
        manager.close()
        state.close()
        with suppress(OSError):
            sockets.rmdir()
        assert leftover_processes == [], f"runtime processes left running: {leftover_processes}"


class Gate:
    """Pause one real operation at a chosen point until released."""

    def __init__(self) -> None:
        self.entered = threading.Event()
        self.released = threading.Event()
        self._used = False
        self._lock = threading.Lock()

    def hold_once(self) -> None:
        with self._lock:
            if self._used:
                return
            self._used = True
        self.entered.set()
        if not self.released.wait(GATE_TIMEOUT):
            raise TimeoutError("test gate was never released")


def _in_thread(target: Callable[[], Any]) -> tuple[threading.Thread, dict[str, Any]]:
    """Run *target* in a thread, capturing its result or exception."""
    outcome: dict[str, Any] = {}

    def run() -> None:
        try:
            outcome["result"] = target()
        except BaseException as exc:  # noqa: BLE001 - reported by the test
            outcome["error"] = exc
        finally:
            outcome["finished_at"] = time.monotonic()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread, outcome


def _boot(case: LiveCase, config: VMConfig | None = None) -> Celesto:
    handle = Celesto(config=config or case.config, **case.handle_kwargs)
    handle.start(boot_timeout=BOOT_TIMEOUT)
    handle.wait_for_ready(timeout=BOOT_TIMEOUT)
    return handle


def _guest_answers(handle: Celesto) -> bool:
    with suppress(Exception):
        return handle.run("echo alive", timeout=30).stdout.strip() == "alive"
    return False


def _pid_alive(pid: int | None) -> bool:
    if pid is None or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


# ---------------------------------------------------------------------------
# 1. Snapshot deletion waits for restore
# ---------------------------------------------------------------------------


def test_snapshot_delete_waits_for_restore(
    live_case: LiveCase, monkeypatch: pytest.MonkeyPatch
) -> None:
    case, report = live_case, live_case.report
    source = _boot(case)
    assert source.run("echo restored-marker > /root/marker; sync").exit_code == 0
    snapshot = source.snapshot(snapshot_type=SnapshotType.DISK)
    source.stop()
    snapshot_disk = snapshot.artifacts.disk_path
    report.facts["snapshot_id"] = snapshot.snapshot_id
    report.facts["snapshot_disk"] = str(snapshot_disk)

    gate = Gate()
    original_copy = QemuRuntimeAdapter._copy_disk_standalone

    def gated_copy(src: Path, dest: Path, *, _depth: int = 0) -> None:
        if _depth == 0 and Path(src) == Path(snapshot_disk):
            report.event("restore_waiting_to_copy_snapshot_disk")
            gate.hold_once()
        original_copy(src, dest, _depth=_depth)

    monkeypatch.setattr(QemuRuntimeAdapter, "_copy_disk_standalone", staticmethod(gated_copy))

    restore_thread, restore = _in_thread(
        lambda: case.manager.restore_snapshot(snapshot.snapshot_id, resume_vm=True)
    )
    assert gate.entered.wait(GATE_TIMEOUT), "restore never reached the snapshot copy"

    delete_thread, deletion = _in_thread(lambda: case.manager.delete_snapshot(snapshot.snapshot_id))
    report.event("snapshot_delete_requested")
    delete_thread.join(BLOCKED_SECONDS)
    deletion_waited = delete_thread.is_alive()
    disk_present_while_waiting = snapshot_disk.exists()
    report.event(
        "while_restore_reads",
        deletion_waited=deletion_waited,
        snapshot_disk_present=disk_present_while_waiting,
    )

    released_at = time.monotonic()
    gate.released.set()
    restore_thread.join(GATE_TIMEOUT)
    delete_thread.join(GATE_TIMEOUT)
    report.event("restore_finished", error=repr(restore.get("error")))
    report.event("snapshot_delete_finished", error=repr(deletion.get("error")))

    restored = case.handle()
    restored.wait_for_ready(timeout=BOOT_TIMEOUT)
    marker = restored.run("cat /root/marker").stdout.strip()
    info = case.manager.get(case.name)
    report.facts.update(
        restore_error=repr(restore.get("error")),
        deletion_error=repr(deletion.get("error")),
        deletion_finished_after_restore=deletion.get("finished_at", 0) >= released_at,
        restored_status=info.status.value,
        restored_marker=marker,
    )

    assert deletion_waited, "snapshot deletion did not wait for the restore reading it"
    assert disk_present_while_waiting, "snapshot disk was removed while restore needed it"
    assert "error" not in restore, f"restore failed: {restore.get('error')!r}"
    assert info.status == VMState.RUNNING
    assert marker == "restored-marker"
    # After restore, deletion either removed the snapshot or refused because
    # the restored computer is active. Both keep the user's data intact.
    error = deletion.get("error")
    if error is not None:
        assert isinstance(error, CelestoError)
        assert "restored computer is active" in str(error)


# ---------------------------------------------------------------------------
# 2. Deletion waits for creation
# ---------------------------------------------------------------------------


def test_delete_waits_for_creation(live_case: LiveCase, monkeypatch: pytest.MonkeyPatch) -> None:
    case, report = live_case, live_case.report
    gate = Gate()
    original_ssh_forward = CelestoManager._should_reserve_ssh_forward

    def gated_ssh_forward(self: CelestoManager, config: VMConfig, *args: Any, **kw: Any) -> bool:
        if config.vm_id == case.name:
            # The CREATED row and disk exist; networking has not started.
            report.event("create_paused_before_networking")
            gate.hold_once()
        return original_ssh_forward(self, config, *args, **kw)

    monkeypatch.setattr(CelestoManager, "_should_reserve_ssh_forward", gated_ssh_forward)

    create_thread, creation = _in_thread(lambda: case.manager.create(case.config))
    assert gate.entered.wait(GATE_TIMEOUT), "create never reached resource setup"
    disk_paths = case.manager.leftover_paths_for_vm(case.name)
    report.facts["disk_paths"] = [str(path) for path in disk_paths]
    assert disk_paths, "create did not write a disk before networking"

    delete_thread, deletion = _in_thread(lambda: case.manager.delete(case.name))
    report.event("delete_requested")
    delete_thread.join(BLOCKED_SECONDS)
    deletion_waited = delete_thread.is_alive()
    row_present = _row_exists(case.state, case.name)
    disks_present = all(path.exists() for path in disk_paths)
    report.event(
        "while_create_runs",
        deletion_waited=deletion_waited,
        row_present=row_present,
        disks_present=disks_present,
    )

    gate.released.set()
    create_thread.join(GATE_TIMEOUT)
    delete_thread.join(GATE_TIMEOUT)
    report.event("create_finished", error=repr(creation.get("error")))
    report.event("delete_finished", error=repr(deletion.get("error")))
    report.facts.update(
        create_error=repr(creation.get("error")),
        delete_error=repr(deletion.get("error")),
        row_after=_row_exists(case.state, case.name),
        disks_after=[str(path) for path in disk_paths if path.exists()],
        ip_lease_after=case.state.get_ip_lease(case.name),
        ssh_port_after=case.state.get_ssh_port(case.name),
    )

    assert deletion_waited, "delete did not wait for create to finish"
    assert row_present and disks_present, "delete removed resources create was still using"
    assert "error" not in creation, f"create failed: {creation.get('error')!r}"
    assert "error" not in deletion, f"delete failed: {deletion.get('error')!r}"
    assert not _row_exists(case.state, case.name)
    assert not any(path.exists() for path in disk_paths)
    assert case.state.get_ssh_port(case.name) is None


def _row_exists(state: SQLiteStateManager, vm_id: str) -> bool:
    try:
        state.get_vm(vm_id)
    except VMNotFoundError:
        return False
    return True


# ---------------------------------------------------------------------------
# 3. Start through a stale handle uses current state
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("use_async", [False, True], ids=["sync-start", "async-start"])
def test_stale_handle_start_uses_current_state(live_case: LiveCase, use_async: bool) -> None:
    case, report = live_case, live_case.report
    first = _boot(case)
    stale = case.handle()
    assert stale.status == VMState.RUNNING
    first.stop()
    report.event(
        "stopped_through_other_handle",
        inventory=case.manager.get(case.name).status.value,
        stale_cached=stale.status.value,
    )

    if use_async:
        asyncio.run(stale.async_start(boot_timeout=BOOT_TIMEOUT))
    else:
        stale.start(boot_timeout=BOOT_TIMEOUT)
    stale.wait_for_ready(timeout=BOOT_TIMEOUT)
    info = case.manager.get(case.name)
    answers = _guest_answers(stale)
    report.event(
        "started_through_stale_handle",
        inventory=info.status.value,
        cached=stale.status.value,
        pid=info.pid,
        pid_alive=_pid_alive(info.pid),
        guest_answers=answers,
    )
    report.facts.update(final_inventory=info.status.value, final_cached=stale.status.value)

    assert info.status == VMState.RUNNING
    assert stale.status == VMState.RUNNING
    assert _pid_alive(info.pid)
    assert answers


# ---------------------------------------------------------------------------
# 4. A stale health check cannot overwrite a newer runtime
# ---------------------------------------------------------------------------


def test_stale_health_check_keeps_replacement_runtime(live_case: LiveCase) -> None:
    case, report = live_case, live_case.report
    handle = _boot(case)
    old_info = case.manager.get(case.name)
    handle.stop()
    handle.start(boot_timeout=BOOT_TIMEOUT)
    handle.wait_for_ready(timeout=BOOT_TIMEOUT)
    new_info = case.manager.get(case.name)
    report.event("restarted", old_pid=old_info.pid, new_pid=new_info.pid)
    assert old_info.pid != new_info.pid
    assert not _pid_alive(old_info.pid)

    returned = case.manager.refresh_status(old_info)
    after = case.manager.get(case.name)
    answers = _guest_answers(case.handle())
    report.event(
        "stale_health_check",
        returned_status=returned.status.value,
        returned_pid=returned.pid,
        inventory_status=after.status.value,
        inventory_pid=after.pid,
        guest_answers=answers,
    )
    report.facts.update(inventory_status=after.status.value, inventory_pid=after.pid)

    assert after.status == VMState.RUNNING
    assert after.pid == new_info.pid
    assert returned.pid == new_info.pid
    assert answers


# ---------------------------------------------------------------------------
# 5. Prune rechecks ownership before deleting
# ---------------------------------------------------------------------------


def test_prune_rechecks_ownership_before_deleting(
    live_case: LiveCase, monkeypatch: pytest.MonkeyPatch
) -> None:
    case, report = live_case, live_case.report
    retained_config = case.config.model_copy(update={"retain_disk_on_delete": True})
    first = _boot(case, retained_config)
    assert first.run("echo kept > /root/kept; sync").exit_code == 0
    first.stop()
    first.delete()
    disks = case.manager.leftover_paths_for_vm(case.name)
    disk = next(path for path in disks if path.suffix in {".qcow2", ".ext4"})
    report.facts["disk"] = str(disk)
    assert disk.exists(), "retained disk was not kept"

    gate = Gate()
    original_scan = CelestoManager.find_leftover_artifacts

    def gated_scan(self: CelestoManager) -> list[Any]:
        found = original_scan(self)
        report.event("prune_scanned", candidates=[str(item.path) for item in found])
        gate.hold_once()
        return found

    monkeypatch.setattr(CelestoManager, "find_leftover_artifacts", gated_scan)

    prune_thread, prune = _in_thread(
        lambda: case.manager.prune_leftover_artifacts(include_retained=True)
    )
    assert gate.entered.wait(GATE_TIMEOUT), "prune never finished its scan"
    scanned_disk = any(event.get("candidates") for event in report.events)
    assert scanned_disk, "prune scan did not see the retained disk"

    second = _boot(case, retained_config)
    reclaimed_marker = second.run("cat /root/kept").stdout.strip()
    report.event("recreated_from_retained_disk", marker=reclaimed_marker)

    gate.released.set()
    prune_thread.join(GATE_TIMEOUT)
    removed = [str(item.path) for item in prune.get("result", [])]
    answers = _guest_answers(second)
    report.event(
        "prune_finished",
        removed=removed,
        error=repr(prune.get("error")),
        disk_present=disk.exists(),
        guest_answers=answers,
    )
    report.facts.update(removed=removed, disk_present_after_prune=disk.exists())

    assert "error" not in prune, f"prune failed: {prune.get('error')!r}"
    assert reclaimed_marker == "kept"
    assert str(disk) not in removed
    assert disk.exists(), "prune deleted the disk a recreated computer uses"
    assert answers


# ---------------------------------------------------------------------------
# 6-8. Cancelling an async operation finishes it before releasing the lock
# ---------------------------------------------------------------------------


def _lifecycle_lock_free(manager: CelestoManager, vm_id: str) -> bool:
    """Return whether another caller could take *vm_id*'s lifecycle lock now."""
    try:
        lock = manager._acquire_operation_lock(
            manager._lifecycle_lock_name(vm_id), timeout=0, vm_id=vm_id
        )
    except CelestoError:
        return False
    manager._release_vm_create_lock(lock)
    return True


def _row(state: SQLiteStateManager, vm_id: str) -> dict[str, Any]:
    try:
        info = state.get_vm(vm_id)
    except VMNotFoundError:
        return {"exists": False}
    return {"exists": True, "status": info.status.value, "pid": info.pid}


async def _cancel_while_gated(
    case: LiveCase, gate: Gate, operation: Callable[[], Any]
) -> tuple[dict[str, Any], str]:
    """Cancel *operation* while *gate* holds its real work, then let it finish.

    Returns what another caller could see while the work was held, and how
    the cancelled call ended.
    """
    task = asyncio.ensure_future(operation())
    entered = await asyncio.to_thread(gate.entered.wait, GATE_TIMEOUT)
    assert entered, "the operation never reached its gated step"
    task.cancel()
    case.report.event("cancel_requested")
    done, _pending = await asyncio.wait({task}, timeout=BLOCKED_SECONDS)
    held = {
        "returned_before_work_finished": bool(done),
        "lock_free_while_work_runs": _lifecycle_lock_free(case.manager, case.name),
        "row_while_work_runs": _row(case.state, case.name),
    }
    case.report.event("while_work_held", **held)
    gate.released.set()
    try:
        await task
    except asyncio.CancelledError:
        ended = "cancelled"
    except Exception as exc:  # noqa: BLE001 - reported by the test
        ended = repr(exc)
    else:
        ended = "returned"
    case.report.event("cancelled_call_ended", ended=ended)
    return held, ended


def _assert_finished_before_releasing(held: dict[str, Any], ended: str) -> None:
    assert not held["returned_before_work_finished"], (
        "the cancelled call returned while its work was still running"
    )
    assert not held["lock_free_while_work_runs"], (
        "the lifecycle lock was released while the work was still running"
    )
    assert ended == "cancelled", f"the cancelled call ended with {ended}"


def _assert_starts_cleanly(case: LiveCase) -> None:
    """A fresh start boots exactly one answering guest."""
    handle = case.handle()
    handle.start(boot_timeout=BOOT_TIMEOUT)
    handle.wait_for_ready(timeout=BOOT_TIMEOUT)
    info = case.manager.get(case.name)
    guests = _runtime_processes(case.data_dir)
    answers = _guest_answers(handle)
    case.report.event(
        "started_again",
        status=info.status.value,
        pid=info.pid,
        guest_processes=len(guests),
        guest_answers=answers,
    )
    assert info.status == VMState.RUNNING
    assert _pid_alive(info.pid)
    assert len(guests) == 1, f"expected one guest process, found: {guests}"
    assert answers


def test_cancelled_async_start_stops_the_launched_guest(
    live_case: LiveCase, monkeypatch: pytest.MonkeyPatch
) -> None:
    case, report = live_case, live_case.report
    case.manager.create(case.config)
    gate = Gate()
    original_start = QemuRuntimeAdapter.start

    def gated_start(self: QemuRuntimeAdapter, vm_info: Any, **kw: Any) -> Any:
        launch = original_start(self, vm_info, **kw)
        if vm_info.vm_id == case.name:
            report.event("guest_launched", pid=launch.pid, pid_alive=_pid_alive(launch.pid))
            gate.hold_once()
        return launch

    monkeypatch.setattr(QemuRuntimeAdapter, "start", gated_start)

    held, ended = asyncio.run(
        _cancel_while_gated(
            case, gate, lambda: case.manager.async_start(case.name, boot_timeout=BOOT_TIMEOUT)
        )
    )
    after = _row(case.state, case.name)
    guests = _runtime_processes(case.data_dir)
    report.facts.update(held=held, ended=ended, row_after=after, guests_after=guests)

    _assert_finished_before_releasing(held, ended)
    assert after == {"exists": True, "status": "stopped", "pid": None}
    assert guests == [], f"cancelled start left a guest running: {guests}"
    monkeypatch.undo()
    _assert_starts_cleanly(case)


def test_cancelled_async_stop_finishes_stopping(
    live_case: LiveCase, monkeypatch: pytest.MonkeyPatch
) -> None:
    case, report = live_case, live_case.report
    _boot(case)
    gate = Gate()
    original_stop = QemuRuntimeAdapter.stop

    def gated_stop(self: QemuRuntimeAdapter, vm_info: Any, **kw: Any) -> None:
        original_stop(self, vm_info, **kw)
        if vm_info.vm_id == case.name:
            report.event("guest_stopped", pid=vm_info.pid, pid_alive=_pid_alive(vm_info.pid))
            gate.hold_once()

    monkeypatch.setattr(QemuRuntimeAdapter, "stop", gated_stop)

    held, ended = asyncio.run(
        _cancel_while_gated(case, gate, lambda: case.manager.async_stop(case.name, timeout=3.0))
    )
    after = _row(case.state, case.name)
    guests = _runtime_processes(case.data_dir)
    report.facts.update(held=held, ended=ended, row_after=after, guests_after=guests)

    _assert_finished_before_releasing(held, ended)
    assert after == {"exists": True, "status": "stopped", "pid": None}
    assert guests == []
    monkeypatch.undo()
    _assert_starts_cleanly(case)


def test_cancelled_async_delete_finishes_deleting(
    live_case: LiveCase, monkeypatch: pytest.MonkeyPatch
) -> None:
    case, report = live_case, live_case.report
    _boot(case)
    disks = [path for path in case.manager.leftover_paths_for_vm(case.name) if path.exists()]
    report.facts["disks"] = [str(path) for path in disks]
    assert disks, "the computer has no disk to delete"
    gate = Gate()
    original_cleanup = CelestoManager._cleanup_vm_artifacts

    def gated_cleanup(self: CelestoManager, vm_id: str, *args: Any, **kw: Any) -> None:
        if vm_id == case.name:
            report.event("delete_removing_files")
            gate.hold_once()
        original_cleanup(self, vm_id, *args, **kw)

    monkeypatch.setattr(CelestoManager, "_cleanup_vm_artifacts", gated_cleanup)

    held, ended = asyncio.run(
        _cancel_while_gated(case, gate, lambda: case.manager.async_delete(case.name))
    )
    after = _row(case.state, case.name)
    disks_after = [str(path) for path in disks if path.exists()]
    guests = _runtime_processes(case.data_dir)
    report.facts.update(
        held=held, ended=ended, row_after=after, disks_after=disks_after, guests_after=guests
    )

    _assert_finished_before_releasing(held, ended)
    assert after == {"exists": False}, "cancelled delete left the computer's row behind"
    assert disks_after == []
    assert guests == []


# ---------------------------------------------------------------------------
# 9. A snapshot does not revive a computer stopped while it was captured
# ---------------------------------------------------------------------------


def test_stop_during_snapshot_keeps_the_computer_stopped(
    live_case: LiveCase, monkeypatch: pytest.MonkeyPatch
) -> None:
    case, report = live_case, live_case.report
    _boot(case)
    gate = Gate()
    original_capture = QemuRuntimeAdapter.create_snapshot

    def gated_capture(self: QemuRuntimeAdapter, request: Any) -> Any:
        result = original_capture(self, request)
        if request.vm_info.vm_id == case.name:
            report.event("snapshot_captured", source_status=result.source_status.value)
            gate.hold_once()
        return result

    monkeypatch.setattr(QemuRuntimeAdapter, "create_snapshot", gated_capture)

    snapshot_thread, snapshot = _in_thread(
        lambda: case.manager.create_snapshot(
            case.name, snapshot_type=SnapshotType.DISK, resume_source=True
        )
    )
    assert gate.entered.wait(GATE_TIMEOUT), "snapshot never finished capturing"
    case.manager.stop(case.name, timeout=3.0)
    stopped = _row(case.state, case.name)
    report.event("stopped_during_snapshot", row=stopped)

    gate.released.set()
    snapshot_thread.join(GATE_TIMEOUT)
    after = _row(case.state, case.name)
    snapshots = [item.snapshot_id for item in case.manager.list_snapshots(vm_id=case.name)]
    report.event(
        "snapshot_finished",
        error=repr(snapshot.get("error")),
        row=after,
        snapshots=snapshots,
    )
    report.facts.update(row_after_stop=stopped, row_after_snapshot=after, snapshots=snapshots)

    assert stopped == {"exists": True, "status": "stopped", "pid": None}
    assert "error" not in snapshot, f"snapshot failed: {snapshot.get('error')!r}"
    assert snapshot["result"].snapshot_id in snapshots
    assert after == stopped, "the snapshot overwrote the stop that ran during it"
    monkeypatch.undo()
    _assert_starts_cleanly(case)

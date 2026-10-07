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

"""Forking a sandbox makes independent children from one saved copy.

The fork engine is internal until the public ``fork()`` lands, so these tests
drive the facade's private ``_fork_many`` / ``_async_fork_many`` on real
sandboxes:

1. A running source forks into three children. Every child boots with the
   source's files, its own instance ID, SSH host key and machine ID, and the
   saved copy (the generation) is gone afterwards. On QEMU the source keeps
   running the whole time; a heartbeat against the source measures any pause.
2. A stopped source forks into one child with an exact name (async path).
3. A taken child name, a paused source and a source with a shared folder or
   extra drive are refused before anything is paused, copied or created.

Each test writes a JSON report (per-child results, identity fingerprints,
the source's longest pause and a listing of leftover generations) to
``CELESTO_E2E_ARTIFACT_DIR`` or pytest's tmp dir.
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
import time
import uuid
from contextlib import suppress
from pathlib import Path
from typing import Any

import pytest
from _util import BOOT_TIMEOUT, E2E_BACKENDS, e2e_artifact_dir, require_e2e_backend

from celesto import Celesto
from celesto.cli._sqlite import SQLiteStateManager
from celesto.exceptions import CelestoError, VMNotFoundError
from celesto.facade import _build_auto_config
from celesto.runtime.backends import BACKEND_QEMU
from celesto.types import VMState, WorkspaceMount
from celesto.vm import CelestoManager, resolve_data_dir

pytestmark = pytest.mark.e2e

_MARKER_PATH = "/root/fork-marker"
# Longest silence allowed from a QEMU source while it is copied live; over
# ten times the gap recorded on a healthy run (see the running-source test).
_QEMU_MAX_HEARTBEAT_GAP = 1.0
# Read with the guest's own tools, independent of what Celesto records.
_GUEST_IDENTITY = (
    "printf 'instance_id=%s\\n' \"$(cat /etc/celesto/instance-id)\"; "
    "printf 'machine_id=%s\\n' \"$(cat /etc/machine-id)\"; "
    "printf 'fingerprint=%s\\n' "
    "\"$(ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub | awk '{print $2}')\"; "
    "printf 'marker_feature=%s\\n' \"$(test -e /etc/celesto/features/instance-id && echo yes)\"; "
    f"printf 'marker=%s\\n' \"$(cat {_MARKER_PATH} 2>/dev/null)\""
)


def _require_backend(backend: str, request: pytest.FixtureRequest) -> None:
    require_e2e_backend(backend, request.config, sandbox_name=f"fork-{backend}")  # type: ignore[arg-type]


def _names(label: str) -> tuple[str, str]:
    prefix = os.environ.get("CELESTO_E2E_NAME_PREFIX", "e2e-")
    suffix = uuid.uuid4().hex[:6]
    return f"{prefix}fork-{label}-{suffix}", suffix


def _artifact(tmp_path: Path, name: str) -> Path:
    return e2e_artifact_dir(tmp_path) / name


def _guest_identity(sandbox: Celesto) -> dict[str, str]:
    result = sandbox.run(_GUEST_IDENTITY)
    assert result.exit_code == 0, f"{sandbox.vm_id}: identity read failed: {result.stderr}"
    values: dict[str, str] = {}
    for line in result.stdout.splitlines():
        key, sep, value = line.partition("=")
        if sep:
            values[key] = value.strip()
    return values


def _recorded(state: SQLiteStateManager, name: str) -> dict[str, str | None] | None:
    record = state.get_vm_identity(name)
    if record is None:
        return None
    return {
        "instance_id": record.instance_id,
        "ssh_host_key_fingerprint": record.ssh_host_key_fingerprint,
        "machine_id": record.machine_id,
    }


def _leftover_generations(manager: CelestoManager, source: str) -> dict[str, list[str]]:
    """Generations of *source* still on disk or in the snapshot list."""
    on_disk = (
        sorted(path.name for path in manager.snapshot_dir.glob(f"fork-{source}-*"))
        if manager.snapshot_dir.exists()
        else []
    )
    listed = sorted(
        snapshot.snapshot_id
        for snapshot in manager.list_snapshots(vm_id=source)
        if snapshot.snapshot_id.startswith("fork-")
    )
    return {"snapshot_dir": on_disk, "snapshot_list": listed}


class _Heartbeat:
    """Runs a tiny guest command in a loop and records the longest gap.

    A paused source can't answer, so the longest gap between answers bounds
    how long the fork paused it.
    """

    def __init__(self, sandbox: Celesto) -> None:
        self._sandbox = sandbox
        self._stop = threading.Event()
        self.beats = 0
        self.longest_gap = 0.0
        self.errors: list[str] = []
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def __enter__(self) -> _Heartbeat:
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        self._thread.join(120)

    def _loop(self) -> None:
        last = time.monotonic()
        while not self._stop.is_set():
            try:
                self._sandbox.run("true", timeout=60)
            except Exception as exc:  # noqa: BLE001 - recorded in the report
                self.errors.append(str(exc))
            now = time.monotonic()
            self.longest_gap = max(self.longest_gap, now - last)
            last = now
            self.beats += 1
            time.sleep(0.05)


def _new_source(name: str, backend: str, state: SQLiteStateManager) -> tuple[Celesto, str]:
    config, ssh_key_path = _build_auto_config(vm_name=name, os="alpine", backend=backend)
    source = Celesto(config=config, ssh_key_path=ssh_key_path, state_manager=state)
    return source, ssh_key_path


def _delete_everything(manager: CelestoManager, names: list[str], source: str) -> None:
    for name in reversed(names):
        with suppress(Exception):
            manager.delete(name)
    with suppress(Exception):
        for snapshot in manager.list_snapshots(vm_id=source):
            manager.delete_snapshot(snapshot.snapshot_id)


@pytest.mark.parametrize("backend", E2E_BACKENDS, ids=str)
def test_running_source_forks_into_three_independent_children(
    backend: str, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    """Three children boot from one copy, each with its own identity."""
    _require_backend(backend, request)
    source_name, suffix = _names("run")
    marker = f"fork-marker-{suffix}"
    artifact = _artifact(tmp_path, f"fork-engine-{backend}-running.json")
    report: dict[str, Any] = {"backend": backend, "source": source_name}
    state = SQLiteStateManager(resolve_data_dir() / "celesto.db")
    manager = CelestoManager(state_manager=state)
    created: list[str] = []
    try:
        source, ssh_key_path = _new_source(source_name, backend, state)
        created.append(source_name)
        source.start(boot_timeout=BOOT_TIMEOUT)
        result = source.run(f"echo {marker} > {_MARKER_PATH}")
        assert result.exit_code == 0, result.stderr
        source_guest = _guest_identity(source)
        source_recorded = _recorded(state, source_name)
        report["source_identity"] = {"guest": source_guest, "recorded": source_recorded}
        assert source_recorded is not None, "the source's identity was never recorded"

        notices: list[str] = []
        beat_sandbox = Celesto.from_id(source_name, ssh_key_path=ssh_key_path, state_manager=state)
        with _Heartbeat(beat_sandbox) as heartbeat:
            started = time.monotonic()
            batch = source._fork_many(3, boot_timeout=BOOT_TIMEOUT, on_notice=notices.append)
            report["fork_seconds"] = round(time.monotonic() - started, 3)
        created.extend(child.name for child in batch.children)
        report["notices"] = notices
        report["source_state"] = batch.source_state.value
        report["warnings"] = list(batch.warnings)
        report["source_longest_pause_seconds"] = round(heartbeat.longest_gap, 3)
        report["heartbeats"] = heartbeat.beats
        report["heartbeat_errors"] = heartbeat.errors
        report["children"] = {}
        for child in batch.children:
            entry: dict[str, Any] = {"ok": child.ok, "error": child.error}
            if child.sandbox is not None:
                entry["config_instance_id"] = child.sandbox.info.config.instance_id
                entry["guest"] = _guest_identity(child.sandbox)
                entry["recorded"] = _recorded(state, child.name)
                lineage = state.get_vm_lineage(child.name)
                entry["forked_from"] = lineage.forked_from if lineage else None
            report["children"][child.name] = entry
        report["leftover_generations"] = _leftover_generations(manager, source_name)

        assert [child.name for child in batch.children] == [
            f"{source_name}-{index}" for index in (1, 2, 3)
        ]
        for name, entry in report["children"].items():
            assert entry["ok"], f"{name} failed: {entry['error']}"
            guest = entry["guest"]
            assert guest["marker"] == marker, f"{name} lost the source's files: {entry}"
            assert guest["marker_feature"] == "yes", f"{name}: {entry}"
            assert guest["instance_id"] == entry["config_instance_id"], f"{name}: {entry}"
            assert entry["recorded"] == {
                "instance_id": guest["instance_id"],
                "ssh_host_key_fingerprint": guest["fingerprint"],
                "machine_id": guest["machine_id"],
            }, f"{name} recorded identity: {entry}"
            assert entry["forked_from"] == source_name
        identities = [source_guest] + [entry["guest"] for entry in report["children"].values()]
        for key in ("instance_id", "fingerprint", "machine_id"):
            values = [identity[key] for identity in identities]
            assert len(set(values)) == len(values), f"{key} is shared: {values}"
        assert report["leftover_generations"] == {"snapshot_dir": [], "snapshot_list": []}
        assert batch.source_state == VMState.RUNNING
        assert batch.warnings == ()
        if backend == BACKEND_QEMU:
            assert not any(notice.startswith("Pausing") for notice in notices), notices
            assert heartbeat.errors == [], heartbeat.errors
            # Measured, not inferred from the missing notice: the source kept
            # answering throughout. Recorded runs on macOS QEMU show a longest
            # gap of 0.07 to 0.09 s (one round trip plus the 0.05 s sleep);
            # a pause for the copy lasts as long as the copy, seconds.
            assert heartbeat.beats >= 3, f"too few heartbeats to measure: {heartbeat.beats}"
            assert heartbeat.longest_gap < _QEMU_MAX_HEARTBEAT_GAP, (
                f"source stopped answering for {heartbeat.longest_gap:.3f} s during the fork"
            )
        else:
            assert f"Pausing {source_name} while its files are copied…" in notices
        report["result"] = "passed"
    except BaseException as exc:
        report["result"] = f"failed: {exc}"
        raise
    finally:
        artifact.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(f"fork engine artifact: {artifact}")
        _delete_everything(manager, created, source_name)
        manager.close()


@pytest.mark.parametrize("backend", E2E_BACKENDS, ids=str)
def test_stopped_source_forks_into_one_named_child(
    backend: str, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    """A stopped source is copied as-is; one child takes exactly the given name."""
    _require_backend(backend, request)
    source_name, suffix = _names("stop")
    child_name = f"{source_name}-exp"
    marker = f"fork-marker-{suffix}"
    artifact = _artifact(tmp_path, f"fork-engine-{backend}-stopped.json")
    report: dict[str, Any] = {"backend": backend, "source": source_name}
    state = SQLiteStateManager(resolve_data_dir() / "celesto.db")
    manager = CelestoManager(state_manager=state)
    created: list[str] = []
    try:
        source, _key = _new_source(source_name, backend, state)
        created.append(source_name)
        source.start(boot_timeout=BOOT_TIMEOUT)
        assert source.run(f"echo {marker} > {_MARKER_PATH} && sync").exit_code == 0
        source_guest = _guest_identity(source)
        source.stop()
        report["source_identity"] = source_guest

        notices: list[str] = []
        batch = asyncio.run(
            source._async_fork_many(
                1, name=child_name, boot_timeout=BOOT_TIMEOUT, on_notice=notices.append
            )
        )
        created.extend(child.name for child in batch.children)
        report["notices"] = notices
        report["source_state"] = batch.source_state.value
        (child,) = batch.children
        report["child"] = {"name": child.name, "ok": child.ok, "error": child.error}
        assert child.ok, child.error
        assert child.name == child_name
        assert child.sandbox is not None
        child_guest = _guest_identity(child.sandbox)
        report["child"]["guest"] = child_guest
        report["child"]["recorded"] = _recorded(state, child_name)
        report["leftover_generations"] = _leftover_generations(manager, source_name)

        assert child_guest["marker"] == marker
        assert child_guest["instance_id"] == child.sandbox.info.config.instance_id
        for key in ("instance_id", "fingerprint", "machine_id"):
            assert child_guest[key] != source_guest[key], f"{key} is shared"
        assert batch.source_state == VMState.STOPPED
        assert state.get_vm(source_name).status == VMState.STOPPED
        assert notices == [], notices
        assert report["leftover_generations"] == {"snapshot_dir": [], "snapshot_list": []}
        report["result"] = "passed"
    except BaseException as exc:
        report["result"] = f"failed: {exc}"
        raise
    finally:
        artifact.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(f"fork engine artifact: {artifact}")
        _delete_everything(manager, created, source_name)
        manager.close()


@pytest.mark.parametrize("backend", E2E_BACKENDS, ids=str)
def test_forks_that_cannot_work_are_refused_before_anything_is_copied(
    backend: str, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    """A taken name, a paused source and a shared folder stop the fork up front."""
    _require_backend(backend, request)
    source_name, suffix = _names("refuse")
    taken = f"{source_name}-exp-2"
    artifact = _artifact(tmp_path, f"fork-engine-{backend}-refusals.json")
    report: dict[str, Any] = {"backend": backend, "source": source_name, "cases": {}}
    state = SQLiteStateManager(resolve_data_dir() / "celesto.db")
    manager = CelestoManager(state_manager=state)
    created: list[str] = []

    def everything() -> dict[str, Any]:
        return {
            "sandboxes": sorted(vm.vm_id for vm in state.list_vms()),
            "generations": _leftover_generations(manager, source_name),
        }

    try:
        source, _key = _new_source(source_name, backend, state)
        created.append(source_name)
        source.start(boot_timeout=BOOT_TIMEOUT)
        assert source.run("true").exit_code == 0
        config, _key = _build_auto_config(vm_name=taken, os="alpine", backend=backend)
        manager.create(config)
        created.append(taken)

        # One of three requested names is taken: nothing is paused or copied.
        before = everything()
        notices: list[str] = []
        with pytest.raises(CelestoError) as caught:
            source._fork_many(
                3, name=f"{source_name}-exp", boot_timeout=BOOT_TIMEOUT, on_notice=notices.append
            )
        report["cases"]["name-taken"] = {"error": str(caught.value), "notices": notices}
        assert str(caught.value) == (
            f"A sandbox named '{taken}' already exists. Choose another name with '--name', "
            f"or run 'celesto sandbox delete {taken}'."
        )
        assert notices == []
        assert everything() == before
        assert state.get_vm(source_name).status == VMState.RUNNING

        # A paused source.
        source.pause()
        with pytest.raises(CelestoError) as caught:
            source._fork_many(1, boot_timeout=BOOT_TIMEOUT)
        report["cases"]["paused"] = {"error": str(caught.value)}
        assert str(caught.value) == (
            f"Sandbox '{source_name}' is paused. Run 'celesto sandbox resume {source_name}', "
            "then fork again."
        )
        assert everything() == before
        assert state.get_vm(source_name).status == VMState.PAUSED
        with pytest.raises(VMNotFoundError):
            state.get_vm(f"{source_name}-1")

        # A shared folder (QEMU) or extra drive (Firecracker has no shared folders).
        shared_name = f"{source_name}-shared"
        config, _key = _build_auto_config(vm_name=shared_name, os="alpine", backend=backend)
        if backend == BACKEND_QEMU:
            folder = tmp_path / "shared-folder"
            folder.mkdir()
            update: dict[str, Any] = {"workspace_mounts": [WorkspaceMount(host_path=folder)]}
        else:
            drive = tmp_path / "extra-drive.img"
            drive.write_bytes(b"\0" * 4096)
            update = {"extra_drives": [drive]}
        shared = Celesto(config=config.model_copy(update=update), state_manager=state)
        created.append(shared_name)
        before = everything()
        with pytest.raises(CelestoError) as caught:
            shared._fork_many(1, boot_timeout=BOOT_TIMEOUT)
        report["cases"]["shared-folder"] = {"error": str(caught.value)}
        assert str(caught.value) == (
            f"Sandbox '{shared_name}' uses a shared folder or extra drive, which forks can't "
            f"copy. Run 'celesto sandbox create --name {shared_name}-copy' without --mount, "
            f"then run 'celesto sandbox fork {shared_name}-copy'."
        )
        assert everything() == before
        report["result"] = "passed"
    except BaseException as exc:
        report["result"] = f"failed: {exc}"
        raise
    finally:
        artifact.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(f"fork engine artifact: {artifact}")
        _delete_everything(manager, created, source_name)
        manager.close()


@pytest.mark.parametrize("backend", E2E_BACKENDS, ids=str)
def test_forks_started_together_get_their_own_names(
    backend: str, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    """Two forks of one source at once: the second continues the numbering."""
    _require_backend(backend, request)
    source_name, _suffix = _names("both")
    artifact = _artifact(tmp_path, f"fork-engine-{backend}-concurrent.json")
    report: dict[str, Any] = {"backend": backend, "source": source_name}
    state = SQLiteStateManager(resolve_data_dir() / "celesto.db")
    manager = CelestoManager(state_manager=state)
    created: list[str] = []
    try:
        source, ssh_key_path = _new_source(source_name, backend, state)
        created.append(source_name)
        source.start(boot_timeout=BOOT_TIMEOUT)
        assert source.run("true").exit_code == 0

        start = threading.Barrier(2)
        outcomes: list[Any] = []
        notices: list[str] = []

        def fork() -> None:
            handle = Celesto.from_id(source_name, ssh_key_path=ssh_key_path, state_manager=state)
            start.wait()
            try:
                outcomes.append(
                    handle._fork_many(2, boot_timeout=BOOT_TIMEOUT, on_notice=notices.append)
                )
            except Exception as exc:  # noqa: BLE001 - reported below
                outcomes.append(exc)

        threads = [threading.Thread(target=fork) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(900)
        batches = [outcome for outcome in outcomes if not isinstance(outcome, Exception)]
        for batch in batches:
            created.extend(child.name for child in batch.children)
        report["outcomes"] = [
            [{"name": c.name, "ok": c.ok, "error": c.error} for c in outcome.children]
            if not isinstance(outcome, Exception)
            else f"raised: {outcome}"
            for outcome in outcomes
        ]
        report["notices"] = notices
        report["leftover_generations"] = _leftover_generations(manager, source_name)

        assert len(batches) == 2, report["outcomes"]
        names = sorted(([c.name for c in batch.children] for batch in batches), key=str)
        assert names == [
            [f"{source_name}-1", f"{source_name}-2"],
            [f"{source_name}-3", f"{source_name}-4"],
        ], report["outcomes"]
        assert all(c.ok for batch in batches for c in batch.children), report["outcomes"]
        # The fork that waited said so, once; the other one didn't wait.
        waiting = [
            n for n in notices if n.startswith("Waiting for the current snapshot or fork of")
        ]
        assert len(waiting) == 1, notices
        assert source_name in waiting[0], notices
        if backend == BACKEND_QEMU:
            assert notices == waiting, notices
        assert report["leftover_generations"] == {"snapshot_dir": [], "snapshot_list": []}
        report["result"] = "passed"
    except BaseException as exc:
        report["result"] = f"failed: {exc}"
        raise
    finally:
        artifact.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(f"fork engine artifact: {artifact}")
        _delete_everything(manager, created, source_name)
        manager.close()

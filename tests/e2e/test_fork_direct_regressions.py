"""Direct fork regressions through real SDK, disk and guest operations.

Designed before repair: start (sync/async) must wait for stopped-source capture;
invalid counts must fail before capture; a failed cleanup must preserve the
child's failure reason and give a truthful, executable recovery command;
cancelled async startup must retain protection until bookkeeping finishes.
Timing gates force race order; no hypervisor or disk operation is simulated.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import tempfile
import threading
import uuid
from collections.abc import Iterator
from contextlib import suppress
from pathlib import Path
from typing import Any

import pytest
from _util import BOOT_TIMEOUT, E2E_BACKENDS, e2e_artifact_dir, require_e2e_backend

from celesto import Celesto, ForkBatch, ForkResult
from celesto.cli._sqlite import SQLiteStateManager
from celesto.facade import _build_auto_config, _ForkIdentityError
from celesto.runtime.base import RuntimeLaunch
from celesto.types import SnapshotInfo, VMInfo, VMState
from celesto.vm import CelestoManager

pytestmark = pytest.mark.e2e
_LiveCase = tuple[Celesto, CelestoManager, dict[str, Any], dict[str, Any]]


@pytest.fixture
def live_case(backend: str, request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[_LiveCase]:
    require_e2e_backend(backend, request.config, sandbox_name="fork-regression")
    name = f"e2e-fork-reg-{uuid.uuid4().hex[:8]}"
    data = tmp_path / "data"
    data.mkdir()
    # UNIX socket paths must remain short on macOS regardless of pytest's cwd.
    sockets = Path(tempfile.mkdtemp(prefix="fc-reg-", dir="/tmp"))
    state = SQLiteStateManager(data / "celesto.db")
    manager = CelestoManager(data_dir=data, socket_dir=sockets, state_manager=state)
    local_manifest = os.environ.get("CELESTO_FORK_REGRESSION_MANIFEST")
    if local_manifest and backend == "qemu":
        manifest_path = Path(local_manifest)
        manifest = json.loads(manifest_path.read_text())
        image_state = SQLiteStateManager(Path(manifest["data_dir"]) / "celesto.db")
        config = manager._config_for_disk_copy(image_state.get_vm(manifest["name"]), name)
        config = config.model_copy(
            update={
                "rootfs_path": manifest_path.parent
                / "images"
                / f"pr627-alpine-{manifest_path.parent.name}"
                / "rootfs.ext4",
                "rootfs_format": "raw-ext4",
                "grow_filesystem": False,
                "disk_size_mib": 512,
            }
        )
        ssh_key = manifest["ssh_key"]
        image_state.close()
    else:
        config, ssh_key = _build_auto_config(vm_name=name, os="alpine", backend=backend)
    kwargs = {
        "data_dir": data,
        "socket_dir": sockets,
        "state_manager": state,
        "ssh_key_path": ssh_key,
    }
    source = Celesto(config=config, **kwargs)
    report: dict[str, Any] = {"backend": backend, "source": name}
    try:
        source.start(boot_timeout=BOOT_TIMEOUT)
        source.wait_for_ready(timeout=BOOT_TIMEOUT)
        assert (
            source.run("printf 'before-start\\n' > /root/fork-direct-marker; sync").exit_code == 0
        )
        source.stop()
        yield source, manager, kwargs, report
    finally:
        artifact = e2e_artifact_dir(tmp_path) / f"{request.node.name}-{name}.json"
        artifact.write_text(json.dumps(report, indent=2, default=str) + "\n")
        for info in reversed(state.list_vms()):
            with suppress(Exception):
                manager.delete(info.vm_id)
        for snapshot in manager.list_snapshots():
            with suppress(Exception):
                manager.delete_snapshot(snapshot.snapshot_id)
        source.close()
        manager.close()
        state.close()
        with suppress(OSError):
            sockets.rmdir()


@pytest.mark.parametrize("backend", E2E_BACKENDS)
@pytest.mark.parametrize("use_async", [False, True], ids=["sync-start", "async-start"])
def test_start_waits_for_stopped_source_fork_capture(
    live_case: _LiveCase, monkeypatch: pytest.MonkeyPatch, use_async: bool
) -> None:
    source, manager, kwargs, report = live_case
    entered, release = threading.Event(), threading.Event()
    start_requested, started = threading.Event(), threading.Event()
    original_capture = CelestoManager._capture_stopped_disk
    errors: dict[str, str] = {}
    batches: list[ForkBatch] = []
    starter = Celesto.from_id(source.vm_id, **kwargs)

    def gated_capture(self: CelestoManager, info: VMInfo, *args: Any, **kw: Any) -> SnapshotInfo:
        if info.vm_id == source.vm_id:
            entered.set()
            if not release.wait(30):
                raise TimeoutError("fork capture gate not released")
        return original_capture(self, info, *args, **kw)

    monkeypatch.setattr(CelestoManager, "_capture_stopped_disk", gated_capture)

    def fork() -> None:
        try:
            batches.append(
                source.fork_many(1, name=f"{source.vm_id}-child", boot_timeout=BOOT_TIMEOUT)
            )
        except BaseException as exc:
            errors["fork"] = repr(exc)

    def start() -> None:
        start_requested.set()
        try:
            if use_async:
                asyncio.run(starter.async_start(boot_timeout=BOOT_TIMEOUT))
            else:
                starter.start(boot_timeout=BOOT_TIMEOUT)
            started.set()
        except BaseException as exc:
            errors["start"] = repr(exc)

    copying = threading.Thread(target=fork, daemon=True)
    starting = threading.Thread(target=start, daemon=True)
    copying.start()
    try:
        assert entered.wait(30), errors
        starting.start()
        assert start_requested.wait(5)
        during_capture = started.wait(1)
        report["start_completed_during_capture"] = during_capture
    finally:
        release.set()
        copying.join(BOOT_TIMEOUT + 30)
        if starting.ident is not None:
            starting.join(BOOT_TIMEOUT + 30)
        starter.close()
    report["errors"] = errors
    assert not copying.is_alive() and not starting.is_alive(), "owned worker did not finish"
    assert not during_capture, "source started while fork held its capture lock"
    assert not errors, errors
    assert started.is_set()
    assert manager.get(source.vm_id).status == VMState.RUNNING
    child = batches[0].children[0]
    assert child.ok, child.error
    assert child.sandbox is not None
    try:
        result = child.sandbox.run("cat /root/fork-direct-marker")
        report["child_marker"] = result.stdout.strip()
        assert result.exit_code == 0 and result.stdout.strip() == "before-start"
    finally:
        child.sandbox.close()


@pytest.mark.parametrize("backend", E2E_BACKENDS)
@pytest.mark.parametrize("use_async", [False, True], ids=["sync-fork", "async-fork"])
def test_fork_rejects_non_integer_counts_before_capture(
    live_case: _LiveCase, monkeypatch: pytest.MonkeyPatch, use_async: bool
) -> None:
    source, manager, _kwargs, report = live_case
    captured: list[str] = []
    original = CelestoManager._capture_fork_generation

    def count_capture(self: CelestoManager, *args: Any, **kwargs: Any) -> SnapshotInfo:
        captured.append(args[0])
        return original(self, *args, **kwargs)

    monkeypatch.setattr(CelestoManager, "_capture_fork_generation", count_capture)
    observations: list[dict[str, Any]] = []
    invalid_counts: list[Any] = [1.5, True, False, "2", None, float("nan"), float("inf")]
    for index, count in enumerate(invalid_counts):
        child_name = f"{source.vm_id}-invalid-{index}"
        try:
            if use_async:
                batch = asyncio.run(source.async_fork_many(count, name=child_name))
            else:
                batch = source.fork_many(count, name=child_name)
        except Exception as exc:
            observations.append(
                {"input": repr(count), "error_type": type(exc).__name__, "error": str(exc)}
            )
        else:
            observations.append(
                {"input": repr(count), "created": [child.name for child in batch.children]}
            )
            for child in batch.children:
                if child.sandbox is not None:
                    child.sandbox.close()
    report.update(invalid_counts=observations, captures_before_valid_request=len(captured))
    assert all(
        item.get("error_type") == "ValueError" and "whole number" in item["error"]
        for item in observations
    ), observations
    assert captured == [], "invalid count reached source capture"
    assert [info.vm_id for info in manager.list_vms()] == [source.vm_id]
    batch = asyncio.run(source.async_fork_many(1)) if use_async else source.fork_many(1)
    child = batch.children[0]
    assert child.ok, child.error
    assert child.sandbox is not None
    try:
        result = child.sandbox.run("cat /root/fork-direct-marker")
        report["valid_count_child_marker"] = result.stdout.strip()
        assert result.exit_code == 0 and result.stdout.strip() == "before-start"
    finally:
        child.sandbox.close()


@pytest.mark.parametrize("backend", E2E_BACKENDS)
@pytest.mark.parametrize("use_async", [False, True], ids=["sync-fork", "async-fork"])
@pytest.mark.parametrize("failure", ["identity", "timeout", "unexpected"])
def test_failed_child_cleanup_reports_manual_recovery(
    live_case: _LiveCase, monkeypatch: pytest.MonkeyPatch, use_async: bool, failure: str
) -> None:
    source, manager, kwargs, report = live_case
    child_name = f"{source.vm_id}-failed"
    original_confirm = Celesto._confirm_fork_child
    original_delete = CelestoManager._delete_unlocked
    denied = True

    def fail_after_real_boot(
        self: Celesto, plan: Any, child: Celesto, deadline: float
    ) -> ForkResult:
        result = original_confirm(self, plan, child, deadline)
        if child.vm_id == child_name:
            report["child_pid_before_injected_failure"] = child.info.pid
            if failure == "identity":
                raise _ForkIdentityError("injected verification failure after real boot")
            if failure == "timeout":
                raise TimeoutError("injected readiness timeout after real boot")
            raise RuntimeError("injected child failure after real boot")
        return result

    def deny_child_cleanup(self: CelestoManager, vm_id: str) -> None:
        if vm_id == child_name and denied:
            raise PermissionError("injected cleanup denial for this test's child")
        return original_delete(self, vm_id)

    monkeypatch.setattr(Celesto, "_confirm_fork_child", fail_after_real_boot)
    monkeypatch.setattr(CelestoManager, "_delete_unlocked", deny_child_cleanup)
    child_handle: Celesto | None = None
    try:
        if use_async:
            batch = asyncio.run(
                source.async_fork_many(1, name=child_name, boot_timeout=BOOT_TIMEOUT)
            )
        else:
            batch = source.fork_many(1, name=child_name, boot_timeout=BOOT_TIMEOUT)
        failed = batch.children[0]
        assert not failed.ok and failed.error is not None
        child_handle = Celesto.from_id(child_name, **kwargs)
        result = child_handle.run("printf 'real-child-still-running\\n'")
        report.update(
            failure=failure,
            error=failed.error,
            guest_stdout=result.stdout.strip(),
            retained_child_pid=manager.get(child_name).pid,
        )
        assert result.exit_code == 0 and result.stdout.strip() == "real-child-still-running"
        reason = {
            "identity": "couldn't confirm",
            "timeout": "didn't start within",
            "unexpected": "couldn't be created",
        }[failure]
        assert reason in failed.error
        assert "was removed" not in failed.error, failed.error
        assert "couldn't finish removing" in failed.error, failed.error
        assert f"celesto sandbox delete {child_name}" in failed.error
        denied = False
        env = dict(os.environ, CELESTO_DATA_DIR=str(manager.data_dir))
        recovery = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; from celesto.cli.main import main; sys.exit(main())",
                "sandbox",
                "delete",
                child_name,
                "--json",
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        report["recovery"] = {
            "exit_code": recovery.returncode,
            "stdout": recovery.stdout,
            "stderr": recovery.stderr,
        }
        assert recovery.returncode == 0, recovery.stderr or recovery.stdout
        assert json.loads(recovery.stdout)["ok"] is True
        assert [info.vm_id for info in manager.list_vms()] == [source.vm_id]
    finally:
        denied = False
        monkeypatch.setattr(CelestoManager, "_delete_unlocked", original_delete)
        if child_handle is not None:
            child_handle.close()


@pytest.mark.parametrize("backend", E2E_BACKENDS)
def test_cancelled_start_holds_protection_until_stop_can_see_launch(
    live_case: _LiveCase, monkeypatch: pytest.MonkeyPatch
) -> None:
    source, manager, _kwargs, report = live_case
    backend = manager.get(source.vm_id).config.backend
    assert backend is not None
    adapter_type = type(manager._runtime_adapter_for_backend(backend))
    original = adapter_type.async_start
    launches: list[RuntimeLaunch] = []

    async def scenario() -> dict[str, Any]:
        entered, release = asyncio.Event(), asyncio.Event()

        async def gated_start(self: Any, info: VMInfo, **kwargs: Any) -> RuntimeLaunch:
            launch = await original(self, info, **kwargs)
            launches.append(launch)
            entered.set()
            await release.wait()
            return launch

        monkeypatch.setattr(adapter_type, "async_start", gated_start)
        starting = asyncio.create_task(source.async_start(boot_timeout=BOOT_TIMEOUT))
        stopping = None
        try:
            await asyncio.wait_for(entered.wait(), timeout=BOOT_TIMEOUT)
            starting.cancel()
            stopping = asyncio.create_task(manager.async_stop(source.vm_id))
            # Deliver cancellation and the stop request while the gate is held.
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            early_start = starting.done()
            early_stop = stopping.done()
        finally:
            release.set()
            with suppress(asyncio.CancelledError):
                await starting
            if stopping is not None:
                await stopping
        info = manager.get(source.vm_id)
        return {
            "cancel_completed_before_launch_bookkeeping": early_start,
            "stop_completed_before_launch_bookkeeping": early_stop,
            "state_after_stop": info.status.value,
            "pid_after_stop": info.pid,
            "runtime_alive_after_stop": manager._is_process_running(launches[0].pid),
        }

    try:
        observed = asyncio.run(scenario())
        report.update(observed)
        assert not observed["cancel_completed_before_launch_bookkeeping"], observed
        assert not observed["stop_completed_before_launch_bookkeeping"], observed
        assert observed["state_after_stop"] == "stopped" and observed["pid_after_stop"] is None
        assert not observed["runtime_alive_after_stop"], observed
    finally:
        # The failing baseline loses the PID. Recover only our own known launch
        # for fixture teardown, after preserving its observed failure evidence.
        if launches and manager._is_process_running(launches[0].pid):
            manager.state.update_vm(
                source.vm_id,
                status=VMState.RUNNING,
                pid=launches[0].pid,
                control_socket_path=launches[0].control_socket_path,
            )

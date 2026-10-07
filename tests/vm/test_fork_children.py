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

"""Fork when one child fails midway, and when QEMU can't copy live.

``tests/e2e/test_fork_engine.py`` proves forks on real sandboxes, where every
child boots and every live copy works. These tests force what a real run
can't: a child that doesn't start in time or reports the wrong identity, and
a QEMU live copy that fails. Failure modes, written before the code:

1. A child that fails is left behind instead of being removed.
2. One child failing cancels or fails the other children.
3. The generation (the saved copy) is left behind after a child fails, or
   is deleted before every child has been attempted.
4. A failed child's result doesn't name the child and the reason (with the
   actual boot timeout).
5. A child whose machine ID, or whose SSH host key, matches the source's
   recorded identity passes the check.
6. A child reporting an instance ID other than its own passes the check.
7. A failed QEMU live copy falls back to pausing the source, or creates
   children anyway, instead of failing with the live-copy message.
8. Two forks of one source started together pick their child names before
   either child exists, so the second fork's children all collide with the
   first's instead of continuing the numbering.
9. A third fork still sees the first two forks' names as free while their
   children are being copied.
10. When two forks ask for the same explicit name, the second fails child by
    child (or copies the source) instead of refusing the whole fork up front.
11. A stopped QEMU source with a raw disk is started while the fork waits for
    the lock, and the fork copies it live anyway, so every child gets a disk
    in the wrong format, instead of refusing before anything is copied.

The sandbox's disk copy, hypervisor start and guest agent are replaced at
their boundaries; the fork's checks, lock, generation and cleanup are real.
"""

from __future__ import annotations

import asyncio
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from celesto.comm.rust_http_vsock_channel import RustHttpVsockChannel
from celesto.exceptions import CelestoError, OperationTimeoutError
from celesto.facade import Celesto
from celesto.guest_identity import ssh_host_key_fingerprint
from celesto.storage._memory import MemoryStateManager
from celesto.types import (
    CommandResult,
    GuestOS,
    NetworkConfig,
    SnapshotCapturePolicy,
    VMConfig,
    VMIdentity,
    VMInfo,
    VMState,
    VsockConfig,
    generate_instance_id,
)
from celesto.vm import CelestoManager

_SOURCE = "src"
_SOURCE_KEY = (
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBxbQZ0ZKgVf2Lw4GJqRCGJw7uYXq1mIuKyhCqzQZ0vV root@celesto"
)
_SOURCE_FINGERPRINT = ssh_host_key_fingerprint(_SOURCE_KEY)
_SOURCE_MACHINE_ID = "11111111111111111111111111111111"


class _World:
    """Fake disk copies, starts and guests for one test."""

    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path
        self.state = MemoryStateManager(tmp_path / "data")
        self.manager = CelestoManager(data_dir=tmp_path / "data", state_manager=self.state)
        self.next_cid = 100
        # Per child: "ok", "timeout", "same-machine-id", "same-host-key", "wrong-instance".
        self.behavior: dict[str, str] = {}
        self.created: list[str] = []
        self.deleted: list[str] = []
        self.generation_seen: dict[str, bool] = {}
        self.capture_policies: list[SnapshotCapturePolicy] = []
        self.live_copy_error: Exception | None = None
        self.copy_seconds = 0.0

    # -- sandbox rows ---------------------------------------------------

    def config(self, name: str, backend: str, **update: Any) -> VMConfig:
        kernel = self.tmp_path / "vmlinux"
        kernel.touch()
        suffix = ".ext4" if backend == "firecracker" else ".qcow2"
        disk = self.manager.disk_dir / f"{name}{suffix}"
        disk.parent.mkdir(parents=True, exist_ok=True)
        if not disk.exists():
            disk.write_bytes(b"disk" * 1024)
        self.next_cid += 1
        vsock = VsockConfig(
            guest_cid=self.next_cid,
            uds_path=str(self.tmp_path / f"{name}.vsock") if backend == "firecracker" else None,
        )
        values: dict[str, Any] = {
            "vm_id": name,
            "kernel_path": kernel,
            "rootfs_path": disk,
            "backend": backend,
            "guest_os": GuestOS.ALPINE,
            "boot_args": "console=ttyS0 reboot=k panic=1 init=/init",
            "comm_channel": "vsock",
            "vsock": vsock,
            "instance_id": generate_instance_id(),
        }
        values.update(update)
        return VMConfig.model_validate(values, context={"validate_paths": False})

    def add_source(self, backend: str, status: VMState) -> Celesto:
        config = self.config(_SOURCE, backend)
        self.state.create_vm(config)
        self.state.update_vm(
            _SOURCE,
            status=status,
            network=NetworkConfig(
                guest_ip="172.16.0.2",
                gateway_ip="172.16.0.1",
                netmask="255.255.255.252",
                tap_device="tap-src",
                guest_mac="06:00:ac:10:00:02",
            ),
        )
        self.state.record_vm_identity(
            _SOURCE,
            VMIdentity(
                instance_id=config.instance_id,
                ssh_host_key_fingerprint=_SOURCE_FINGERPRINT,
                machine_id=_SOURCE_MACHINE_ID,
            ),
        )
        return Celesto.from_id(_SOURCE, state_manager=self.state, data_dir=self.manager.data_dir)

    # -- boundaries -----------------------------------------------------

    def create_from_disk(self, source: VMInfo, disk_path: Path, name: str, **_: Any) -> VMInfo:
        self.generation_seen[name] = disk_path.is_file()
        # A slow copy keeps the race window open for concurrent forks.
        time.sleep(self.copy_seconds)
        config = self.config(name, source.config.backend or "firecracker")
        self.state.create_vm(config)
        self.created.append(name)
        return self.state.get_vm(name)

    def start(self, vm_id: str, boot_timeout: float = 30.0) -> VMInfo:
        if self.behavior.get(vm_id) == "timeout":
            raise OperationTimeoutError(f"sandbox {vm_id} did not boot", {"vm_id": vm_id})
        return self.state.update_vm(vm_id, status=VMState.RUNNING)

    def delete(self, vm_id: str) -> None:
        self.deleted.append(vm_id)
        self.state.delete_vm(vm_id)

    def guest_output(self, vm_id: str) -> str:
        info = self.state.get_vm(vm_id)
        behavior = self.behavior.get(vm_id, "ok")
        instance_id = info.config.instance_id
        if behavior == "wrong-instance":
            instance_id = generate_instance_id()
        machine_id = _SOURCE_MACHINE_ID if behavior == "same-machine-id" else f"{vm_id:0>32}"[-32:]
        # Each child gets its own host key unless it should repeat the source's.
        host_key = _SOURCE_KEY if behavior == "same-host-key" else _SOURCE_KEY.replace("Bx", "Cx")
        return (
            "supports_instance_id=1\n"
            f"instance_id={instance_id}\n"
            f"machine_id={machine_id}\n"
            f"host_key={host_key}\n"
        )

    def capture(self, *args: Any, capture_policy: SnapshotCapturePolicy, **kwargs: Any) -> Any:
        self.capture_policies.append(capture_policy)
        if capture_policy == SnapshotCapturePolicy.LIVE_ONLY and self.live_copy_error:
            raise self.live_copy_error
        raise AssertionError(f"unexpected capture with {capture_policy}")

    def generations(self) -> list[str]:
        root = self.manager.snapshot_dir
        on_disk = sorted(p.name for p in root.glob("fork-*")) if root.exists() else []
        listed = sorted(s.snapshot_id for s in self.manager.list_snapshots(vm_id=_SOURCE))
        return on_disk + listed


@pytest.fixture
def world(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> _World:
    w = _World(tmp_path)
    monkeypatch.setattr(
        CelestoManager, "_create_from_disk", lambda self, *a, **k: w.create_from_disk(*a, **k)
    )

    async def async_create_from_disk(self, *a: Any, **k: Any) -> VMInfo:  # noqa: ANN001
        return w.create_from_disk(*a, **k)

    monkeypatch.setattr(CelestoManager, "_async_create_from_disk", async_create_from_disk)
    monkeypatch.setattr(
        CelestoManager, "start", lambda self, vm_id, boot_timeout=30.0: w.start(vm_id)
    )

    async def async_start(self, vm_id: str, boot_timeout: float = 30.0) -> VMInfo:  # noqa: ANN001
        return w.start(vm_id)

    monkeypatch.setattr(CelestoManager, "async_start", async_start)
    monkeypatch.setattr(CelestoManager, "_delete_unlocked", lambda self, vm_id: w.delete(vm_id))
    monkeypatch.setattr(
        CelestoManager, "_create_snapshot_locked", lambda self, *a, **k: w.capture(*a, **k)
    )
    monkeypatch.setattr("celesto.comm.select.host_supports_vsock", lambda: True)
    # Firecracker's vsock bridge exists only on Linux hosts.
    monkeypatch.setattr("celesto.comm.select.platform", SimpleNamespace(system=lambda: "Linux"))
    monkeypatch.setattr(
        RustHttpVsockChannel, "wait_ready", lambda self, timeout=60.0, interval=0.1: None
    )
    monkeypatch.setattr(RustHttpVsockChannel, "sync", lambda self, timeout=10: None)
    monkeypatch.setattr(
        RustHttpVsockChannel,
        "run",
        lambda self, command, timeout=30, shell="login": CommandResult(
            exit_code=0, stdout=w.guest_output(self.sandbox_name), stderr=""
        ),
    )
    return w


def _by_name(batch: Any) -> dict[str, Any]:
    return {child.name: child for child in batch.children}


@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
def test_a_child_that_does_not_start_is_removed_and_the_others_finish(
    world: _World, use_async: bool
) -> None:
    source = world.add_source("firecracker", VMState.STOPPED)
    world.behavior["src-2"] = "timeout"

    if use_async:
        batch = asyncio.run(source._async_fork_many(3, parallel=2, boot_timeout=45))
    else:
        batch = source._fork_many(3, parallel=2, boot_timeout=45)

    children = _by_name(batch)
    assert list(children) == ["src-1", "src-2", "src-3"]
    assert children["src-1"].ok and children["src-3"].ok
    failed = children["src-2"]
    assert not failed.ok
    assert failed.sandbox is None
    assert failed.error == (
        "Sandbox 'src-2' didn't start within 45 seconds and was removed. "
        "Run the fork again with '--boot-timeout 90'."
    )
    assert world.deleted == ["src-2"]
    assert sorted(vm.vm_id for vm in world.state.list_vms()) == ["src", "src-1", "src-3"]
    # Every child copied from the generation; it is gone afterwards.
    assert world.generation_seen == {"src-1": True, "src-2": True, "src-3": True}
    assert world.generations() == []
    assert batch.source_state == VMState.STOPPED
    assert batch.warnings == ()
    # A stopped source is copied as it is: no live copy and no pause.
    assert world.capture_policies == []
    for name in ("src-1", "src-3"):
        recorded = world.state.get_vm_identity(name)
        assert recorded is not None
        assert recorded.instance_id == world.state.get_vm(name).config.instance_id


@pytest.mark.parametrize("behavior", ["same-machine-id", "same-host-key", "wrong-instance"])
def test_a_child_that_cannot_prove_its_own_identity_is_removed(
    world: _World, behavior: str
) -> None:
    source = world.add_source("firecracker", VMState.STOPPED)
    world.behavior["src-1"] = behavior

    batch = source._fork_many(2, boot_timeout=30)

    children = _by_name(batch)
    assert not children["src-1"].ok
    assert children["src-1"].error == (
        "Sandbox 'src-1' couldn't confirm it has its own identity and was removed. "
        "Run the fork again."
    )
    assert children["src-2"].ok
    assert world.deleted == ["src-1"]
    assert world.generations() == []


def test_a_failed_qemu_live_copy_fails_the_fork_without_pausing(world: _World) -> None:
    source = world.add_source("qemu", VMState.RUNNING)
    world.live_copy_error = CelestoError("This machine cannot keep the sandbox available")

    with pytest.raises(CelestoError) as caught:
        source._fork_many(2, boot_timeout=30)

    assert str(caught.value) == (
        "Sandbox 'src' couldn't be copied while running. "
        "Run 'celesto sandbox stop src', then fork again."
    )
    assert world.capture_policies == [SnapshotCapturePolicy.LIVE_ONLY]
    assert world.created == []
    assert world.generations() == []
    assert world.state.get_vm(_SOURCE).status == VMState.RUNNING


def _names_of(batch: Any) -> list[str]:
    assert all(child.ok for child in batch.children), batch.children
    return [child.name for child in batch.children]


def test_forks_started_together_continue_the_numbering(world: _World) -> None:
    world.add_source("firecracker", VMState.STOPPED)
    world.copy_seconds = 0.2
    start = threading.Barrier(3)
    batches: list[Any] = []
    errors: list[BaseException] = []

    def fork() -> None:
        handle = Celesto.from_id(
            _SOURCE, state_manager=world.state, data_dir=world.manager.data_dir
        )
        start.wait()
        try:
            batches.append(handle._fork_many(2, boot_timeout=30))
        except BaseException as exc:  # noqa: BLE001 - reported below
            errors.append(exc)

    threads = [threading.Thread(target=fork) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(30)

    assert errors == []
    names = sorted((_names_of(batch) for batch in batches), key=lambda names: names[0])
    assert names == [["src-1", "src-2"], ["src-3", "src-4"], ["src-5", "src-6"]]
    assert world.generations() == []


def test_async_forks_started_together_continue_the_numbering(world: _World) -> None:
    world.add_source("firecracker", VMState.STOPPED)
    world.copy_seconds = 0.2

    async def both() -> list[Any]:
        handles = [
            Celesto.from_id(_SOURCE, state_manager=world.state, data_dir=world.manager.data_dir)
            for _ in range(2)
        ]
        return await asyncio.gather(*(h._async_fork_many(2, boot_timeout=30) for h in handles))

    batches = asyncio.run(both())

    names = sorted((_names_of(batch) for batch in batches), key=lambda names: names[0])
    assert names == [["src-1", "src-2"], ["src-3", "src-4"]]
    assert world.generations() == []


@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
def test_a_name_taken_while_waiting_refuses_the_whole_fork(world: _World, use_async: bool) -> None:
    world.add_source("firecracker", VMState.STOPPED)
    world.copy_seconds = 0.2

    async def both() -> list[Any]:
        handles = [
            Celesto.from_id(_SOURCE, state_manager=world.state, data_dir=world.manager.data_dir)
            for _ in range(2)
        ]
        return await asyncio.gather(
            *(h._async_fork_many(2, name="exp", boot_timeout=30) for h in handles),
            return_exceptions=True,
        )

    if use_async:
        outcomes = asyncio.run(both())
    else:
        outcomes = []
        start = threading.Barrier(2)

        def fork() -> None:
            handle = Celesto.from_id(
                _SOURCE, state_manager=world.state, data_dir=world.manager.data_dir
            )
            start.wait()
            try:
                outcomes.append(handle._fork_many(2, name="exp", boot_timeout=30))
            except CelestoError as exc:
                outcomes.append(exc)

        threads = [threading.Thread(target=fork) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(30)

    refused = [outcome for outcome in outcomes if isinstance(outcome, CelestoError)]
    batches = [outcome for outcome in outcomes if not isinstance(outcome, BaseException)]
    assert len(refused) == 1 and len(batches) == 1, outcomes
    assert str(refused[0]) == (
        "A sandbox named 'exp-1' already exists. Choose another name with '--name', "
        "or run 'celesto sandbox delete exp-1'."
    )
    assert _names_of(batches[0]) == ["exp-1", "exp-2"]
    # The refused fork copied nothing: only the winner's children were made.
    assert sorted(world.created) == ["exp-1", "exp-2"]
    assert world.generations() == []


@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
def test_a_raw_qemu_source_started_while_waiting_is_refused_before_copying(
    world: _World, monkeypatch: pytest.MonkeyPatch, use_async: bool
) -> None:
    source = world.add_source("qemu", VMState.STOPPED)
    stored = world.state.get_vm(_SOURCE).config
    world.state.update_vm(_SOURCE, config=stored.model_copy(update={"rootfs_format": "raw"}))
    claim = Celesto._claim_fork_names

    def claim_then_start(self: Celesto, *args: Any, **kwargs: Any) -> Any:
        # Someone starts the source after the fork's checks, before its lock.
        claimed = claim(self, *args, **kwargs)
        world.state.update_vm(_SOURCE, status=VMState.RUNNING)
        return claimed

    monkeypatch.setattr(Celesto, "_claim_fork_names", claim_then_start)

    with pytest.raises(CelestoError) as caught:
        if use_async:
            asyncio.run(source._async_fork_many(2, boot_timeout=30))
        else:
            source._fork_many(2, boot_timeout=30)

    assert str(caught.value) == (
        "Sandbox 'src' couldn't be copied while running. "
        "Run 'celesto sandbox stop src', then fork again."
    )
    assert world.capture_policies == []
    assert world.created == []
    assert world.generations() == []


def test_fork_plan_captures_shared_base_once_and_reuses_it(
    world: _World, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A source disappearing after capture must not make each child recopy its base."""
    base = world.tmp_path / "base.qcow2"
    source = world.add_source("qemu", VMState.STOPPED)
    lookups: list[str] = []
    passed_bases: list[Path | None] = []
    monkeypatch.setattr(
        source._sdk,
        "_shared_base_image",
        lambda info: (lookups.append(info.vm_id), base)[1],
    )
    monkeypatch.setattr(source._sdk, "_ensure_fork_disk_space", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(source._sdk, "_ensure_fork_ports", lambda *_args: None)
    monkeypatch.setattr(
        source._sdk,
        "_create_from_disk",
        lambda _source, _disk, _name, **kwargs: passed_bases.append(kwargs["shared_base"]),
    )
    plan = source._plan_fork(2, name="exp", parallel=1, boot_timeout=30)
    generation = SimpleNamespace(
        artifacts=SimpleNamespace(disk_path=world.tmp_path / "capture"), created_at=None
    )
    source._create_fork_child(plan, generation, "exp-1")
    source._create_fork_child(plan, generation, "exp-2")

    assert lookups == ["src"]
    assert plan.shared_base == base
    assert passed_bases == [base, base]

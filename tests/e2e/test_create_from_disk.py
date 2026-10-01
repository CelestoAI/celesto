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

"""New sandboxes made from a copy of another sandbox's disk stand on their own.

This is the internal building block for fork (not a user command yet). The
test creates a source sandbox, writes a marker file, stops it, copies its disk
to a stand-in for fork's saved copy, and creates two sandboxes from that copy.
Both must boot with the marker, their own name, network, ports and identity,
and keep working after the saved copy and the source are deleted. Each run
writes a JSON summary of every sandbox.
"""

from __future__ import annotations

import asyncio
import json
import os
import platform
import shutil
import socket
import subprocess
import uuid
from contextlib import suppress
from pathlib import Path
from typing import Any

import pytest
from _util import BOOT_TIMEOUT, E2E_BACKENDS, require_backend_available, selected_backend

from celesto import Celesto
from celesto.cli._sqlite import SQLiteStateManager
from celesto.exceptions import CelestoError, VMNotFoundError
from celesto.facade import _build_auto_config
from celesto.host.disk import clone_or_sparse_copy
from celesto.runtime.backends import BACKEND_QEMU
from celesto.types import PortForwardConfig, VMInfo, VMState, WorkspaceMount
from celesto.vm import CelestoManager, resolve_data_dir

pytestmark = pytest.mark.e2e

_MARKER_PATH = "/root/copied-disk-marker"
_FORWARD_GUEST_PORT = 8080
_HOST_KEY_FINGERPRINT = "ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub | awk '{print $2}'"


def _require_backend(backend: str, request: pytest.FixtureRequest) -> None:
    selected = selected_backend(request.config)
    if selected != "all" and backend != selected:
        pytest.skip(
            f"End-to-end tests for '{backend}' are skipped because this run selected "
            f"'{selected}'; rerun all backends with: pytest tests/e2e."
        )
    if backend == BACKEND_QEMU and platform.system() == "Darwin":
        # macOS runs QEMU with Hypervisor.framework, so /dev/kvm is not needed.
        if shutil.which("qemu-system-aarch64") is None:
            pytest.skip("Install QEMU (brew install qemu) to run the copied-disk test.")
        return
    require_backend_available(backend, request.config, sandbox_name=f"disk-copy-{backend}")  # type: ignore[arg-type]


def _free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _port_is_bound(port: int) -> bool:
    """True when something on this machine listens on 127.0.0.1:*port*."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return True
    return False


def _guest_value(sandbox: Celesto, command: str) -> str:
    result = sandbox.run(command)
    assert result.exit_code == 0, f"{sandbox.vm_id}: {command!r} failed: {result.stderr}"
    return result.stdout.strip()


def _backing_chain(disk: Path) -> list[str]:
    """Return every file a disk reads from, top first, as qemu-img reports it."""
    if disk.suffix != ".qcow2":
        return [str(disk)]
    result = subprocess.run(
        ["qemu-img", "info", "-U", "--backing-chain", "--output=json", str(disk)],
        capture_output=True,
        text=True,
        check=True,
    )
    return [str(Path(layer["filename"]).resolve()) for layer in json.loads(result.stdout)]


def _summary(info: VMInfo) -> dict[str, Any]:
    network = info.network
    return {
        "status": info.status.value,
        "instance_id": info.config.instance_id,
        "guest_ip": network.guest_ip if network else None,
        "network_device": network.tap_device if network else None,
        "ssh_host_port": network.ssh_host_port if network else None,
        "port_forwards": [
            {"host_port": forward.host_port, "guest_port": forward.guest_port}
            for forward in info.config.port_forwards
        ],
        "vsock": info.config.vsock.model_dump() if info.config.vsock else None,
        "disk": str(info.config.rootfs_path),
        "retain_disk_on_delete": info.config.retain_disk_on_delete,
    }


@pytest.mark.parametrize("backend", E2E_BACKENDS, ids=str)
def test_sandboxes_created_from_a_copied_disk_are_independent(
    backend: str, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    """Two sandboxes from one disk copy boot with the source's files and new resources."""
    _require_backend(backend, request)

    prefix = os.environ.get("CELESTO_E2E_NAME_PREFIX", "e2e-")
    suffix = uuid.uuid4().hex[:6]
    source_name = f"{prefix}disk-src-{suffix}"
    child_names = [f"{prefix}disk-copy{index}-{suffix}" for index in (1, 2)]
    marker = f"copied-disk-{suffix}"
    artifact_dir = Path(os.environ.get("CELESTO_E2E_ARTIFACT_DIR", tmp_path))
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact = artifact_dir / f"create-from-disk-{backend}.json"
    report: dict[str, Any] = {"backend": backend, "source": source_name, "sandboxes": {}}

    state = SQLiteStateManager(resolve_data_dir() / "celesto.db")
    manager = CelestoManager(state_manager=state)
    created: list[str] = []
    generation_dir = resolve_data_dir() / "e2e-generations" / suffix
    try:
        config, ssh_key_path = _build_auto_config(vm_name=source_name, os="alpine", backend=backend)
        if backend == BACKEND_QEMU:
            # Create-time forwards exist only for QEMU's user-mode network.
            config = config.model_copy(
                update={
                    "port_forwards": [
                        PortForwardConfig(
                            host_port=_free_local_port(), guest_port=_FORWARD_GUEST_PORT
                        )
                    ]
                }
            )
        source = Celesto(config=config, ssh_key_path=ssh_key_path, state_manager=state)
        created.append(source_name)
        source.start(boot_timeout=BOOT_TIMEOUT)
        _guest_value(source, f"echo {marker} > {_MARKER_PATH} && sync && cat {_MARKER_PATH}")
        source_machine_id = _guest_value(source, "cat /etc/machine-id")
        source_fingerprint = _guest_value(source, _HOST_KEY_FINGERPRINT)
        source.stop()
        source_info = state.get_vm(source_name)
        report["sandboxes"][source_name] = {
            **_summary(source_info),
            "machine_id": source_machine_id,
            "host_key_fingerprint": source_fingerprint,
            "backing_chain": _backing_chain(source_info.config.rootfs_path),
        }

        # Stand-in for fork's saved copy: a disk file outside the disk
        # directory that is deleted once the new sandboxes exist.
        generation_dir.mkdir(parents=True, exist_ok=True)
        assert source_info.config.rootfs_path is not None
        generation_disk = generation_dir / source_info.config.rootfs_path.name
        clone_or_sparse_copy(source_info.config.rootfs_path, generation_disk)

        # The first copy goes through the sync path and the second through
        # the async one, so both stay covered.
        first_child, second_child = child_names
        info = manager._create_from_disk(source_info, generation_disk, first_child)
        created.append(first_child)
        assert info.status == VMState.CREATED
        info = asyncio.run(
            manager._async_create_from_disk(source_info, generation_disk, second_child)
        )
        created.append(second_child)
        assert info.status == VMState.CREATED
        shutil.rmtree(generation_dir)

        children: dict[str, Celesto] = {}
        for name in child_names:
            child = Celesto.from_id(name, ssh_key_path=ssh_key_path, state_manager=state)
            child.start(boot_timeout=BOOT_TIMEOUT)
            children[name] = child
            info = state.get_vm(name)
            entry = _summary(info)
            entry["marker"] = _guest_value(child, f"cat {_MARKER_PATH}")
            entry["guest_instance_id"] = _guest_value(child, "cat /etc/celesto/instance-id")
            entry["machine_id"] = _guest_value(child, "cat /etc/machine-id")
            entry["host_key_fingerprint"] = _guest_value(child, _HOST_KEY_FINGERPRINT)
            child_disk = Path(entry["disk"])
            entry["backing_chain"] = _backing_chain(child_disk)
            entry["base_image_copies"] = sorted(
                path.name for path in child_disk.parent.glob(f"{child_disk.name}.backing-*")
            )
            entry["forward_host_ports_bound"] = [
                _port_is_bound(forward["host_port"]) for forward in entry["port_forwards"]
            ]
            lineage = state.get_vm_lineage(name)
            entry["lineage"] = (
                {"forked_from": lineage.forked_from, "forked_at": lineage.forked_at.isoformat()}
                if lineage
                else None
            )
            report["sandboxes"][name] = entry

        everyone = [source_name, *child_names]
        sandboxes = report["sandboxes"]
        for name in child_names:
            entry = sandboxes[name]
            assert entry["marker"] == marker, f"{name} lost the source's files: {entry}"
            assert entry["guest_instance_id"] == entry["instance_id"], f"{name}: {entry}"
            assert entry["retain_disk_on_delete"] is False
            assert entry["lineage"] is not None, f"{name} has no lineage"
            assert entry["lineage"]["forked_from"] == source_name
            assert [f["guest_port"] for f in entry["port_forwards"]] == [
                f["guest_port"] for f in sandboxes[source_name]["port_forwards"]
            ], f"{name} forwards different guest ports: {entry}"
            assert all(entry["forward_host_ports_bound"]), f"{name} forward not listening: {entry}"
            if backend == BACKEND_QEMU:
                # Like any QEMU sandbox, a copy shares the read-only base
                # image; only the layers above it are its own.
                source_chain = sandboxes[source_name]["backing_chain"]
                assert len(source_chain) >= 2, f"source has no base image: {source_chain}"
                assert entry["backing_chain"] == [
                    str(Path(entry["disk"]).resolve()),
                    *source_chain[1:],
                ], f"{name} does not share the base image: {entry['backing_chain']}"
                assert entry["base_image_copies"] == [], f"{name}: {entry['base_image_copies']}"
        for key in ("instance_id", "machine_id", "host_key_fingerprint", "ssh_host_port", "disk"):
            values = [sandboxes[name][key] for name in everyone]
            assert len(set(values)) == len(values), f"{key} is shared: {values}"
        forward_ports = [
            forward["host_port"]
            for name in everyone
            for forward in sandboxes[name]["port_forwards"]
        ]
        assert len(set(forward_ports)) == len(forward_ports), f"forward ports: {forward_ports}"
        vsock_cids = [
            sandboxes[name]["vsock"]["guest_cid"] for name in everyone if sandboxes[name]["vsock"]
        ]
        assert len(set(vsock_cids)) == len(vsock_cids), f"vsock CIDs are shared: {vsock_cids}"
        vsock_sockets = [
            sandboxes[name]["vsock"]["uds_path"]
            for name in everyone
            if sandboxes[name]["vsock"] and sandboxes[name]["vsock"]["uds_path"]
        ]
        assert len(set(vsock_sockets)) == len(vsock_sockets), f"vsock sockets: {vsock_sockets}"
        if source_info.network is not None and source_info.network.tap_device != "usernet":
            # QEMU's user-mode network gives every sandbox the same private
            # address, so addresses must differ only on host-network devices.
            for key in ("guest_ip", "network_device"):
                values = [sandboxes[name][key] for name in everyone]
                assert len(set(values)) == len(values), f"{key} is shared: {values}"

        manager.delete(source_name)
        created.remove(source_name)
        report["source_deleted"] = True
        after: dict[str, Any] = {}
        for name, child in children.items():
            child.stop()
            child.start(boot_timeout=BOOT_TIMEOUT)
            lineage = state.get_vm_lineage(name)
            after[name] = {
                "marker": _guest_value(child, f"cat {_MARKER_PATH}"),
                "forked_from": lineage.forked_from if lineage else None,
            }
        report["after_source_deleted"] = after
        for name, values in after.items():
            assert values == {"marker": marker, "forked_from": source_name}, f"{name}: {values}"
        report["result"] = "passed"
    except BaseException as exc:
        report["result"] = f"failed: {exc}"
        raise
    finally:
        artifact.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(f"create-from-disk artifact: {artifact}")
        for name in reversed(created):
            with suppress(Exception):
                manager.delete(name)
        shutil.rmtree(generation_dir, ignore_errors=True)
        manager.close()


@pytest.mark.parametrize("backend", E2E_BACKENDS, ids=str)
def test_sources_a_disk_copy_cannot_reproduce_are_refused(
    backend: str, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    """Shared folders, extra drives, shared disks and kept disks stop a copy early."""
    _require_backend(backend, request)

    prefix = os.environ.get("CELESTO_E2E_NAME_PREFIX", "e2e-")
    suffix = uuid.uuid4().hex[:6]
    artifact_dir = Path(os.environ.get("CELESTO_E2E_ARTIFACT_DIR", tmp_path))
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact = artifact_dir / f"create-from-disk-refusals-{backend}.json"
    state = SQLiteStateManager(resolve_data_dir() / "celesto.db")
    manager = CelestoManager(state_manager=state)
    shared_folder = tmp_path / "shared-folder"
    shared_folder.mkdir()
    extra_drive = tmp_path / "extra-drive.img"
    extra_drive.write_bytes(b"\0" * 4096)
    saved_disk = tmp_path / "saved-disk"
    saved_disk.write_bytes(b"\0" * 4096)

    cases: dict[str, dict[str, Any]] = {
        "extra-drive": {"extra_drives": [extra_drive]},
        "shared-disk": {"disk_mode": "shared"},
    }
    if backend == BACKEND_QEMU:
        # Shared folders exist only on QEMU.
        cases["shared-folder"] = {"workspace_mounts": [WorkspaceMount(host_path=shared_folder)]}
    report: dict[str, Any] = {"backend": backend, "cases": {}}
    created: list[str] = []
    try:
        for case, update in cases.items():
            source_name = f"{prefix}refuse-{case}-{suffix}"
            child_name = f"{prefix}refuse-{case}-copy-{suffix}"
            config, _key = _build_auto_config(vm_name=source_name, os="alpine", backend=backend)
            source = manager.create(config.model_copy(update=update))
            created.append(source_name)
            with pytest.raises(CelestoError) as caught:
                manager._create_from_disk(source, saved_disk, child_name)
            with pytest.raises(VMNotFoundError):
                state.get_vm(child_name)
            leftovers = sorted(p.name for p in manager.disk_dir.glob(f"{child_name}*"))
            report["cases"][case] = {"error": str(caught.value), "leftovers": leftovers}
            assert source_name in str(caught.value), caught.value
            assert leftovers == []

        if backend == BACKEND_QEMU:
            # A copy shares its source's base image, so a missing one stops it.
            source_name = f"{prefix}refuse-base-{suffix}"
            child_name = f"{prefix}refuse-base-copy-{suffix}"
            config, _key = _build_auto_config(vm_name=source_name, os="alpine", backend=backend)
            assert config.rootfs_path is not None
            base_copy = tmp_path / f"base{config.rootfs_path.suffix}"
            clone_or_sparse_copy(config.rootfs_path, base_copy)
            source = manager.create(config.model_copy(update={"rootfs_path": base_copy}))
            created.append(source_name)
            base_copy.unlink()
            with pytest.raises(CelestoError) as caught:
                manager._create_from_disk(source, saved_disk, child_name)
            with pytest.raises(VMNotFoundError):
                state.get_vm(child_name)
            leftovers = sorted(p.name for p in manager.disk_dir.glob(f"{child_name}*"))
            report["cases"]["missing-base-image"] = {
                "error": str(caught.value),
                "leftovers": leftovers,
            }
            assert source_name in str(caught.value), caught.value
            assert str(base_copy.resolve()) in str(caught.value), caught.value
            assert leftovers == []

        # A kept disk under the new name must never be reused or overwritten.
        source_name = f"{prefix}refuse-kept-{suffix}"
        child_name = f"{prefix}refuse-kept-copy-{suffix}"
        config, _key = _build_auto_config(vm_name=source_name, os="alpine", backend=backend)
        source = manager.create(config)
        created.append(source_name)
        assert source.config.rootfs_path is not None
        kept_disk = manager.disk_dir / f"{child_name}{source.config.rootfs_path.suffix}"
        kept_disk.write_bytes(b"kept")
        try:
            with pytest.raises(CelestoError) as caught:
                manager._create_from_disk(source, saved_disk, child_name)
            report["cases"]["kept-disk"] = {
                "error": str(caught.value),
                "kept_disk_untouched": kept_disk.read_bytes() == b"kept",
            }
            assert f"celesto sandbox delete {child_name}" in str(caught.value)
            assert kept_disk.read_bytes() == b"kept"
            with pytest.raises(VMNotFoundError):
                state.get_vm(child_name)
        finally:
            kept_disk.unlink(missing_ok=True)
        report["result"] = "passed"
    except BaseException as exc:
        report["result"] = f"failed: {exc}"
        raise
    finally:
        artifact.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(f"create-from-disk refusals artifact: {artifact}")
        for name in created:
            with suppress(Exception):
                manager.delete(name)
        manager.close()

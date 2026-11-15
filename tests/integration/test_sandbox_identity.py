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

"""Computers created at the same time must never share an ID or a disk.

A computer's ID is also its name. It keys the disk, logs, sockets and inventory
row. Unnamed computers get IDs like ``sbx-volta-k3x9p2``. These tests create
many computers at once through the real SDK and CLI paths with real
``qemu-img`` disks, without booting them, and write a JSON report of every ID
and disk to ``tmp_path`` as the result artifact.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest

from celesto._naming import SCIENTISTS
from celesto.cli.main import main
from celesto.cli.service import CLIService
from celesto.exceptions import VMAlreadyExistsError
from celesto.facade import Celesto
from celesto.images.boot import BootImage, DirectKernelBoot
from celesto.vm import CelestoManager

PARALLEL = 20
GENERATED_ID = re.compile(rf"^sbx-({'|'.join(SCIENTISTS)})-[a-z0-9]{{6}}$")

pytestmark = pytest.mark.skipif(
    shutil.which("qemu-img") is None,
    reason="needs qemu-img to create real computer disks",
)


@pytest.fixture
def boot_image(tmp_path: Path) -> BootImage:
    """A small qcow2 base image and a placeholder kernel; no VM is booted."""
    base = tmp_path / "images" / "base.qcow2"
    base.parent.mkdir()
    subprocess.run(["qemu-img", "create", "-f", "qcow2", str(base), "64M"], check=True)
    kernel = tmp_path / "images" / "vmlinuz"
    kernel.write_bytes(b"kernel")
    return BootImage(
        name="identity-test",
        rootfs_path=base,
        rootfs_format="qcow2",
        kernel_path=kernel,
        boot=DirectKernelBoot(quiet=False),
    )


def _create(boot_image: BootImage, data_dir: Path, **kwargs: Any) -> Celesto:
    return Celesto.from_image(
        boot_image,
        backend="qemu",
        network="slirp",
        data_dir=data_dir,
        socket_dir=data_dir / "sockets",
        **kwargs,
    )


def _qcow2_backing(disk: Path) -> str:
    info = subprocess.run(
        ["qemu-img", "info", "-U", "--output=json", str(disk)],
        check=True,
        capture_output=True,
        text=True,
    )
    return str(json.loads(info.stdout)["backing-filename"])


def _report(path: Path, vms: list[Celesto]) -> list[dict[str, str]]:
    rows = sorted(
        ({"id": vm.vm_id, "disk": str(vm.info.config.rootfs_path)} for vm in vms),
        key=lambda row: row["id"],
    )
    path.write_text(json.dumps(rows, indent=2) + "\n")
    return rows


def test_parallel_sdk_creates_get_unique_ids_and_disks(
    tmp_path: Path, boot_image: BootImage
) -> None:
    # The reported bug: unnamed SDK computers created from many threads drew
    # names from ~50 scientists, two got the same one, and both used one disk.
    data_dir = tmp_path / "data"

    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        vms = list(pool.map(lambda _: _create(boot_image, data_dir), range(PARALLEL)))
    try:
        rows = _report(tmp_path / "sdk-identity-report.json", vms)

        assert len({row["id"] for row in rows}) == PARALLEL
        assert len({row["disk"] for row in rows}) == PARALLEL
        for row in rows:
            assert GENERATED_ID.match(row["id"]), row["id"]
            disk = Path(row["disk"])
            assert disk == data_dir / "disks" / f"{row['id']}.qcow2"
            assert _qcow2_backing(disk) == str(boot_image.rootfs_path)
    finally:
        for vm in vms:
            vm.delete()


def test_parallel_cli_creates_share_one_inventory_safely(
    tmp_path: Path,
    boot_image: BootImage,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    data_dir = tmp_path / "data"
    monkeypatch.setenv("CELESTO_DATA_DIR", str(data_dir))
    state = CLIService(data_dir=data_dir).state_manager()

    def create(_: int) -> Celesto:
        return _create(boot_image, data_dir, state_manager=state)

    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        vms = list(pool.map(create, range(PARALLEL)))
    try:
        rows = _report(tmp_path / "cli-identity-report.json", vms)
        assert len({row["id"] for row in rows}) == PARALLEL
        assert {info.vm_id for info in state.list_vms()} == {row["id"] for row in rows}

        # The generated ID is what users type in later commands.
        target = rows[0]["id"]
        capsys.readouterr()
        assert main(["computer", "info", target, "--json"]) == 0
        assert json.loads(capsys.readouterr().out)["data"]["vm"]["name"] == target

        # A name the caller chooses is used as-is, and only once.
        named = _create(boot_image, data_dir, state_manager=state, vm_id="my-computer")
        vms.append(named)
        assert named.vm_id == "my-computer"
        with pytest.raises(VMAlreadyExistsError, match="my-computer"):
            _create(boot_image, data_dir, state_manager=state, vm_id="my-computer")
    finally:
        for vm in vms:
            vm.delete()
        state.close()


def test_same_name_in_two_sdk_processes_never_shares_a_disk(
    tmp_path: Path, boot_image: BootImage
) -> None:
    # Two SDK scripts each keep their own in-memory inventory, so neither can
    # see the other's computer. Only the disk on the shared data directory
    # shows the name is taken, and the second create must refuse to reuse it.
    data_dir = tmp_path / "data"
    first = _create(boot_image, data_dir, vm_id="shared-name")
    disk = data_dir / "disks" / "shared-name.qcow2"
    try:
        assert first.info.config.rootfs_path == disk
        before = disk.stat()

        with pytest.raises(VMAlreadyExistsError) as excinfo:
            _create(boot_image, data_dir, vm_id="shared-name")

        message = str(excinfo.value)
        report = {
            "first": {"id": first.vm_id, "disk": str(disk)},
            "second_error": message,
            "disk_untouched": disk.stat().st_mtime_ns == before.st_mtime_ns,
        }
        (tmp_path / "same-name-report.json").write_text(json.dumps(report, indent=2) + "\n")

        assert message == (
            "A computer named 'shared-name' already exists; choose another name or run "
            "'celesto computer delete shared-name'."
        )
        assert disk.exists()
        assert disk.stat().st_mtime_ns == before.st_mtime_ns
        assert _qcow2_backing(disk) == str(boot_image.rootfs_path)
    finally:
        first.delete()
    assert not disk.exists()


def test_disk_kept_on_purpose_is_reused_by_a_new_sdk_process(
    tmp_path: Path, boot_image: BootImage
) -> None:
    # A disk kept with retain_disk_on_delete belongs to no computer, so a later
    # script that asks for the same name picks it up again.
    data_dir = tmp_path / "data"
    first = _create(boot_image, data_dir, vm_id="kept-name")
    # The SDK has no keyword for this yet; set it the way the CLI stores it.
    state = first._sdk.state
    config = state.get_vm("kept-name").config
    state.update_vm("kept-name", config=config.model_copy(update={"retain_disk_on_delete": True}))
    disk = data_dir / "disks" / "kept-name.qcow2"
    first.delete()
    assert disk.exists()

    second = _create(boot_image, data_dir, vm_id="kept-name")
    try:
        assert second.info.config.rootfs_path == disk
    finally:
        second.delete()


_CRASHING_SDK_SCRIPT = """
import os, sys
from pathlib import Path
from celesto import facade
from celesto.facade import Celesto
from celesto.images.boot import BootImage, DirectKernelBoot

base, kernel, data_dir, name, keep = sys.argv[1:6]
image = BootImage(
    name="identity-test",
    rootfs_path=Path(base),
    rootfs_format="qcow2",
    kernel_path=Path(kernel),
    boot=DirectKernelBoot(quiet=False),
)
# Persistent browser profiles set retain_disk_on_delete when they create the
# computer; the SDK has no keyword for it, so set it on the way in.
create = facade.CelestoManager.create
def create_kept(self, config):
    return create(self, config.model_copy(update={"retain_disk_on_delete": keep == "keep"}))
facade.CelestoManager.create = create_kept
Celesto.from_image(
    image,
    backend="qemu",
    network="slirp",
    data_dir=Path(data_dir),
    socket_dir=Path(data_dir) / "sockets",
    vm_id=name,
)
os._exit(0)  # exit without delete, like a killed script
"""


def _create_in_crashing_process(
    boot_image: BootImage, data_dir: Path, name: str, *, keep: bool
) -> None:
    subprocess.run(
        [
            sys.executable,
            "-c",
            _CRASHING_SDK_SCRIPT,
            str(boot_image.rootfs_path),
            str(boot_image.kernel_path),
            str(data_dir),
            name,
            "keep" if keep else "no-keep",
        ],
        check=True,
    )


def test_kept_disk_reopens_after_its_sdk_process_crashed(
    tmp_path: Path, boot_image: BootImage
) -> None:
    # A persistent browser profile keeps its disk under a stable name. If the
    # script that owned it died without cleaning up, the next run must still
    # get the same disk back.
    data_dir = tmp_path / "data"
    _create_in_crashing_process(boot_image, data_dir, "profile-name", keep=True)
    disk = data_dir / "disks" / "profile-name.qcow2"
    assert disk.exists()

    reopened = _create(boot_image, data_dir, vm_id="profile-name")
    try:
        assert reopened.info.config.rootfs_path == disk
        # While this script owns it, nobody else may take it.
        with pytest.raises(VMAlreadyExistsError, match="profile-name"):
            _create(boot_image, data_dir, vm_id="profile-name")
    finally:
        reopened.delete()
    (tmp_path / "crashed-profile-report.json").write_text(
        json.dumps({"id": "profile-name", "disk": str(disk), "reopened": True}, indent=2) + "\n"
    )


def test_unkept_disk_from_crashed_sdk_process_is_not_adopted(
    tmp_path: Path, boot_image: BootImage
) -> None:
    data_dir = tmp_path / "data"
    _create_in_crashing_process(boot_image, data_dir, "left-behind", keep=False)
    disk = data_dir / "disks" / "left-behind.qcow2"

    with pytest.raises(VMAlreadyExistsError, match="celesto computer delete left-behind") as exc:
        _create(boot_image, data_dir, vm_id="left-behind")

    assert disk.exists()
    (tmp_path / "unkept-crash-report.json").write_text(
        json.dumps({"id": "left-behind", "disk": str(disk), "rejected": str(exc.value)}, indent=2)
        + "\n"
    )


# Holds a file open while its command line names only the process itself,
# like Firecracker and libkrun, whose arguments never mention the disk.
_HOLD_OPEN_SCRIPT = """
import sys, time
handle = open(sys.stdin.readline().strip(), "rb")
print("ready", flush=True)
time.sleep(60)
"""


def test_kept_disk_still_open_in_a_runtime_is_not_adopted(
    tmp_path: Path, boot_image: BootImage
) -> None:
    # The script that owned the disk died, but the computer's runtime outlived
    # it and still has the disk open. Taking the disk now would share it.
    data_dir = tmp_path / "data"
    _create_in_crashing_process(boot_image, data_dir, "still-running", keep=True)
    disk = data_dir / "disks" / "still-running.qcow2"

    holder = subprocess.Popen(
        [sys.executable, "-c", _HOLD_OPEN_SCRIPT],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdin is not None and holder.stdout is not None
        holder.stdin.write(f"{disk}\n")
        holder.stdin.flush()
        assert holder.stdout.readline().strip() == "ready"

        with pytest.raises(VMAlreadyExistsError, match="still-running") as exc:
            _create(boot_image, data_dir, vm_id="still-running")
    finally:
        holder.kill()
        holder.wait()

    reopened = _create(boot_image, data_dir, vm_id="still-running")
    reopened.delete()
    (tmp_path / "open-disk-report.json").write_text(
        json.dumps(
            {
                "id": "still-running",
                "disk": str(disk),
                "rejected_while_open": str(exc.value),
                "reopened_after_runtime_exit": True,
            },
            indent=2,
        )
        + "\n"
    )


def test_default_prune_keeps_disk_of_crashed_script(tmp_path: Path, boot_image: BootImage) -> None:
    # A kept disk whose script died is still a disk the user asked to keep.
    data_dir = tmp_path / "data"
    _create_in_crashing_process(boot_image, data_dir, "kept-after-crash", keep=True)
    disk = data_dir / "disks" / "kept-after-crash.qcow2"
    manager = CelestoManager(data_dir=data_dir, socket_dir=data_dir / "sockets")

    removed = manager.prune_leftover_artifacts()
    assert all(item.path != disk for item in removed)
    assert disk.exists()

    removed = manager.prune_leftover_artifacts(include_retained=True)
    assert disk in {item.path for item in removed}
    assert not disk.exists()
    (tmp_path / "prune-report.json").write_text(
        json.dumps({"id": "kept-after-crash", "disk": str(disk), "kept_by_default": True}, indent=2)
        + "\n"
    )

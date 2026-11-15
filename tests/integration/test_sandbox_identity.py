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

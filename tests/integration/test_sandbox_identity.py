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

"""Concurrent sandbox creation must give every sandbox its own ID and disk.

Each sandbox has a generated unique ID that keys its disk, logs, sockets and
inventory row, plus a friendly name. These tests create many sandboxes at once
through the real SDK and CLI paths, with real ``qemu-img`` disks, and write a
JSON report of every ID, name and disk to ``tmp_path`` as the result artifact.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from typing import Any

import pytest

from celesto.cli.main import main
from celesto.cli.service import CLIService
from celesto.exceptions import VMAlreadyExistsError
from celesto.facade import Celesto
from celesto.images.boot import BootImage, DirectKernelBoot
from celesto.types import VMConfig

PARALLEL = 20

pytestmark = pytest.mark.skipif(
    shutil.which("qemu-img") is None,
    reason="needs qemu-img to create real sandbox disks",
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


def _report(path: Path, rows: list[dict[str, str]]) -> None:
    path.write_text(json.dumps(sorted(rows, key=lambda row: row["id"]), indent=2) + "\n")


def test_parallel_sdk_creates_get_unique_ids_and_disks(
    tmp_path: Path, boot_image: BootImage
) -> None:
    # The reported bug: unnamed SDK computers created from many threads drew
    # names from ~50 scientists, two got the same one, and both used one disk.
    data_dir = tmp_path / "data"

    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        vms = list(pool.map(lambda _: _create(boot_image, data_dir), range(PARALLEL)))
    try:
        rows = [
            {
                "id": vm.vm_id,
                "name": vm.name,
                "disk": str(vm.info.config.rootfs_path),
            }
            for vm in vms
        ]
        _report(tmp_path / "sdk-identity-report.json", rows)

        ids = [row["id"] for row in rows]
        disks = [Path(row["disk"]) for row in rows]
        assert len(set(ids)) == PARALLEL
        assert len(set(disks)) == PARALLEL
        for row, disk in zip(rows, disks, strict=True):
            assert disk == data_dir / "disks" / f"{row['id']}.qcow2"
            assert _qcow2_backing(disk) == str(boot_image.rootfs_path)
            assert row["name"], "every computer gets a friendly name"
    finally:
        for vm in vms:
            vm.delete()


def test_parallel_cli_creates_get_unique_names_and_resolve_by_name(
    tmp_path: Path,
    boot_image: BootImage,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # In the persistent CLI inventory, names are unique among existing
    # computers, so `celesto computer <verb> <name>` stays unambiguous.
    data_dir = tmp_path / "data"
    monkeypatch.setenv("CELESTO_DATA_DIR", str(data_dir))
    service = CLIService(data_dir=data_dir)
    state = service.state_manager()

    def create(_: int) -> Celesto:
        return _create(boot_image, data_dir, state_manager=state)

    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        vms = list(pool.map(create, range(PARALLEL)))
    try:
        rows = [{"id": vm.vm_id, "name": vm.name} for vm in vms]
        _report(tmp_path / "cli-identity-report.json", rows)
        assert len({row["id"] for row in rows}) == PARALLEL
        assert len({row["name"] for row in rows}) == PARALLEL
        assert {(info.vm_id, info.config.name) for info in state.list_vms()} == {
            (row["id"], row["name"]) for row in rows
        }

        # Any command accepts the friendly name or the ID.
        target = rows[0]
        for ref in (target["name"], target["id"]):
            capsys.readouterr()
            assert main(["computer", "info", ref, "--json"]) == 0
            payload = json.loads(capsys.readouterr().out)
            assert payload["data"]["vm"]["id"] == target["id"]
            assert payload["data"]["vm"]["name"] == target["name"]

        # A name already in use is refused instead of sharing anything.
        with pytest.raises(VMAlreadyExistsError, match=target["name"]):
            Celesto(
                VMConfig(
                    name=target["name"],
                    kernel_path=boot_image.kernel_path,
                    rootfs_path=boot_image.rootfs_path,
                    rootfs_format="qcow2",
                    backend="qemu",
                ),
                data_dir=data_dir,
                socket_dir=data_dir / "sockets",
                state_manager=state,
            )
    finally:
        for vm in vms:
            vm.delete()
        state.close()


def test_computer_saved_before_ids_still_works_by_its_name(
    tmp_path: Path,
    boot_image: BootImage,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Inventories written by older releases key each computer by its name and
    # have no name column. Those computers keep their name as both ID and name.
    data_dir = tmp_path / "data"
    data_dir.mkdir(mode=0o700)
    db_path = data_dir / "celesto.db"
    legacy = VMConfig(
        vm_id="sbx-volta",
        kernel_path=boot_image.kernel_path,
        rootfs_path=boot_image.rootfs_path,
        rootfs_format="qcow2",
        backend="qemu",
    )
    legacy_json = json.dumps(
        {key: value for key, value in json.loads(legacy.model_dump_json()).items() if key != "name"}
    )
    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.execute(
            "CREATE TABLE vms (id TEXT PRIMARY KEY, status TEXT NOT NULL, config TEXT NOT NULL,"
            " network TEXT, pid INTEGER, socket_path TEXT, created_at TEXT NOT NULL,"
            " updated_at TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO vms (id, status, config, created_at, updated_at)"
            " VALUES ('sbx-volta', 'stopped', ?, '2026-01-01T00:00:00+00:00',"
            " '2026-01-01T00:00:00+00:00')",
            (legacy_json,),
        )
    db_path.chmod(0o600)
    monkeypatch.setenv("CELESTO_DATA_DIR", str(data_dir))

    assert main(["computer", "info", "sbx-volta", "--json"]) == 0
    vm = json.loads(capsys.readouterr().out)["data"]["vm"]
    assert (vm["id"], vm["name"]) == ("sbx-volta", "sbx-volta")

    # The old name stays reserved: a new computer cannot take it.
    state = CLIService(data_dir=data_dir).state_manager()
    try:
        with pytest.raises(VMAlreadyExistsError, match="sbx-volta"):
            _create(boot_image, data_dir, state_manager=state, name="sbx-volta")
        assert [info.vm_id for info in state.list_vms()] == ["sbx-volta"]
    finally:
        state.close()
    (tmp_path / "legacy-identity-report.json").write_text(json.dumps(vm, indent=2) + "\n")

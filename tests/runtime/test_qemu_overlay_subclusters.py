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

"""Per-VM qcow2 overlays honor ``QemuRootDiskOptions.qcow2_subclusters``.

These run the real ``qemu-img`` against a real raw base, then read the
overlay's layout back with ``qemu-img info``. Failure modes:
1. The option is accepted but the overlay keeps the default 64 KiB layout.
2. Default overlays change layout for every existing user.
3. The async create path drifts from the sync one.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from celesto.types import QemuRootDiskOptions, VMConfig
from celesto.vm import CelestoManager

pytestmark = pytest.mark.skipif(
    shutil.which("qemu-img") is None, reason="needs qemu-img to create real overlays"
)


def _manager(tmp_path: Path) -> CelestoManager:
    return CelestoManager(
        data_dir=tmp_path / "data", socket_dir=tmp_path / "sockets", backend="qemu"
    )


def _config(tmp_path: Path, root_disk: QemuRootDiskOptions | None) -> VMConfig:
    kernel = tmp_path / "vmlinux"
    kernel.touch()
    base = tmp_path / "base.ext4"
    with base.open("wb") as handle:
        handle.truncate(64 * 1024 * 1024)
    return VMConfig(
        vm_id="vm-overlay",
        kernel_path=kernel,
        rootfs_path=base,
        rootfs_format="raw-ext4",
        backend="qemu",
        qemu_root_disk=root_disk,
    )


def _layout(disk: Path | None) -> tuple[int, bool]:
    assert disk is not None
    info = json.loads(
        subprocess.run(
            ["qemu-img", "info", "--output=json", str(disk)],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    )
    extended_l2 = bool(info.get("format-specific", {}).get("data", {}).get("extended-l2"))
    return info["cluster-size"], extended_l2


def test_overlay_uses_subclusters_when_requested(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    try:
        config = manager._materialize_rootfs(
            _config(tmp_path, QemuRootDiskOptions(qcow2_subclusters=True))
        )
    finally:
        manager.close()

    assert config.rootfs_format == "qcow2"
    assert _layout(config.rootfs_path) == (128 * 1024, True)


def test_overlay_keeps_default_layout_without_the_option(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    try:
        # Root disk tuning without the option must not change the layout.
        config = manager._materialize_rootfs(
            _config(tmp_path, QemuRootDiskOptions(bus="pci", iothread=True))
        )
    finally:
        manager.close()

    assert _layout(config.rootfs_path) == (64 * 1024, False)


def test_async_overlay_uses_subclusters_when_requested(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    try:
        config = asyncio.run(
            manager._async_materialize_rootfs(
                _config(tmp_path, QemuRootDiskOptions(qcow2_subclusters=True))
            )
        )
    finally:
        manager.close()

    assert _layout(config.rootfs_path) == (128 * 1024, True)

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

"""A real QEMU guest runs on the opt-in I/O tuning: vhost-net PCI NIC, PCI
root disk with an iothread, and a qcow2 overlay with 4 KiB subclusters.

Every command reaches the guest over SSH through the tuned NIC, so the guest
answering at all proves the vhost-net data path works. Failure modes:
1. QEMU rejects the tuned argv (machine, NIC, or disk), so the VM never boots.
2. The guest kernel does not find the PCI NIC or disk, so SSH never answers.
3. ``vhost=on`` is dropped, so QEMU still moves every packet itself.
4. The overlay keeps the 64 KiB layout, or small writes do not survive a
   restart on the subcluster layout.

Each variant writes ``qemu-io-<variant>.json`` with its evidence to
``$CELESTO_E2E_ARTIFACT_DIR`` (or the test's tmp dir).
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import subprocess
from contextlib import suppress
from pathlib import Path
from typing import Any

import pytest
from _util import BOOT_TIMEOUT, require_backend_available, selected_backend

from celesto import Celesto
from celesto.facade import _build_auto_config
from celesto.runtime.backends import BACKEND_QEMU
from celesto.types import QemuNetOptions, QemuRootDiskOptions, VMState

pytestmark = pytest.mark.e2e

_VHOST_NET = Path("/dev/vhost-net")
# 257 x 4 KiB: spans more than one 128 KiB cluster and ends mid-cluster.
_SMALL_WRITES = "dd if=/dev/urandom of=/root/small-writes.bin bs=4k count=257 conv=fsync"


def _require_qemu_with_vhost_net(request: pytest.FixtureRequest) -> None:
    selected = selected_backend(request.config)
    if selected not in ("all", BACKEND_QEMU):
        pytest.skip(
            f"QEMU I/O tuning e2e is skipped because this run selected '{selected}'; "
            "rerun with: pytest tests/e2e --e2e-backend qemu."
        )
    require_backend_available(BACKEND_QEMU, request.config, sandbox_name="qemu-io-tuning")
    if not (_VHOST_NET.exists() and os.access(_VHOST_NET, os.R_OK | os.W_OK)):
        message = (
            "QEMU I/O tuning e2e needs read-write /dev/vhost-net; load it with "
            "`sudo modprobe vhost_net` and grant access with "
            "`sudo chgrp kvm /dev/vhost-net && sudo chmod 660 /dev/vhost-net`."
        )
        if selected == BACKEND_QEMU:
            pytest.fail(message)
        pytest.skip(message)


def _process_tree(pid: int) -> list[int]:
    """Return ``pid`` and its descendants (the launch may wrap QEMU)."""
    pids, index = [pid], 0
    while index < len(pids):
        for children in Path(f"/proc/{pids[index]}/task").glob("*/children"):
            with suppress(OSError):
                pids.extend(int(child) for child in children.read_text().split())
        index += 1
    return pids


def _open_vhost_net_fds(pid: int) -> int:
    """Count /dev/vhost-net descriptors held by the VM's process tree."""
    count = 0
    for tree_pid in _process_tree(pid):
        for fd in Path(f"/proc/{tree_pid}/fd").glob("*"):
            with suppress(OSError):
                if os.readlink(fd) == str(_VHOST_NET):
                    count += 1
    return count


def _overlay_info(disk: Path) -> dict[str, Any]:
    # -U: the running VM holds the image lock; this is a read-only peek.
    result = subprocess.run(
        ["qemu-img", "info", "-U", "--output=json", str(disk)],
        check=True,
        capture_output=True,
        text=True,
    )
    info = json.loads(result.stdout)
    return {
        "format": info["format"],
        "cluster_size": info["cluster-size"],
        "extended_l2": bool(info.get("format-specific", {}).get("data", {}).get("extended-l2")),
    }


def _guest(sandbox: Celesto, command: str) -> str:
    result = sandbox.run(command)
    assert result.exit_code == 0, f"{command!r} failed: {result.stderr or result.stdout}"
    return result.stdout.strip()


def _artifact_dir(tmp_path: Path) -> Path:
    directory = Path(os.environ.get("CELESTO_E2E_ARTIFACT_DIR") or tmp_path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _console_tail(sandbox: Celesto, lines: int = 60) -> list[str]:
    log = sandbox.data_dir / f"{sandbox.vm_id}.log"
    with suppress(OSError):
        return log.read_text(errors="replace").splitlines()[-lines:]
    return []


@pytest.mark.parametrize("tuned", [True, False], ids=["tuned", "baseline"])
def test_qemu_guest_runs_on_vhost_pci_nic_and_subcluster_overlay(
    tuned: bool, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    """The tuned guest works end to end; ``baseline`` runs the same steps on
    the default NIC and disk so a restart failure can be pinned on the tuning
    or not."""
    _require_qemu_with_vhost_net(request)

    variant = "tuned" if tuned else "baseline"
    config, ssh_key_path = _build_auto_config(
        vm_name=f"e2e-qemu-io-{variant}-{secrets.token_hex(2)}",
        os="alpine",
        backend=BACKEND_QEMU,
        qemu_machine="auto",
        memory=None,
        disk_size_mib=None,
        ssh_key_path=None,
    )
    update: dict[str, Any] = {"qemu_network": "tap"}
    if tuned:
        update["qemu_net"] = QemuNetOptions(vhost=True, bus="pci")
        update["qemu_root_disk"] = QemuRootDiskOptions(
            bus="pci", iothread=True, aio="io_uring", qcow2_subclusters=True
        )
    config = config.model_copy(update=update)

    evidence: dict[str, Any] = {"vm_id": config.vm_id, "variant": variant}
    sandbox = Celesto(config, ssh_key_path=ssh_key_path, comm_channel="ssh")
    try:
        sandbox.start(boot_timeout=BOOT_TIMEOUT)
        assert sandbox.status == VMState.RUNNING

        info = sandbox.info
        assert info.pid is not None
        assert info.config.rootfs_path is not None
        evidence["network"] = info.network.model_dump(mode="json") if info.network else None
        evidence["host"] = {
            "vhost_net_fds": _open_vhost_net_fds(info.pid),
            "overlay": _overlay_info(Path(info.config.rootfs_path)),
        }
        evidence["guest"] = {
            "nic_device": _guest(sandbox, "readlink -f /sys/class/net/eth0/device"),
            "root_disk_device": _guest(sandbox, "readlink -f /sys/block/vda/device"),
        }

        # A 1 MiB upload streams through SSH over the NIC under test.
        payload = os.urandom(1024 * 1024)
        upload = tmp_path / "payload.bin"
        upload.write_bytes(payload)
        sandbox.upload_file(str(upload), "/root/payload.bin")
        uploaded = _guest(sandbox, "sha256sum /root/payload.bin").split()[0]
        evidence["upload_sha256_matches"] = uploaded == hashlib.sha256(payload).hexdigest()

        _guest(sandbox, _SMALL_WRITES)
        before = _guest(sandbox, "sha256sum /root/small-writes.bin").split()[0]
        # Re-read from the disk, not the page cache.
        _guest(sandbox, "sync && echo 3 > /proc/sys/vm/drop_caches")
        reread = _guest(sandbox, "sha256sum /root/small-writes.bin").split()[0]
        evidence["small_writes_reread_from_disk"] = before == reread

        sandbox.stop()
        check = subprocess.run(
            ["qemu-img", "check", "--output=json", str(info.config.rootfs_path)],
            check=False,
            capture_output=True,
            text=True,
        )
        evidence["overlay_check_exit"] = check.returncode

        try:
            sandbox.start(boot_timeout=BOOT_TIMEOUT)
            restarted = sandbox.info
            evidence["restart_network"] = (
                restarted.network.model_dump(mode="json") if restarted.network else None
            )
            after = _guest(sandbox, "sha256sum /root/small-writes.bin").split()[0]
            evidence["small_writes_survive_restart"] = before == after
        except Exception as error:
            evidence["restart_error"] = f"{type(error).__name__}: {error}"
            evidence["restart_console_tail"] = _console_tail(sandbox)
            raise
    finally:
        try:
            artifact = _artifact_dir(tmp_path) / f"qemu-io-{variant}.json"
            artifact.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
            print(f"QEMU I/O evidence: {artifact}")
        finally:
            # Clean up even if the evidence cannot be written.
            with suppress(Exception):
                sandbox.stop()
            with suppress(Exception):
                sandbox.delete()

    assert evidence["upload_sha256_matches"], evidence
    assert evidence["small_writes_reread_from_disk"], evidence
    assert evidence["overlay_check_exit"] == 0, evidence
    assert evidence["small_writes_survive_restart"], evidence
    if not tuned:
        return
    assert evidence["host"]["vhost_net_fds"] > 0, evidence
    assert evidence["host"]["overlay"] == {
        "format": "qcow2",
        "cluster_size": 128 * 1024,
        "extended_l2": True,
    }, evidence
    assert "/pci" in evidence["guest"]["nic_device"], evidence
    assert "/pci" in evidence["guest"]["root_disk_device"], evidence

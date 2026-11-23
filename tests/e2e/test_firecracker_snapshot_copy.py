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

"""End-to-end check that Firecracker snapshots copy the disk with the fast copy.

Firecracker ``disk`` and ``full`` snapshots pause the sandbox while its disk is
copied. They use ``clone_or_sparse_copy``: a reflink clone on btrfs/XFS, or a
copy that skips empty space elsewhere. This test boots a real Firecracker
sandbox, takes both kinds of snapshot, restores the disk snapshot, and checks a
marker file survived.

It writes ``firecracker-snapshot-copy.json`` to the test's temporary directory
(and to junit properties) with the copy method, the time the sandbox stayed
paused, and the snapshot disk's apparent and allocated sizes.
"""

from __future__ import annotations

import json
import logging
from contextlib import suppress
from pathlib import Path
from typing import Any

import pytest
from _util import BOOT_TIMEOUT, require_backend_available, selected_backend

from celesto import Celesto
from celesto.runtime.backends import BACKEND_FIRECRACKER
from celesto.storage import MemoryStateManager
from celesto.types import SnapshotInfo, SnapshotType

pytestmark = pytest.mark.e2e

_COPY_LOGGER = "celesto.runtime.firecracker"
_MARKER_PATH = "/root/snapshot-copy-marker.txt"
_MARKER = "fast-copy-marker"


def _copy_record(caplog: pytest.LogCaptureFixture, snapshot: SnapshotInfo) -> dict[str, Any]:
    """Return what the runtime logged about copying this snapshot's disk."""
    records = [
        record
        for record in caplog.records
        if record.name == _COPY_LOGGER
        and getattr(record, "snapshot_id", None) == snapshot.snapshot_id
    ]
    assert len(records) == 1, f"expected one disk-copy record for {snapshot.snapshot_id}"
    record = records[0]
    disk = Path(snapshot.artifacts.disk_path).stat()
    return {
        "snapshot_id": snapshot.snapshot_id,
        "snapshot_type": snapshot.snapshot_type.value,
        "copy_method": record.copy_method,
        "copy_seconds": record.copy_seconds,
        "pause_seconds": record.pause_seconds,
        "disk_apparent_bytes": disk.st_size,
        "disk_allocated_bytes": disk.st_blocks * 512,
    }


def test_firecracker_snapshots_use_fast_disk_copy(
    request: pytest.FixtureRequest,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    record_property: Any,
) -> None:
    """Disk and full snapshots record the fast copy; the disk snapshot restores."""
    selected = selected_backend(request.config)
    if selected not in ("all", BACKEND_FIRECRACKER):
        pytest.skip(
            f"End-to-end tests for '{BACKEND_FIRECRACKER}' are skipped because this run "
            f"selected '{selected}'; rerun all backends with: pytest tests/e2e."
        )
    require_backend_available(
        BACKEND_FIRECRACKER, request.config, sandbox_name="snapshot-copy-firecracker"
    )
    caplog.set_level(logging.DEBUG, logger=_COPY_LOGGER)

    # from_snapshot needs the same inventory and data_dir as the source computer.
    data_dir = tmp_path / "data"
    inventory = MemoryStateManager(data_dir)
    sandbox = Celesto(
        backend=BACKEND_FIRECRACKER,
        os="alpine",
        comm_channel="ssh",
        data_dir=data_dir,
        state_manager=inventory,
    )
    restored: Celesto | None = None
    evidence: dict[str, Any] = {"backend": BACKEND_FIRECRACKER}
    try:
        sandbox.start(boot_timeout=BOOT_TIMEOUT)
        write = sandbox.run(f"echo {_MARKER} > {_MARKER_PATH} && sync")
        assert write.exit_code == 0

        full = sandbox.snapshot(snapshot_type=SnapshotType.FULL, resume_source=True)
        evidence["full"] = _copy_record(caplog, full)

        disk = sandbox.snapshot(snapshot_type=SnapshotType.DISK)
        evidence["disk"] = _copy_record(caplog, disk)

        sandbox.stop()
        sandbox.delete()

        restored = Celesto.from_snapshot(
            disk.snapshot_id,
            backend=BACKEND_FIRECRACKER,
            resume_vm=True,
            data_dir=data_dir,
            state_manager=inventory,
        )
        result = restored.run(f"cat {_MARKER_PATH}")
        evidence["restored_marker"] = result.stdout.strip()
        assert result.exit_code == 0
        assert result.stdout.strip() == _MARKER
    finally:
        artifact = tmp_path / "firecracker-snapshot-copy.json"
        artifact.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
        record_property("snapshot_copy_artifact", str(artifact))
        record_property("snapshot_copy", json.dumps(evidence, sort_keys=True))
        # restored reuses the source vm_id, so deleting either removes the VM.
        target = restored or sandbox
        with suppress(Exception):
            target.stop()
        with suppress(Exception):
            target.delete()

    for kind in ("full", "disk"):
        entry = evidence[kind]
        assert entry["copy_method"], f"{kind} snapshot did not record a copy method"
        assert entry["pause_seconds"] is not None and entry["pause_seconds"] >= 0

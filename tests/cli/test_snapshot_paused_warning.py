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

"""Warn when ``celesto sandbox snapshot create`` leaves its sandbox paused.

The end-to-end suite cannot reliably make a resume fail, so this isolated
test runs the real CLI, SDK and manager against a fake Firecracker API whose
resume call fails. Failure modes it must catch:

- The warning is missing from human output.
- The warning is missing from JSON ``warnings``.
- The snapshot is reported as failed even though it succeeded.
- The recovery command names the wrong sandbox.
- The warning is saved with the snapshot and shows up again on later reads.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from celesto.cli.main import main
from celesto.cli.service import CLIService
from celesto.exceptions import CelestoError
from celesto.types import VMConfig, VMState

SANDBOX = "sbx-einstein"
EXPECTED_WARNING = (
    "Sandbox 'sbx-einstein' stayed paused after the snapshot. "
    "Run 'celesto sandbox resume sbx-einstein' to continue it."
)


@pytest.fixture
def running_sandbox(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CLIService:
    """Record a running Firecracker sandbox in a throwaway CLI inventory."""
    data_dir = tmp_path / "data"
    monkeypatch.setenv("CELESTO_DATA_DIR", str(data_dir))
    service = CLIService(data_dir)

    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.ext4"
    kernel.touch()
    rootfs.write_text("rootfs-data")
    manager = service.manager(data_dir=data_dir, backend="firecracker")
    manager.network = MagicMock()
    manager.network.host_ip = "172.16.0.1"
    manager.network.generate_mac.return_value = "AA:FC:00:00:00:01"
    manager.create(
        VMConfig(vm_id=SANDBOX, vcpu_count=1, memory=512, kernel_path=kernel, rootfs_path=rootfs)
    )
    (data_dir / "disks" / f"{SANDBOX}.ext4").write_text("managed-disk")
    socket_path = tmp_path / "fc.sock"
    socket_path.touch()
    manager.state.update_vm(
        SANDBOX, status=VMState.RUNNING, pid=12345, control_socket_path=socket_path
    )
    return service


def _snapshot(*extra_args: str, resume_fails: bool = True) -> tuple[int, MagicMock]:
    """Run ``snapshot create`` against a fake Firecracker API."""

    def _write_snapshot(snapshot_path: Path, mem_path: Path, snapshot_type: str = "Full") -> None:
        snapshot_path.write_text("vmstate")
        mem_path.write_text("memory")

    with patch("celesto.runtime.firecracker.FirecrackerClient") as client_cls:
        client = MagicMock()
        client.create_snapshot.side_effect = _write_snapshot
        if resume_fails:
            client.resume_vm.side_effect = CelestoError("resume failed")
        client_cls.return_value = client
        ret = main(
            [
                "sandbox",
                "snapshot",
                "create",
                SANDBOX,
                "--snapshot-id",
                "snap-001",
                "--resume-source",
                *extra_args,
            ]
        )
    return ret, client


def test_snapshot_create_warns_in_human_output(
    running_sandbox: CLIService, capsys: pytest.CaptureFixture[str]
) -> None:
    """Human output reports success and the exact resume command."""
    ret, client = _snapshot()

    captured = capsys.readouterr()
    assert ret == 0, captured.out + captured.err
    client.resume_vm.assert_called_once()
    out = " ".join(captured.out.split())
    assert f"Created snapshot 'snap-001' from VM '{SANDBOX}'." in out
    assert EXPECTED_WARNING in out


def test_snapshot_create_json_lists_warning(
    running_sandbox: CLIService, capsys: pytest.CaptureFixture[str]
) -> None:
    """JSON reports success and the warning in ``warnings``; the warning isn't saved."""
    ret, _ = _snapshot("--json")

    captured = capsys.readouterr()
    assert ret == 0, captured.out + captured.err
    payload = json.loads(captured.out)
    assert payload["ok"] is True
    assert payload["error"] is None
    assert payload["data"]["snapshot"]["snapshot_id"] == "snap-001"
    assert payload["data"]["snapshot"]["vm_id"] == SANDBOX
    assert payload["data"]["warnings"] == [EXPECTED_WARNING]

    with running_sandbox.manager() as sdk:
        assert sdk.get(SANDBOX).status == VMState.PAUSED
        assert sdk.get_snapshot("snap-001").warnings == ()


def test_snapshot_create_json_has_no_warnings_when_resume_succeeds(
    running_sandbox: CLIService, capsys: pytest.CaptureFixture[str]
) -> None:
    """A clean snapshot carries an empty ``warnings`` list."""
    ret, _ = _snapshot("--json", resume_fails=False)

    captured = capsys.readouterr()
    assert ret == 0, captured.out + captured.err
    assert json.loads(captured.out)["data"]["warnings"] == []

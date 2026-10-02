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

"""Recording a sandbox's identity when it becomes ready.

``tests/e2e/test_sandbox_identity.py`` proves the happy path on real
sandboxes. These tests cover what a real boot cannot easily produce, written
as failure modes before the code:

1. The guest read fails or times out, and that failure breaks or delays
   ``wait_for_ready`` (and so ``create`` and ``start``).
2. A record already exists for the current instance ID, and every readiness
   still runs a guest command.
3. A sandbox from an older image (no marker) is read on every readiness
   because nothing is ever recorded for it.
4. The guest reports an instance ID other than the one Celesto booted it
   with, and that stale identity is recorded as current.
5. A sandbox created before instance IDs existed runs a guest command.
6. The internal read fires the user's ``on_pre_run`` callbacks, which could
   block it or show the user a command they never ran.
7. The fingerprint is not in OpenSSH's ``SHA256:...`` format, so it never
   matches what ``ssh-keygen -l`` shows.
8. Deleting a sandbox keeps its identity record, so a new sandbox with the
   same name inherits it.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from celesto.cli._sqlite import SQLiteStateManager
from celesto.comm.rust_http_vsock_channel import RustHttpVsockChannel
from celesto.exceptions import OperationTimeoutError
from celesto.facade import Celesto
from celesto.guest_identity import ssh_host_key_fingerprint
from celesto.storage._memory import MemoryStateManager
from celesto.types import CommandResult, GuestOS, VMConfig, VMIdentity, VMInfo, VMState, VsockConfig

_INSTANCE_ID = "0123456789abcdef0123456789abcdef"
_MACHINE_ID = "fedcba9876543210fedcba9876543210"
_HOST_KEY = (
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBxbQZ0ZKgVf2Lw4GJqRCGJw7uYXq1mIuKyhCqzQZ0vV root@celesto"
)


def _guest_output(
    *, marker: bool = True, instance_id: str = _INSTANCE_ID, host_key: str = _HOST_KEY
) -> str:
    lines = [
        f"supports_instance_id={'1' if marker else ''}",
        f"instance_id={instance_id if marker else ''}",
        f"machine_id={_MACHINE_ID}",
        f"host_key={host_key}",
    ]
    return "\n".join(lines) + "\n"


class _Guest:
    """Answers the vsock agent's ``/exec`` like a booted sandbox would."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.output = _guest_output()
        self.error: Exception | None = None

    def run(self, channel, command, timeout=30, shell="login"):  # noqa: ANN001
        self.calls.append(command)
        if self.error is not None:
            raise self.error
        return CommandResult(exit_code=0, stdout=self.output, stderr="")


@pytest.fixture
def guest(monkeypatch: pytest.MonkeyPatch) -> _Guest:
    fake = _Guest()
    monkeypatch.setattr("celesto.comm.select.host_supports_vsock", lambda: True)
    monkeypatch.setattr(
        RustHttpVsockChannel, "wait_ready", lambda self, timeout=60.0, interval=0.1: None
    )
    monkeypatch.setattr(
        RustHttpVsockChannel,
        "run",
        lambda self, command, timeout=30, shell="login": fake.run(self, command, timeout, shell),
    )
    return fake


def _sandbox(tmp_path: Path, state, *, instance_id: str | None = _INSTANCE_ID) -> Celesto:  # noqa: ANN001
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.ext4"
    kernel.touch()
    rootfs.touch()
    config = VMConfig(
        vm_id="vm1",
        kernel_path=kernel,
        rootfs_path=rootfs,
        backend="qemu",
        guest_os=GuestOS.ALPINE,
        boot_args="console=ttyS0 reboot=k panic=1 init=/init",
        comm_channel="vsock",
        vsock=VsockConfig(guest_cid=5),
        instance_id=instance_id,
    )
    if not _exists(state, "vm1"):
        state.create_vm(config)
    info = VMInfo(vm_id="vm1", status=VMState.RUNNING, config=config)

    vm = Celesto.__new__(Celesto)
    vm._comm_channel_request = "vsock"
    vm._vm_id = "vm1"
    vm._control_channel = None
    vm._control_ready = False
    vm._callbacks = MagicMock()
    vm._ssh = None
    vm._ssh_ready = False
    vm._info = info
    vm._sdk = MagicMock()
    vm._sdk.get.return_value = info
    vm._sdk.state = state
    return vm


def _exists(state, vm_id: str) -> bool:  # noqa: ANN001
    try:
        state.get_vm(vm_id)
    except Exception:
        return False
    return True


@pytest.fixture(params=["memory", "sqlite"])
def state(request: pytest.FixtureRequest, tmp_path: Path):  # noqa: ANN201
    if request.param == "memory":
        return MemoryStateManager(tmp_path / "data")
    return SQLiteStateManager(tmp_path / "celesto.db")


def test_ready_records_identity_the_guest_reports(tmp_path: Path, state, guest: _Guest) -> None:  # noqa: ANN001
    vm = _sandbox(tmp_path, state)

    vm.wait_for_ready(timeout=5)

    record = vm._recorded_identity()
    assert record is not None
    assert record.instance_id == _INSTANCE_ID
    assert record.machine_id == _MACHINE_ID
    assert record.ssh_host_key_fingerprint == ssh_host_key_fingerprint(_HOST_KEY)


def test_failed_guest_read_does_not_fail_readiness(tmp_path: Path, state, guest: _Guest) -> None:  # noqa: ANN001
    guest.error = OperationTimeoutError("identity read", 5)
    vm = _sandbox(tmp_path, state)

    vm.wait_for_ready(timeout=5)

    assert vm._control_ready is True
    assert vm._recorded_identity() is None


def test_existing_record_skips_the_guest_read(tmp_path: Path, state, guest: _Guest) -> None:  # noqa: ANN001
    _sandbox(tmp_path, state).wait_for_ready(timeout=5)
    guest.calls.clear()

    _sandbox(tmp_path, state).wait_for_ready(timeout=5)

    assert guest.calls == []


def test_older_image_is_recorded_once_without_instance_id(
    tmp_path: Path,
    state,  # noqa: ANN001
    guest: _Guest,
) -> None:
    guest.output = _guest_output(marker=False)
    vm = _sandbox(tmp_path, state)
    vm.wait_for_ready(timeout=5)

    record = vm._recorded_identity()
    assert record is not None
    assert record.instance_id is None
    guest.calls.clear()
    _sandbox(tmp_path, state).wait_for_ready(timeout=5)
    assert guest.calls == []


def test_stale_instance_id_is_not_recorded(tmp_path: Path, state, guest: _Guest) -> None:  # noqa: ANN001
    guest.output = _guest_output(instance_id="ffffffffffffffffffffffffffffffff")
    vm = _sandbox(tmp_path, state)

    vm.wait_for_ready(timeout=5)

    assert vm._recorded_identity() is None


def test_sandbox_without_instance_id_runs_no_guest_command(
    tmp_path: Path,
    state,  # noqa: ANN001
    guest: _Guest,
) -> None:
    vm = _sandbox(tmp_path, state, instance_id=None)

    vm.wait_for_ready(timeout=5)

    assert guest.calls == []
    assert vm._recorded_identity() is None


def test_identity_read_does_not_fire_user_run_callbacks(
    tmp_path: Path,
    state,  # noqa: ANN001
    guest: _Guest,
) -> None:
    vm = _sandbox(tmp_path, state)

    vm.wait_for_ready(timeout=5)

    assert guest.calls
    vm._callbacks.fire.assert_not_called()


@pytest.mark.skipif(shutil.which("ssh-keygen") is None, reason="needs ssh-keygen")
def test_fingerprint_matches_ssh_keygen(tmp_path: Path) -> None:
    key = tmp_path / "key"
    subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)], check=True)
    expected = subprocess.run(
        ["ssh-keygen", "-lf", f"{key}.pub"], check=True, capture_output=True, text=True
    ).stdout.split()[1]

    assert ssh_host_key_fingerprint(Path(f"{key}.pub").read_text()) == expected


def test_deleting_a_sandbox_drops_its_identity(tmp_path: Path, state) -> None:  # noqa: ANN001
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.ext4"
    kernel.touch()
    rootfs.touch()
    config = VMConfig(vm_id="vm1", kernel_path=kernel, rootfs_path=rootfs)
    state.create_vm(config)
    state.record_vm_identity(
        "vm1",
        VMIdentity(
            instance_id=_INSTANCE_ID,
            ssh_host_key_fingerprint="SHA256:abc",
            machine_id=_MACHINE_ID,
        ),
    )

    state.delete_vm("vm1")
    state.create_vm(config)

    assert state.get_vm_identity("vm1") is None

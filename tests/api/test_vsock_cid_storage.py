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

"""Tests for per-VM vsock CID allocation (mirrors the SSH-port pool)."""

from pathlib import Path

import pytest

from celesto.cli.state import SQLiteStateManager as StateManager
from celesto.storage._base import VSOCK_CID_START
from celesto.storage._memory import MemoryStateManager
from celesto.types import GuestOS, VMConfig


def _make_config(tmp_path: Path, vm_id: str) -> VMConfig:
    rootfs = tmp_path / f"{vm_id}.ext4"
    rootfs.write_bytes(b"rootfs")
    kernel = tmp_path / f"{vm_id}.bin"
    kernel.write_bytes(b"kernel")
    return VMConfig(
        vm_id=vm_id,
        kernel_path=kernel,
        rootfs_path=rootfs,
        guest_os=GuestOS.ALPINE,
    )


@pytest.fixture
def state(tmp_path: Path) -> StateManager:
    return StateManager(tmp_path / "state.db")


def test_reserve_vsock_cid_starts_at_pool_start(state: StateManager, tmp_path: Path) -> None:
    state.create_vm(_make_config(tmp_path, "vm-a"))
    cid = state.reserve_vsock_cid("vm-a")
    assert cid == VSOCK_CID_START
    assert state.get_vsock_cid("vm-a") == VSOCK_CID_START


def test_reserve_is_idempotent(state: StateManager, tmp_path: Path) -> None:
    state.create_vm(_make_config(tmp_path, "vm-a"))
    first = state.reserve_vsock_cid("vm-a")
    second = state.reserve_vsock_cid("vm-a")
    assert first == second


def test_distinct_vms_get_distinct_cids(state: StateManager, tmp_path: Path) -> None:
    state.create_vm(_make_config(tmp_path, "vm-a"))
    state.create_vm(_make_config(tmp_path, "vm-b"))
    cid_a = state.reserve_vsock_cid("vm-a")
    cid_b = state.reserve_vsock_cid("vm-b")
    assert cid_a != cid_b


def test_released_cid_is_not_given_out_again_at_once(state: StateManager, tmp_path: Path) -> None:
    """A deleted VM's QEMU can hold its CID in the kernel for seconds after the
    delete. Rotation gives the next VM a different CID, so it cannot collide."""
    state.create_vm(_make_config(tmp_path, "vm-a"))
    cid = state.reserve_vsock_cid("vm-a")
    state.release_vsock_cid("vm-a")
    assert state.get_vsock_cid("vm-a") is None

    state.create_vm(_make_config(tmp_path, "vm-b"))
    assert state.reserve_vsock_cid("vm-b") == cid + 1


def test_rotation_continues_in_a_new_state_manager(tmp_path: Path) -> None:
    """The pool agent opens a new state manager for each command, so the
    rotation position must be stored in the database, not in memory."""
    first = StateManager(tmp_path / "state.db")
    first.create_vm(_make_config(tmp_path, "vm-a"))
    cid = first.reserve_vsock_cid("vm-a")
    first.release_vsock_cid("vm-a")

    second = StateManager(tmp_path / "state.db")
    second.create_vm(_make_config(tmp_path, "vm-b"))
    assert second.reserve_vsock_cid("vm-b") == cid + 1


def test_rotation_wraps_to_pool_start_and_skips_cids_in_use(
    state: StateManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("celesto.storage._base.VSOCK_CID_END", VSOCK_CID_START + 2)
    for vm_id in ("vm-a", "vm-b", "vm-c"):
        state.create_vm(_make_config(tmp_path, vm_id))
        state.reserve_vsock_cid(vm_id)
    # The pool is full. Free the middle CID: the next VM wraps past the
    # still-used first CID and gets the freed one.
    state.release_vsock_cid("vm-b")

    state.create_vm(_make_config(tmp_path, "vm-d"))
    assert state.reserve_vsock_cid("vm-d") == VSOCK_CID_START + 1


def test_reserve_skips_excluded_cids(state: StateManager, tmp_path: Path) -> None:
    """Callers exclude CIDs that the kernel still holds (live QEMU processes,
    or a CID that QEMU just failed to bind)."""
    state.create_vm(_make_config(tmp_path, "vm-a"))
    excluded = {VSOCK_CID_START, VSOCK_CID_START + 1}
    assert state.reserve_vsock_cid("vm-a", exclude=excluded) == VSOCK_CID_START + 2


def test_explicit_cid_does_not_move_rotation(state: StateManager, tmp_path: Path) -> None:
    state.create_vm(_make_config(tmp_path, "vm-a"))
    state.reserve_vsock_cid("vm-a", guest_cid=42)

    state.create_vm(_make_config(tmp_path, "vm-b"))
    assert state.reserve_vsock_cid("vm-b") == VSOCK_CID_START


def test_memory_state_rotates_cids(tmp_path: Path) -> None:
    memory = MemoryStateManager(tmp_path)
    memory.create_vm(_make_config(tmp_path, "vm-a"))
    cid = memory.reserve_vsock_cid("vm-a")
    memory.release_vsock_cid("vm-a")

    memory.create_vm(_make_config(tmp_path, "vm-b"))
    assert memory.reserve_vsock_cid("vm-b") == cid + 1
    memory.create_vm(_make_config(tmp_path, "vm-c"))
    assert memory.reserve_vsock_cid("vm-c", exclude={cid + 2}) == cid + 3


def test_explicit_cid_request_for_restore(state: StateManager, tmp_path: Path) -> None:
    state.create_vm(_make_config(tmp_path, "vm-a"))
    cid = state.reserve_vsock_cid("vm-a", guest_cid=42)
    assert cid == 42
    assert state.get_vsock_cid("vm-a") == 42


def test_delete_vm_cascades_cid(state: StateManager, tmp_path: Path) -> None:
    state.create_vm(_make_config(tmp_path, "vm-a"))
    state.reserve_vsock_cid("vm-a")
    state.delete_vm("vm-a")
    assert state.get_vsock_cid("vm-a") is None

# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""Per-computer credential-protection version in the host state DB (D-21).

Isolated test, kept because the end-to-end start tests cannot cheaply reach
an upgraded database or a second state-manager process. Failure modes written
before the code:

1. A database from the previous release (``vms`` table without the new
   column) fails to open, or its computers look already protected, so the
   D-21 cleanup never runs.
2. Computers created by this release look unprotected, so D-21 runs on a
   fresh computer and prints a bogus message.
3. The in-memory backend behaves differently from SQLite.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from celesto.cli.state import SQLiteStateManager
from celesto.credentials.store import PROTECTION_VERSION
from celesto.storage._memory import MemoryStateManager
from celesto.types import VMConfig


def _config(tmp_path: Path, vm_id: str) -> VMConfig:
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.ext4"
    kernel.touch()
    rootfs.touch()
    return VMConfig(vm_id=vm_id, kernel_path=kernel, rootfs_path=rootfs)


@pytest.fixture(params=["sqlite", "memory"])
def make_state(request: pytest.FixtureRequest, tmp_path: Path):
    if request.param == "sqlite":
        return lambda: SQLiteStateManager(tmp_path / "state.db")
    memory = MemoryStateManager(tmp_path)
    return lambda: memory


def test_new_sandboxes_are_protected_and_version_can_be_raised(make_state, tmp_path) -> None:
    state = make_state()
    state.create_vm(_config(tmp_path, "w2-a"))
    assert state.get_credential_protection("w2-a") == PROTECTION_VERSION
    state.set_credential_protection("w2-a", PROTECTION_VERSION + 1)
    assert make_state().get_credential_protection("w2-a") == PROTECTION_VERSION + 1


def test_sandboxes_from_the_previous_release_read_as_unprotected(tmp_path: Path) -> None:
    db = tmp_path / "state.db"
    # Shape of the previous release's vms table: no credential column.
    old = SQLiteStateManager(db)
    old.create_vm(_config(tmp_path, "w2-old"))
    with sqlite3.connect(db) as conn:
        conn.execute("ALTER TABLE vms DROP COLUMN credential_protection")

    upgraded = SQLiteStateManager(db)
    assert upgraded.get_credential_protection("w2-old") == 0
    upgraded.set_credential_protection("w2-old", PROTECTION_VERSION)
    assert SQLiteStateManager(db).get_credential_protection("w2-old") == PROTECTION_VERSION

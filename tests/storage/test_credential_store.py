# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""Per-sandbox credential state in the host state DB (D-05, D-09, D-17).

Isolated test, kept because the end-to-end start tests cannot cheaply reach
an upgraded database or a second state-manager process. Failure modes written
before the code:

1. Placeholders are not persisted, so a new state manager (the next CLI
   command) creates new ones and the guest files from the last start stop
   matching.
2. Saving a second batch of placeholders drops names saved earlier.
3. One sandbox reads another sandbox's placeholders.
4. Deleting a sandbox leaves its placeholders behind, so a new sandbox with
   the same name inherits them.
5. A database from the previous release (``vms`` table without the new
   column) fails to open, or its sandboxes look already protected, so the
   D-17 cleanup never runs.
6. Sandboxes created by this release look unprotected, so D-17 runs on a
   fresh sandbox and prints a bogus message.
7. The in-memory backend behaves differently from SQLite.
8. A real value is written: the store must only ever hold placeholders, which
   is a property of the callers; here we only check that the DB holds exactly
   what was saved and nothing else.
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


def test_placeholders_persist_merge_and_stay_per_sandbox(make_state, tmp_path: Path) -> None:
    state = make_state()
    state.create_vm(_config(tmp_path, "w2-a"))
    state.create_vm(_config(tmp_path, "w2-b"))

    state.save_credential_placeholders("w2-a", {"OPENAI_API_KEY": "sk-proj-AAA"})
    state.save_credential_placeholders("w2-a", {"GITHUB_TOKEN": "gho_BBB"})
    state.save_credential_placeholders("w2-b", {"OPENAI_API_KEY": "sk-proj-CCC"})

    reopened = make_state()
    assert reopened.get_credential_placeholders("w2-a") == {
        "OPENAI_API_KEY": "sk-proj-AAA",
        "GITHUB_TOKEN": "gho_BBB",
    }
    assert reopened.get_credential_placeholders("w2-b") == {"OPENAI_API_KEY": "sk-proj-CCC"}
    assert reopened.get_credential_placeholders("w2-missing") == {}


def test_deleting_a_sandbox_forgets_its_placeholders(make_state, tmp_path: Path) -> None:
    state = make_state()
    state.create_vm(_config(tmp_path, "w2-a"))
    state.save_credential_placeholders("w2-a", {"OPENAI_API_KEY": "sk-proj-AAA"})
    state.delete_vm("w2-a")
    state.create_vm(_config(tmp_path, "w2-a"))
    assert state.get_credential_placeholders("w2-a") == {}


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
        conn.execute("DROP TABLE credential_placeholders")

    upgraded = SQLiteStateManager(db)
    assert upgraded.get_credential_protection("w2-old") == 0
    upgraded.save_credential_placeholders("w2-old", {"OPENAI_API_KEY": "sk-proj-AAA"})
    upgraded.set_credential_protection("w2-old", PROTECTION_VERSION)
    assert SQLiteStateManager(db).get_credential_protection("w2-old") == PROTECTION_VERSION

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

"""The ``/proc`` fallback that decides whether a kept disk is still open.

Kept in isolation because the end-to-end tests run on macOS, where ``lsof``
always answers, so they never reach this Linux-only path. Ways it can fail:

1. A process owned by the disk's owner holds the disk open -> must say open.
2. That process's fd list cannot be read -> must say unknown, not "free",
   or a crashed script's disk is shared with its still-running computer.
3. A process exits mid-scan -> must be skipped, not turn the answer unknown.
4. Every readable process is clear -> must say free, so crash recovery works.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from celesto import vm as celesto_vm
from celesto.vm import CelestoManager, _file_open_by_any_process


def _fake_proc(tmp_path: Path) -> tuple[Path, Path]:
    disk = tmp_path / "disks" / "profile.qcow2"
    disk.parent.mkdir()
    disk.write_bytes(b"disk")
    proc = tmp_path / "proc"
    proc.mkdir()
    return proc, disk


def _process(proc: Path, pid: int, *targets: Path) -> Path:
    fd_dir = proc / str(pid) / "fd"
    fd_dir.mkdir(parents=True)
    for number, target in enumerate(targets):
        (fd_dir / str(number)).symlink_to(target)
    return fd_dir


def test_disk_held_open_is_reported_open(tmp_path: Path) -> None:
    proc, disk = _fake_proc(tmp_path)
    _process(proc, 100, tmp_path / "other-file")
    _process(proc, 200, disk)

    assert _file_open_by_any_process(disk, use_lsof=False, proc_root=proc) is True


def test_all_processes_clear_reports_free(tmp_path: Path) -> None:
    proc, disk = _fake_proc(tmp_path)
    _process(proc, 100, tmp_path / "other-file")

    assert _file_open_by_any_process(disk, use_lsof=False, proc_root=proc) is False


@pytest.mark.skipif(os.geteuid() == 0, reason="root can read any directory")
def test_unreadable_process_of_disk_owner_reports_unknown(tmp_path: Path) -> None:
    proc, disk = _fake_proc(tmp_path)
    _process(proc, 100, tmp_path / "other-file")
    hidden = _process(proc, 200, disk)
    hidden.chmod(0)
    try:
        assert _file_open_by_any_process(disk, use_lsof=False, proc_root=proc) is None
    finally:
        hidden.chmod(0o755)


def test_process_that_exits_mid_scan_is_skipped(tmp_path: Path) -> None:
    proc, disk = _fake_proc(tmp_path)
    _process(proc, 100, tmp_path / "other-file")
    # A pid directory without an fd directory is what a process that has
    # just exited looks like.
    (proc / "300").mkdir()

    assert _file_open_by_any_process(disk, use_lsof=False, proc_root=proc) is False


# 5. ``lsof`` exits 1 both for "nobody has it open" and for an error such as a
#    failed stat. Only a clean exit 1 means free.
# 6. A descriptor that cannot be resolved must make the answer unknown, while
#    a descriptor that vanished mid-scan is skipped.
# 7. The scan follows the user that runs the computer, which can differ from
#    the disk's owner when a root script reuses a kept disk.
# 8. Whenever the probe cannot tell, a kept disk is not adopted.


@pytest.mark.skipif(shutil.which("lsof") is None, reason="needs lsof")
def test_lsof_error_reports_unknown(tmp_path: Path) -> None:
    free = tmp_path / "free.qcow2"
    free.write_bytes(b"disk")

    assert _file_open_by_any_process(free) is False
    assert _file_open_by_any_process(tmp_path / "missing.qcow2") is None


@pytest.mark.skipif(os.geteuid() == 0, reason="root can read any directory")
def test_unresolvable_descriptor_reports_unknown(tmp_path: Path) -> None:
    proc, disk = _fake_proc(tmp_path)
    fd_dir = _process(proc, 200, tmp_path / "other-file")
    # Listable but not searchable: the entry is visible, its target is not.
    fd_dir.chmod(0o444)
    try:
        assert _file_open_by_any_process(disk, use_lsof=False, proc_root=proc) is None
    finally:
        fd_dir.chmod(0o755)


def test_descriptor_closed_mid_scan_is_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proc, disk = _fake_proc(tmp_path)
    _process(proc, 200, tmp_path / "other-file", tmp_path / "closing-file")
    readlink = os.readlink

    def closing(entry: str | os.PathLike[str]) -> str:
        if Path(entry).name == "1":
            raise FileNotFoundError(entry)
        return readlink(entry)

    monkeypatch.setattr(os, "readlink", closing)

    assert _file_open_by_any_process(disk, use_lsof=False, proc_root=proc) is False


def test_scan_follows_the_runtime_user(tmp_path: Path) -> None:
    proc, disk = _fake_proc(tmp_path)
    _process(proc, 200, disk)
    me = os.stat(proc / "200").st_uid

    assert (
        _file_open_by_any_process(disk, use_lsof=False, proc_root=proc, runtime_uids={me}) is True
    )
    assert (
        _file_open_by_any_process(disk, use_lsof=False, proc_root=proc, runtime_uids={me + 1})
        is False
    )


def _dead_pid() -> int:
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    child.wait()
    return child.pid


@pytest.mark.parametrize(("probe", "adopted"), [(None, False), (True, False), (False, True)])
def test_kept_disk_is_adopted_only_when_probe_says_free(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    probe: bool | None,
    adopted: bool,
) -> None:
    manager = CelestoManager(data_dir=tmp_path / "data", socket_dir=tmp_path / "sockets")
    disk = manager.disk_dir / "profile.qcow2"
    disk.parent.mkdir(parents=True, exist_ok=True)
    disk.write_bytes(b"disk")
    (disk.parent / "profile.qcow2.owner").write_text(
        json.dumps(
            {
                "vm_id": "profile",
                "pid": _dead_pid(),
                "uid": os.geteuid(),
                "keep": True,
                "in_memory_inventory": True,
            }
        )
    )
    monkeypatch.setattr(celesto_vm, "_file_open_by_any_process", lambda *a, **k: probe)

    assert manager._disk_owner_gone_and_kept(disk) is adopted

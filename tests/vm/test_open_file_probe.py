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

import os
from pathlib import Path

import pytest

from celesto.vm import _file_open_by_any_process


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

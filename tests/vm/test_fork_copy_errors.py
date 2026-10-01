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

"""What a fork child reports when copying its disk fails.

A real run copies every disk cleanly, so these tests break the copy at its
outer boundaries: the saved copy disappears, or ``qemu-img`` can't read it,
reports the wrong format, or can't finish re-pointing the copy at its base
image. Failure modes, written before the code:

1. The child's message tells the user to "run the copy again", which is
   not a command.
2. The child's message shows internal file paths.
3. The child's disk or record is left behind after the failure.
4. The other children fail too.

The fork engine, child records and disk copies are real; the start, guest
agent and ``qemu-img`` are replaced (``qemu-img`` by a small script).
"""

from __future__ import annotations

import stat
import sys
from pathlib import Path
from typing import Any

import pytest

from celesto.types import VMState
from celesto.vm import CelestoManager
from tests.vm.test_fork_children import _World, world  # noqa: F401 - fixture

_REAL_CREATE_FROM_DISK = CelestoManager._create_from_disk
_REAL_DELETE_UNLOCKED = CelestoManager._delete_unlocked

_FAILED = "Sandbox 'src-1' couldn't be created and was removed. Run the fork again."

# A stand-in for qemu-img. Every disk is a qcow2 layer on the base image.
# MODE breaks one step once: the first read of the saved copy, or the
# re-pointing of the first child's copy. Later children copy cleanly.
_FAKE_QEMU_IMG = """\
import json, os, sys
MODE = {mode!r}
BASE = {base!r}
ONCE = {once!r}
args = sys.argv[1:]

def first_time():
    if os.path.exists(ONCE):
        return False
    open(ONCE, "w").close()
    return True

if args[0] == "info":
    path = args[-1]
    saved = "/snapshots/" in path
    if path == BASE:
        print(json.dumps({{"format": "raw"}}))
        sys.exit(0)
    broken = saved and MODE in ("unreadable", "wrong-format") and first_time()
    if broken and MODE == "unreadable":
        sys.stderr.write("qemu-img: Could not open the disk\\n")
        sys.exit(1)
    fmt = "raw" if broken else "qcow2"
    print(json.dumps({{"format": fmt, "backing-filename": BASE,
                      "backing-filename-format": "raw"}}))
elif args[0] == "rebase":
    if MODE == "rebase" and "/disks/src-1." in args[-1] and first_time():
        sys.stderr.write("qemu-img: Could not change the backing file\\n")
        sys.exit(1)
else:
    sys.exit(2)
"""


@pytest.fixture
def copying(world: _World, monkeypatch: pytest.MonkeyPatch) -> _World:  # noqa: F811
    # Real child records and disks, so a leftover is visible.
    monkeypatch.setattr(CelestoManager, "_create_from_disk", _REAL_CREATE_FROM_DISK)
    monkeypatch.setattr(CelestoManager, "_delete_unlocked", _REAL_DELETE_UNLOCKED)
    # Userspace networking: no host network devices are made for children.
    monkeypatch.setattr(
        CelestoManager, "_uses_host_tap_networking", staticmethod(lambda config, backend: False)
    )
    return world


def _use_fake_qemu_img(world: _World, monkeypatch: pytest.MonkeyPatch, mode: str) -> None:  # noqa: F811
    base = world.tmp_path / "images" / "base.raw"
    base.parent.mkdir(parents=True)
    base.write_bytes(b"base" * 1024)
    script = world.tmp_path / "qemu-img"
    script.write_text(
        f"#!{sys.executable}\n"
        + _FAKE_QEMU_IMG.format(
            mode=mode, base=str(base.resolve()), once=str(world.tmp_path / "broke-once")
        )
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setattr(CelestoManager, "_find_qemu_img_binary", lambda self: script)


def _assert_only_the_first_child_failed(world: _World, batch: Any) -> None:  # noqa: F811
    results = {child.name: child for child in batch.children}
    assert results["src-1"].ok is False
    assert results["src-1"].error == _FAILED
    assert results["src-2"].ok, results["src-2"].error
    assert sorted(vm.vm_id for vm in world.state.list_vms()) == ["src", "src-2"]
    assert world.manager._instance_disk_paths_for_id("src-1") == []
    assert world.generations() == []


@pytest.mark.parametrize("mode", ["unreadable", "wrong-format"])
def test_a_qemu_child_whose_copy_fails_says_to_run_the_fork_again(
    copying: _World, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    _use_fake_qemu_img(copying, monkeypatch, mode)
    source = copying.add_source("qemu", VMState.STOPPED)

    batch = source._fork_many(2, parallel=1, boot_timeout=30)

    _assert_only_the_first_child_failed(copying, batch)


def test_a_child_whose_saved_copy_is_missing_says_to_run_the_fork_again(
    copying: _World, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_fake_qemu_img(copying, monkeypatch, "none")
    source = copying.add_source("qemu", VMState.STOPPED)
    real = CelestoManager._materialize_rootfs_from_disk

    def materialize(self: CelestoManager, config: Any, disk_path: Path, **kw: Any) -> Any:
        if config.vm_id == "src-1":
            disk_path = disk_path.with_name("gone.qcow2")
        return real(self, config, disk_path, **kw)

    monkeypatch.setattr(CelestoManager, "_materialize_rootfs_from_disk", materialize)

    batch = source._fork_many(2, parallel=1, boot_timeout=30)

    _assert_only_the_first_child_failed(copying, batch)

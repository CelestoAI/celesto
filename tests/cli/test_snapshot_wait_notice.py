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

"""The notice ``stop`` and ``delete`` print while a snapshot or fork runs.

``tests/e2e/test_snapshot_locks.py`` races a real snapshot with ``stop`` and
``delete``. The lock they wait for is also held by forks, which that test
can't run on every host, so this one holds the lock itself and runs the real
CLI. Failure modes, written before the code:

1. The notice says "the snapshot" while a fork holds the lock.
2. The notice lands on stdout and breaks ``--json`` output.
"""

from __future__ import annotations

import fcntl
import json
import threading
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from celesto.cli.main import main
from celesto.cli.service import CLIService
from celesto.types import VMConfig

SANDBOX = "sbx-einstein"
NOTICE = "Waiting for the current snapshot or fork of sbx-einstein to finish…"


@pytest.fixture
def held_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Record a created sandbox and hold its snapshot lock for half a second."""
    data_dir = tmp_path / "data"
    monkeypatch.setenv("CELESTO_DATA_DIR", str(data_dir))
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.ext4"
    kernel.touch()
    rootfs.write_text("rootfs-data")
    manager = CLIService(data_dir).manager(data_dir=data_dir, backend="firecracker")
    manager.network = MagicMock()
    manager.network.host_ip = "172.16.0.1"
    manager.network.generate_mac.return_value = "AA:FC:00:00:00:01"
    manager.create(
        VMConfig(vm_id=SANDBOX, vcpu_count=1, memory=512, kernel_path=kernel, rootfs_path=rootfs)
    )
    lock_path = data_dir / "locks" / f"{SANDBOX}.snapshot.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        release = threading.Timer(0.5, fcntl.flock, (lock.fileno(), fcntl.LOCK_UN))
        release.start()
        try:
            yield
        finally:
            release.join()


@pytest.mark.parametrize("action", ["stop", "delete"])
def test_stop_and_delete_say_they_wait_for_a_snapshot_or_fork(
    held_lock: None, action: str, capsys: pytest.CaptureFixture[str]
) -> None:
    main(["sandbox", action, SANDBOX, "--json"])

    captured = capsys.readouterr()
    assert NOTICE in captured.err
    assert NOTICE not in captured.out
    json.loads(captured.out)

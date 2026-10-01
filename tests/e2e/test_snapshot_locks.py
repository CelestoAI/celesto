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

"""Stop and delete wait for an in-progress snapshot instead of breaking it.

Every step runs through the real ``celesto`` CLI in its own process, the way a
user (or a second agent) would race a snapshot with ``stop`` or ``delete``.
Each test writes a JSON timeline (snapshot start/end, stop or delete
start/end) so a run can be inspected and compared later. Set
``CELESTO_E2E_ARTIFACTS_DIR`` to keep the timelines outside pytest's tmp dir.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from _util import (
    BOOT_TIMEOUT,
    E2E_BACKENDS,
    E2EBackend,
    require_e2e_backend,
)

from celesto.vm import resolve_data_dir

pytestmark = pytest.mark.e2e

# A 1 GiB file makes the disk copy take several seconds, which leaves a wide
# window to start ``stop`` or ``delete`` while the snapshot still runs.
BIG_FILE_BYTES = 1024 * 1024 * 1024
DISK_SIZE_MIB = 3072
# A deadlock must fail the test instead of hanging CI.
COMMAND_TIMEOUT = 300.0
NAME_PREFIX = os.environ.get("CELESTO_E2E_NAME_PREFIX", "e2e")

_CLI = [sys.executable, "-c", "import sys; from celesto.cli.main import main; sys.exit(main())"]


@dataclass
class _Timeline:
    """Wall-clock marks for one race, written out as the test artifact."""

    scenario: str
    backend: str
    sandbox: str
    origin: float = field(default_factory=time.monotonic)
    events: dict[str, float] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)

    def mark(self, event: str) -> None:
        self.events[event] = round(time.monotonic() - self.origin, 3)

    def write(self, directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"snapshot-lock-{self.backend}-{self.scenario}.json"
        payload = {
            "scenario": self.scenario,
            "backend": self.backend,
            "sandbox": self.sandbox,
            "seconds_since_start": self.events,
            **self.details,
        }
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print(f"snapshot lock timeline: {path}")
        return path


class _Background:
    """One CLI command running in its own process, timed from start to exit."""

    def __init__(self, args: list[str], timeline: _Timeline, name: str) -> None:
        timeline.mark(f"{name}_start")
        self._proc = subprocess.Popen(
            [*_CLI, *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self._result: tuple[str, str] | None = None
        self._thread = threading.Thread(target=self._wait, args=(timeline, name), daemon=True)
        self._thread.start()

    def _wait(self, timeline: _Timeline, name: str) -> None:
        self._result = self._proc.communicate()
        timeline.mark(f"{name}_end")

    def running(self) -> bool:
        return self._proc.poll() is None

    def finish(self, timeout: float = COMMAND_TIMEOUT) -> tuple[int, str, str]:
        self._thread.join(timeout)
        if self._thread.is_alive():
            self._proc.kill()
            self._thread.join(10)
            pytest.fail(f"Command did not finish within {timeout:.0f}s: {self._proc.args!r}")
        assert self._result is not None
        return self._proc.returncode, self._result[0], self._result[1]


def _cli(*args: str, timeout: float = COMMAND_TIMEOUT) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            [*_CLI, *args], capture_output=True, text=True, timeout=timeout, check=False
        )
    except subprocess.TimeoutExpired:
        pytest.fail(f"'celesto {' '.join(args)}' did not finish within {timeout:.0f}s")


def _cli_json(*args: str) -> dict[str, Any]:
    result = _cli(*args, "--json")
    payload = json.loads(result.stdout)
    assert payload["ok"], f"'celesto {' '.join(args)}' failed: {payload['error']}"
    return payload["data"]


def _snapshot_lock_held(sandbox: str) -> bool:
    """True while another process holds this sandbox's snapshot lock."""
    import fcntl

    lock_path = resolve_data_dir() / "locks" / f"{sandbox}.snapshot.lock"
    if not lock_path.exists():
        return False
    with lock_path.open("a") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return False


def _wait_for_snapshot_to_hold_lock(sandbox: str, snapshot: _Background) -> None:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if _snapshot_lock_held(sandbox):
            return
        if not snapshot.running():
            code, stdout, stderr = snapshot.finish()
            pytest.fail(f"Snapshot finished before the race began ({code}): {stdout}{stderr}")
        time.sleep(0.05)
    pytest.fail(f"Snapshot of {sandbox} never started")


def _require_backend(backend: E2EBackend, request: pytest.FixtureRequest, sandbox: str) -> None:
    require_e2e_backend(backend, request.config, sandbox_name=sandbox)


def _create_sandbox(backend: E2EBackend, sandbox: str) -> None:
    _cli_json(
        "sandbox",
        "create",
        "--name",
        sandbox,
        "--backend",
        backend,
        "--os",
        "alpine",
        "--comm-channel",
        "ssh",
        "--disk-size",
        str(DISK_SIZE_MIB),
        "--boot-timeout",
        str(BOOT_TIMEOUT),
    )


def _write_big_file(sandbox: str) -> None:
    script = (
        "echo lock-sentinel > /root/sentinel.txt && "
        f"dd if=/dev/urandom of=/root/big.bin bs=1M count={BIG_FILE_BYTES // (1024 * 1024)} "
        "2>/dev/null && sync"
    )
    result = _cli("sandbox", "exec", sandbox, "--", "sh", "-c", script)
    assert result.returncode == 0, result.stdout + result.stderr


def _cleanup(*sandboxes: str) -> None:
    for sandbox in sandboxes:
        with suppress(Exception):
            _cli("sandbox", "delete", sandbox, "--json", timeout=120)


def _artifacts_dir(tmp_path: Path) -> Path:
    configured = os.environ.get("CELESTO_E2E_ARTIFACTS_DIR")
    return Path(configured) if configured else tmp_path / "artifacts"


def _race_snapshot_with(
    action: str, backend: E2EBackend, sandbox: str
) -> tuple[_Timeline, str, tuple[int, str, str]]:
    """Start a disk snapshot, then run ``action`` on the same running sandbox."""
    timeline = _Timeline(scenario=f"{action}-during-snapshot", backend=backend, sandbox=sandbox)
    snapshot_id = f"{sandbox}-snap"
    snapshot = _Background(
        [
            "sandbox",
            "snapshot",
            "create",
            sandbox,
            "--snapshot-id",
            snapshot_id,
            "--snapshot-type",
            "disk",
            "--json",
        ],
        timeline,
        "snapshot",
    )
    _wait_for_snapshot_to_hold_lock(sandbox, snapshot)
    timeline.mark("snapshot_holds_lock")

    other = _Background(["sandbox", action, sandbox, "--json"], timeline, action)
    other_result = other.finish()
    snapshot_code, snapshot_stdout, snapshot_stderr = snapshot.finish()

    timeline.details["snapshot_exit_code"] = snapshot_code
    timeline.details[f"{action}_exit_code"] = other_result[0]
    timeline.details[f"{action}_stderr"] = other_result[2]
    assert snapshot_code == 0, snapshot_stdout + snapshot_stderr
    assert json.loads(snapshot_stdout)["ok"], snapshot_stdout
    return timeline, snapshot_id, other_result


@pytest.mark.parametrize("backend", E2E_BACKENDS, ids=str)
def test_delete_waits_for_snapshot_of_running_sandbox(
    backend: E2EBackend, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    """Delete of a running sandbox waits for its snapshot, which then restores."""
    sandbox = f"{NAME_PREFIX}-lock-del-{uuid4().hex[:6]}"
    _require_backend(backend, request, sandbox)
    try:
        _create_sandbox(backend, sandbox)
        _write_big_file(sandbox)

        timeline, snapshot_id, (code, stdout, stderr) = _race_snapshot_with(
            "delete", backend, sandbox
        )
        try:
            assert code == 0, stdout + stderr
            assert f"Waiting for the snapshot of {sandbox} to finish" in stderr
            # stderr carries the notice so --json output stays parseable.
            assert json.loads(stdout)["ok"]
            assert timeline.events["delete_end"] >= timeline.events["snapshot_end"]

            info = _cli("sandbox", "info", sandbox, "--json")
            assert json.loads(info.stdout)["ok"] is False, "sandbox should be gone"

            restored = _cli_json("sandbox", "snapshot", "restore", snapshot_id, "--resume")
            timeline.details["restored_sandbox"] = restored["vm"]["name"]
            check = _cli(
                "sandbox",
                "exec",
                sandbox,
                "--",
                "sh",
                "-c",
                "cat /root/sentinel.txt && stat -c %s /root/big.bin",
            )
            assert check.returncode == 0, check.stdout + check.stderr
            assert check.stdout.split() == ["lock-sentinel", str(BIG_FILE_BYTES)]
            timeline.details["restored_check"] = check.stdout.split()
        finally:
            timeline.write(_artifacts_dir(tmp_path))
    finally:
        _cleanup(sandbox)
        with suppress(Exception):
            _cli("sandbox", "snapshot", "delete", f"{sandbox}-snap", "--json", timeout=120)


@pytest.mark.parametrize("backend", E2E_BACKENDS, ids=str)
def test_stop_waits_for_snapshot_of_running_sandbox(
    backend: E2EBackend, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    """Stop waits for the snapshot, leaving a complete snapshot and a stopped sandbox."""
    sandbox = f"{NAME_PREFIX}-lock-stop-{uuid4().hex[:6]}"
    _require_backend(backend, request, sandbox)
    try:
        _create_sandbox(backend, sandbox)
        _write_big_file(sandbox)

        timeline, snapshot_id, (code, stdout, stderr) = _race_snapshot_with(
            "stop", backend, sandbox
        )
        try:
            assert code == 0, stdout + stderr
            assert f"Waiting for the snapshot of {sandbox} to finish" in stderr
            assert json.loads(stdout)["ok"]
            assert timeline.events["stop_end"] >= timeline.events["snapshot_end"]

            info = _cli_json("sandbox", "info", sandbox)
            assert info["vm"]["status"] == "stopped"

            snapshots = _cli_json("sandbox", "snapshot", "list")["snapshots"]
            snapshot = next(item for item in snapshots if item["snapshot_id"] == snapshot_id)
            disk_path = Path(snapshot["artifacts"]["disk_path"])
            assert disk_path.is_file()
            timeline.details["snapshot_disk_bytes"] = disk_path.stat().st_size
        finally:
            timeline.write(_artifacts_dir(tmp_path))
    finally:
        _cleanup(sandbox)
        with suppress(Exception):
            _cli("sandbox", "snapshot", "delete", f"{sandbox}-snap", "--json", timeout=120)


@pytest.mark.parametrize("backend", E2E_BACKENDS, ids=str)
def test_delete_of_running_sandbox_without_snapshot_does_not_wait(
    backend: E2EBackend, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    """Delete takes the snapshot lock once; a running sandbox must not deadlock."""
    sandbox = f"{NAME_PREFIX}-lock-plain-{uuid4().hex[:6]}"
    _require_backend(backend, request, sandbox)
    timeline = _Timeline(scenario="delete-without-snapshot", backend=backend, sandbox=sandbox)
    try:
        _create_sandbox(backend, sandbox)
        timeline.mark("delete_start")
        result = _cli("sandbox", "delete", sandbox, "--json", timeout=120)
        timeline.mark("delete_end")
        timeline.details["delete_stderr"] = result.stderr
        assert result.returncode == 0, result.stdout + result.stderr
        assert json.loads(result.stdout)["ok"]
        assert "Waiting for the snapshot" not in result.stderr

        info = _cli("sandbox", "info", sandbox, "--json")
        assert json.loads(info.stdout)["ok"] is False, "sandbox should be gone"
    finally:
        timeline.write(_artifacts_dir(tmp_path))
        _cleanup(sandbox)

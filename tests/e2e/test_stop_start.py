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

"""Files written right before ``celesto computer stop`` survive ``start`` (issue #668).

Drives the real CLI the way an agent script does: write files, stop at once,
start again, and check every file is still there. Each round writes to the
computer's own disk (``/root``) and to a shared folder (``/workspace``). The
shared folder runs in both modes, because they keep changes in different places:

- read-only (the default): changes stay inside the computer, on its disk;
- writable (``--writable-mounts``): changes must reach this machine's folder.

The test writes a JSON report of every round to ``CELESTO_E2E_ARTIFACT_DIR``
(or pytest's temporary folder) so a run can be checked after the fact.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import uuid
from contextlib import suppress
from pathlib import Path

import pytest
from _util import BOOT_TIMEOUT, _qemu_binary_available, require_backend_available

from celesto.runtime.backends import BACKEND_QEMU

pytestmark = pytest.mark.e2e

ROUNDS = 3
CLI = str(Path(sys.executable).parent / "celesto")


def _celesto(*args: str, timeout: float = BOOT_TIMEOUT + 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [CLI, *args], capture_output=True, text=True, timeout=timeout, check=False
    )


def _require_qemu(config: pytest.Config) -> None:
    # The bug was reported on macOS, where QEMU uses Hypervisor.framework
    # instead of /dev/kvm, so do not demand KVM there.
    if platform.system() == "Darwin" and _qemu_binary_available():
        return
    require_backend_available(BACKEND_QEMU, config, sandbox_name="stop-start")


@pytest.mark.parametrize("writable", [False, True], ids=["read-only-folder", "writable-folder"])
def test_stop_then_start_keeps_files_written_just_before_stop(
    writable: bool, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    _require_qemu(request.config)
    artifact_dir = Path(os.environ.get("CELESTO_E2E_ARTIFACT_DIR", tmp_path))
    artifact_dir.mkdir(parents=True, exist_ok=True)
    mode = "writable" if writable else "read-only"
    report_path = artifact_dir / f"stop-start-{mode}-report.json"

    shared = tmp_path / "shared"
    shared.mkdir()
    name = f"e2e-stop-start-{uuid.uuid4().hex[:8]}"
    rounds: list[dict[str, object]] = []
    report = {"computer": name, "issue": 668, "shared_folder": mode, "rounds": rounds}

    created = _celesto(
        "computer", "create",
        "--name", name,
        "--backend", "qemu",
        "--os", "ubuntu",
        "--mount", f"{shared}:/workspace",
        "--boot-timeout", str(BOOT_TIMEOUT),
        *(["--writable-mounts"] if writable else []),
    )  # fmt: skip
    assert created.returncode == 0, created.stderr or created.stdout
    try:
        for round_number in range(1, ROUNDS + 1):
            token = f"round-{round_number}-{uuid.uuid4().hex[:8]}"
            files = {
                "computer disk": f"/root/stop-{round_number}.txt",
                f"{mode} shared folder": f"/workspace/stop-{round_number}.txt",
            }
            write = _celesto(
                "computer", "exec", name, "--",
                "sh", "-c", " && ".join(f"echo {token} > {path}" for path in files.values()),
            )  # fmt: skip
            assert write.returncode == 0, write.stderr

            stop = _celesto("computer", "stop", name)
            assert stop.returncode == 0, stop.stderr or stop.stdout
            start = _celesto("computer", "start", name)
            assert start.returncode == 0, start.stderr or start.stdout

            survived = {}
            for place, path in files.items():
                read = _celesto("computer", "exec", name, "--", "cat", path)
                survived[place] = read.returncode == 0 and read.stdout.strip() == token
            if writable:
                # A writable folder's changes must also land on this machine.
                host_copy = shared / f"stop-{round_number}.txt"
                survived["this machine's folder"] = (
                    host_copy.exists() and host_copy.read_text().strip() == token
                )
            rounds.append({"round": round_number, "token": token, "kept": survived})
            report_path.write_text(json.dumps(report, indent=2) + "\n")

            lost = [place for place, kept in survived.items() if not kept]
            assert not lost, (
                f"round {round_number}: stop lost files on the {', '.join(lost)}; "
                f"report: {report_path}"
            )
    finally:
        with suppress(Exception):
            _celesto("computer", "delete", name, "--force")
        print(f"stop/start report: {report_path}")

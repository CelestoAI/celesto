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

"""``celesto sandbox fork`` and ``vm.fork()`` through the real user paths.

The CLI test runs the real ``celesto`` command against a locally built Alpine
image and walks the steps in the plan (``docs/designs/sandbox-fork-plan.md``,
PR 6):

1. ``celesto sandbox fork SOURCE --count 3 --json`` exits 0 with three
   children, and each child has the source's files.
2. ``celesto sandbox info CHILD`` shows where the child came from.
3. Forking a paused source exits 1 with the exact message; running the
   command it prints and forking again succeeds (human output).
4. Repeating that fork with the same ``--name`` is refused and creates
   nothing.

The SDK test checks that ``vm.fork()`` returns a working child and that
``vm.fork_many()`` returns a ``ForkBatch``.

Each test writes a JSON artifact (every command, its exit code, stdout and
stderr) to ``CELESTO_E2E_ARTIFACT_DIR`` or pytest's tmp dir.
"""

from __future__ import annotations

import json
import os
import platform
import re
import shlex
import subprocess
import sys
import uuid
from contextlib import suppress
from pathlib import Path
from typing import Any

import pytest
from _util import BOOT_TIMEOUT, E2E_BACKENDS, e2e_artifact_dir, require_e2e_backend

from celesto import Celesto, CelestoError, ForkBatch, ForkResult
from celesto.cli._sqlite import SQLiteStateManager
from celesto.facade import _build_auto_config
from celesto.vm import CelestoManager, resolve_data_dir

pytestmark = pytest.mark.e2e

_CLI_MAIN = "from celesto.cli.main import main; raise SystemExit(main())"
_MARKER_PATH = "/marker"


def _require_backend(backend: str, request: pytest.FixtureRequest) -> None:
    require_e2e_backend(backend, request.config, sandbox_name=f"fork-cli-{backend}")  # type: ignore[arg-type]


def _source_name(label: str) -> tuple[str, str]:
    prefix = os.environ.get("CELESTO_E2E_NAME_PREFIX", "e2e-")
    suffix = uuid.uuid4().hex[:6]
    return f"{prefix}fk{label}-{suffix}", suffix


def _artifact(tmp_path: Path, name: str) -> Path:
    return e2e_artifact_dir(tmp_path) / name


class _Cli:
    """Runs ``celesto`` commands and records each one for the artifact."""

    def __init__(self) -> None:
        self.steps: list[dict[str, Any]] = []

    def run(self, *args: str, step: str) -> tuple[int, str, str]:
        proc = subprocess.run(
            [sys.executable, "-c", _CLI_MAIN, *args],
            capture_output=True,
            text=True,
            timeout=900,
            check=False,
        )
        record: dict[str, Any] = {
            "step": step,
            "command": "celesto " + shlex.join(args),
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
        with suppress(json.JSONDecodeError):
            record["json"] = json.loads(proc.stdout)
        self.steps.append(record)
        return proc.returncode, proc.stdout, proc.stderr

    def json(self, *args: str, step: str) -> tuple[int, dict[str, Any]]:
        """Run with ``--json`` (placed before ``--``) and return the envelope."""
        split = args.index("--") if "--" in args else len(args)
        code, stdout, stderr = self.run(*args[:split], "--json", *args[split:], step=step)
        try:
            envelope = json.loads(stdout)
        except json.JSONDecodeError:
            pytest.fail(f"celesto {' '.join(args)} printed no JSON: {stdout}\n{stderr}")
        assert envelope["exit_code"] == code, envelope
        return code, envelope

    def ok(self, *args: str, step: str) -> dict[str, Any]:
        code, envelope = self.json(*args, step=step)
        assert code == 0 and envelope["ok"], f"celesto {' '.join(args)}: {envelope}"
        return envelope["data"] or {}


def _sandbox_names(cli: _Cli, step: str) -> list[str]:
    data = cli.ok("sandbox", "list", "--all", step=step)
    return sorted(row["name"] for row in data["vms"])


def _delete_everything(data_dir: Path, names: list[str], source: str) -> None:
    state = SQLiteStateManager(data_dir / "celesto.db")
    manager = CelestoManager(state_manager=state)
    for name in reversed(names):
        with suppress(Exception):
            manager.delete(name)
    with suppress(Exception):
        for snapshot in manager.list_snapshots(vm_id=source):
            manager.delete_snapshot(snapshot.snapshot_id)


@pytest.mark.parametrize("backend", E2E_BACKENDS, ids=str)
def test_sandbox_fork_cli_end_to_end(
    backend: str, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    """Fork from the CLI: children, lineage, a paused source, and a safe retry."""
    _require_backend(backend, request)
    source, suffix = _source_name("cli")
    marker = f"fork-cli-{suffix}"
    exact = f"{source}-exact"
    cli = _Cli()
    report: dict[str, Any] = {"backend": backend, "host": platform.system(), "source": source}
    artifact = _artifact(tmp_path, f"sandbox-fork-cli-{backend}-{platform.system().lower()}.json")
    created: list[str] = []
    try:
        cli.ok(
            "sandbox",
            "create",
            "--name",
            source,
            "--os",
            "alpine",
            "--backend",
            backend,
            "--boot-timeout",
            str(BOOT_TIMEOUT),
            step="create source",
        )
        created.append(source)
        cli.ok(
            "sandbox",
            "exec",
            source,
            "--",
            "sh",
            "-c",
            f"echo {marker} > {_MARKER_PATH} && sync",
            step="write marker",
        )

        # 1. Three children, each with the source's files.
        code, envelope = cli.json(
            "sandbox",
            "fork",
            source,
            "--count",
            "3",
            "--boot-timeout",
            str(BOOT_TIMEOUT),
            step="fork --count 3",
        )
        children = (envelope.get("data") or {}).get("children", [])
        created.extend(child["name"] for child in children)
        assert code == 0 and envelope["ok"], envelope
        assert [child["name"] for child in children] == [f"{source}-{i}" for i in (1, 2, 3)]
        for child in children:
            assert child["ok"] is True and child["status"] == "created", child
            assert child["error"] is None, child
            assert child["sandbox"]["name"] == child["name"], child
            assert child["sandbox"]["status"] == "running", child
        assert envelope["data"]["warnings"] == []
        assert envelope["data"]["source_state"] == "running"
        for child in children:
            data = cli.ok(
                "sandbox", "exec", child["name"], "--", "cat", _MARKER_PATH, step="read marker"
            )
            assert data["stdout"].strip() == marker, (child["name"], data)

        # 2. A child shows where it came from.
        info = cli.ok("sandbox", "info", children[0]["name"], step="info child")
        assert info["vm"]["forked_from"] == source, info
        assert info["vm"]["forked_at"], info
        _, human_info, _ = cli.run("sandbox", "info", children[0]["name"], step="info child human")
        assert "Forked From" in human_info and source in human_info, human_info

        # 3. A paused source is refused with the exact message and recovery.
        cli.ok("sandbox", "pause", source, step="pause source")
        before = _sandbox_names(cli, "list before paused fork")
        code, envelope = cli.json(
            "sandbox", "fork", source, "--name", exact, step="fork paused source"
        )
        expected = (
            f"Sandbox '{source}' is paused. Run 'celesto sandbox resume {source}', then fork again."
        )
        assert code == 1 and not envelope["ok"], envelope
        assert envelope["error"]["message"] == expected, envelope
        assert _sandbox_names(cli, "list after paused fork") == before
        recovery = re.search(r"Run '([^']+)'", envelope["error"]["message"])
        assert recovery is not None
        cli.ok(*shlex.split(recovery.group(1))[1:], step="run printed recovery")

        code, stdout, stderr = cli.run(
            "sandbox",
            "fork",
            source,
            "--name",
            exact,
            "--boot-timeout",
            str(BOOT_TIMEOUT),
            step="fork after resume (human output)",
        )
        created.append(exact)
        assert code == 0, (stdout, stderr)
        assert re.search(rf"^{re.escape(exact)}\s+created$", stdout, re.MULTILINE), stdout
        data = cli.ok("sandbox", "exec", exact, "--", "cat", _MARKER_PATH, step="read marker")
        assert data["stdout"].strip() == marker

        # 4. The same --name again is refused before anything is created.
        before = _sandbox_names(cli, "list before retry")
        code, envelope = cli.json("sandbox", "fork", source, "--name", exact, step="retry fork")
        assert code == 1 and not envelope["ok"], envelope
        assert envelope["error"]["message"] == (
            f"A sandbox named '{exact}' already exists. Choose another name with '--name', "
            f"or run 'celesto sandbox delete {exact}'."
        ), envelope
        assert _sandbox_names(cli, "list after retry") == before
        report["result"] = "passed"
    finally:
        report["steps"] = cli.steps
        artifact.write_text(json.dumps(report, indent=2, default=str))
        _delete_everything(resolve_data_dir(), created, source)


@pytest.mark.parametrize("backend", E2E_BACKENDS, ids=str)
def test_sdk_fork_and_fork_many(
    backend: str, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    """``vm.fork()`` returns a working child; ``fork_many()`` returns a batch."""
    _require_backend(backend, request)
    source_name, suffix = _source_name("sdk")
    marker = f"fork-sdk-{suffix}"
    artifact = _artifact(tmp_path, f"sandbox-fork-sdk-{backend}-{platform.system().lower()}.json")
    report: dict[str, Any] = {"backend": backend, "host": platform.system(), "source": source_name}
    state = SQLiteStateManager(resolve_data_dir() / "celesto.db")
    created: list[str] = [source_name]
    try:
        config, ssh_key_path = _build_auto_config(vm_name=source_name, os="alpine", backend=backend)
        source = Celesto(config=config, ssh_key_path=ssh_key_path, state_manager=state)
        source.start(boot_timeout=BOOT_TIMEOUT)
        assert source.run(f"echo {marker} > {_MARKER_PATH} && sync").exit_code == 0

        child = source.fork(f"{source_name}-one", boot_timeout=BOOT_TIMEOUT)
        created.append(child.vm_id)
        assert isinstance(child, Celesto)
        report["fork"] = {
            "name": child.vm_id,
            "status": child.status.value,
            "marker": child.run(f"cat {_MARKER_PATH}").stdout.strip(),
        }
        assert report["fork"]["marker"] == marker, report

        batch = source.fork_many(2, name=f"{source_name}-many", boot_timeout=BOOT_TIMEOUT)
        created.extend(result.name for result in batch.children)
        assert isinstance(batch, ForkBatch)
        report["fork_many"] = {
            "children": [
                {
                    "name": result.name,
                    "ok": result.ok,
                    "error": result.error,
                    "marker": (
                        result.sandbox.run(f"cat {_MARKER_PATH}").stdout.strip()
                        if result.sandbox
                        else None
                    ),
                }
                for result in batch.children
            ],
            "warnings": list(batch.warnings),
            "source_state": batch.source_state.value,
        }
        assert all(isinstance(result, ForkResult) for result in batch.children)
        assert [result.name for result in batch.children] == [
            f"{source_name}-many-1",
            f"{source_name}-many-2",
        ]
        for entry in report["fork_many"]["children"]:
            assert entry["ok"] and entry["marker"] == marker, entry

        # A taken name is refused before anything is created.
        with pytest.raises(CelestoError) as refused:
            source.fork(f"{source_name}-one")
        report["refused"] = str(refused.value)
        assert str(refused.value).startswith(f"A sandbox named '{source_name}-one' already exists")
        report["result"] = "passed"
    finally:
        artifact.write_text(json.dumps(report, indent=2, default=str))
        _delete_everything(resolve_data_dir(), created, source_name)

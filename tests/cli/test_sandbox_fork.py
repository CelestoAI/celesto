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

"""``celesto sandbox fork`` output when a child fails, a warning appears, or
the sandbox is in the cloud.

``tests/e2e/test_sandbox_fork_cli.py`` runs the command on real sandboxes,
where every child boots and the source never stays paused. These tests
replace the fork engine's result to force the rest. Failure modes, written
before the code:

1. The command exits 0 when a child failed, or JSON says ``ok: true``.
2. A failed child is missing from JSON, or has no ``error``, or the error
   differs from the message the engine gave.
3. A created child has no details in JSON, or a different shape from the
   rows ``celesto sandbox list`` shows.
4. Human output leaves out a failed child's message or a warning.
5. A notice ("Pausing …") lands on stdout and breaks ``--json`` parsing.
6. ``--cloud`` reaches the local engine instead of failing with the cloud
   message, in both human and JSON output.
7. Child handles are left open.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest

from celesto._fork import ForkBatch, ForkResult, cloud_message, pausing_notice
from celesto.cli import main as cli_main
from celesto.cli.main import main
from celesto.types import NetworkConfig, VMState

_SOURCE = "sbx-einstein"
_FAILED = (
    "Sandbox 'sbx-einstein-2' didn't start within 30 seconds and was removed. "
    "Run the fork again with '--boot-timeout 60'."
)
_WARNING = (
    "Sandbox 'sbx-einstein' stayed paused after the fork. "
    "Run 'celesto sandbox resume sbx-einstein' to continue it."
)


class _Child:
    def __init__(self, name: str) -> None:
        self.vm_id = name
        self.closed = False
        self.info = SimpleNamespace(
            vm_id=name,
            status=VMState.RUNNING,
            pid=4242,
            config=SimpleNamespace(preset=None, workspace_mounts=[]),
            network=NetworkConfig(
                guest_ip="172.16.0.6",
                gateway_ip="172.16.0.5",
                netmask="255.255.255.252",
                tap_device="tap-c1",
                guest_mac="06:00:ac:10:00:06",
                ssh_host_port=2223,
            ),
        )

    def close(self) -> None:
        self.closed = True


class _Source:
    def __init__(self, batch: ForkBatch) -> None:
        self.vm_id = _SOURCE
        self.batch = batch
        self.calls: list[dict[str, Any]] = []
        self.closed = False

    def _fork_many(self, count: int, **kwargs: Any) -> ForkBatch:
        self.calls.append({"count": count, **kwargs})
        kwargs["on_notice"](pausing_notice(_SOURCE))
        return self.batch

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def partial(monkeypatch: pytest.MonkeyPatch) -> tuple[_Source, _Child]:
    child = _Child("sbx-einstein-1")
    batch = ForkBatch(
        children=(
            ForkResult(name="sbx-einstein-1", ok=True, sandbox=child),  # type: ignore[arg-type]
            ForkResult(name="sbx-einstein-2", ok=False, error=_FAILED),
        ),
        warnings=(_WARNING,),
        source_state=VMState.PAUSED,
    )
    source = _Source(batch)
    monkeypatch.setattr(cli_main, "_cli_vm_from_id", lambda vm_id, **_: source)
    return source, child


def test_json_reports_each_child_and_exits_1_when_one_failed(
    partial: tuple[_Source, _Child], capsys: pytest.CaptureFixture[str]
) -> None:
    source, child = partial

    code = main(["sandbox", "fork", _SOURCE, "--count", "2", "--parallel", "1", "--json"])

    out, err = capsys.readouterr()
    envelope = json.loads(out)
    assert code == 1
    assert envelope["ok"] is False and envelope["exit_code"] == 1
    assert envelope["error"]["message"] == _FAILED
    data = envelope["data"]
    assert data["source_state"] == "paused"
    assert data["warnings"] == [_WARNING]
    created, failed = data["children"]
    assert created == {
        "name": "sbx-einstein-1",
        "ok": True,
        "status": "created",
        "sandbox": {
            "name": "sbx-einstein-1",
            "preset": None,
            "status": "running",
            "pid": 4242,
            "ip_address": "172.16.0.6",
            "ssh_port": 2223,
            "warnings": [],
        },
        "error": None,
    }
    assert failed == {
        "name": "sbx-einstein-2",
        "ok": False,
        "status": "failed",
        "sandbox": None,
        "error": _FAILED,
    }
    assert pausing_notice(_SOURCE) in err
    assert source.calls == [
        {
            "count": 2,
            "name": None,
            "parallel": 1,
            "boot_timeout": 30.0,
            "on_notice": source.calls[0]["on_notice"],
        }
    ]
    assert child.closed and source.closed


def test_human_output_has_one_line_per_child_then_warnings(
    partial: tuple[_Source, _Child], capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(["sandbox", "fork", _SOURCE, "--count", "2"])

    out, err = capsys.readouterr()
    assert code == 1
    lines = [line.rstrip() for line in out.splitlines() if line.strip()]
    assert lines[0] == "sbx-einstein-1  created"
    assert lines[1] == f"sbx-einstein-2  failed: {_FAILED}"
    assert f"Warning: {_WARNING}" in " ".join(out.split())
    assert pausing_notice(_SOURCE) in err


@pytest.mark.parametrize("json_output", [True, False], ids=["json", "human"])
def test_cloud_sandboxes_are_refused_before_anything_runs(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], json_output: bool
) -> None:
    def unexpected(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("a cloud fork must not reach the local engine")

    monkeypatch.setattr(cli_main, "_cli_vm_from_id", unexpected)

    code = main(["sandbox", "fork", _SOURCE, "--cloud", *(["--json"] if json_output else [])])

    out, err = capsys.readouterr()
    assert code == 1
    if json_output:
        assert json.loads(out)["error"]["message"] == cloud_message()
    else:
        # The error panel wraps long lines inside a border.
        assert cloud_message() in " ".join(err.replace("│", " ").split())

"""Local usage telemetry behavior at the CLI and Python SDK boundaries."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from click.testing import CliRunner

from celesto import Computer
from celesto import _telemetry as telemetry
from celesto.cli.main import build_cli
from celesto.types import CommandResult


@pytest.fixture
def capture_events(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    monkeypatch.setattr(telemetry, "_STATE_PATH", tmp_path / ".celesto" / "telemetry.json")
    monkeypatch.setattr(telemetry, "_PROJECT_KEY", "test-public-capture-key")
    monkeypatch.setattr(telemetry, "_notice_this_process", False)

    def post(_url: str, *, json: dict[str, Any], timeout: float) -> SimpleNamespace:
        events.append(json)
        return SimpleNamespace(status_code=200)

    monkeypatch.setattr(httpx, "post", post)
    monkeypatch.setattr(telemetry, "_queue", telemetry._send)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("CELESTO_NO_TELEMETRY", raising=False)
    monkeypatch.delenv("DO_NOT_TRACK", raising=False)
    return events


def test_first_use_notice_precedes_identity_and_events(
    capture_events: list[dict[str, Any]],
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "0")
    assert telemetry.begin_local_use("python_sdk") is False
    assert "celesto config telemetry off" in capsys.readouterr().err
    first_state = json.loads(telemetry._STATE_PATH.read_text())
    assert first_state == {"notice_shown": True}
    telemetry.record_success("python_sdk", "computer")
    assert capture_events == []

    monkeypatch.setattr(telemetry, "_notice_this_process", False)
    assert telemetry.begin_local_use("python_sdk") is True
    telemetry.record_success("python_sdk", "command_execution")
    telemetry.record_success("python_sdk", "command_execution")

    assert [event["event"] for event in capture_events] == [
        "celesto_oss_active",
        "celesto_oss_feature_used",
    ]
    state = json.loads(telemetry._STATE_PATH.read_text())
    assert state["installation_id"] == capture_events[0]["distinct_id"]
    assert state["installation_id"].startswith("celesto-oss-")
    assert capture_events[1]["distinct_id"] == state["installation_id"]
    assert capture_events[1]["properties"]["feature"] == "command_execution"
    assert set(capture_events[1]["properties"]) == {
        "schema_version",
        "surface",
        "celesto_version",
        "os_family",
        "$process_person_profile",
        "$geoip_disable",
        "feature",
    }
    assert telemetry._STATE_PATH.stat().st_mode & 0o777 == 0o600


def test_opt_out_and_environment_override_create_no_identity(
    capture_events: list[dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "0")
    telemetry.set_enabled(False)
    assert telemetry.status() == (False, "saved preference")
    assert telemetry.begin_local_use("cli") is False
    assert "installation_id" not in json.loads(telemetry._STATE_PATH.read_text())
    assert capture_events == []

    telemetry.set_enabled(True)
    monkeypatch.setenv("DO_NOT_TRACK", "1")
    assert telemetry.status() == (False, "DO_NOT_TRACK")
    assert telemetry.begin_local_use("python_sdk") is False
    monkeypatch.delenv("DO_NOT_TRACK")
    monkeypatch.setenv("CELESTO_NO_TELEMETRY", "1")
    assert telemetry.status() == (False, "CELESTO_NO_TELEMETRY")
    assert telemetry.begin_local_use("cli") is False
    assert "installation_id" not in json.loads(telemetry._STATE_PATH.read_text())


def test_unreadable_state_fails_closed(
    capture_events: list[dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "0")
    telemetry._STATE_PATH.parent.mkdir()
    telemetry._STATE_PATH.write_text("not json")
    assert telemetry.status() == (False, "unavailable state")
    assert telemetry.begin_local_use("cli") is False
    telemetry.record_success("cli", "computer")
    assert capture_events == []


def test_concurrent_operations_keep_event_caps(
    capture_events: list[dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "0")
    telemetry.begin_local_use("python_sdk")
    monkeypatch.setattr(telemetry, "_notice_this_process", False)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda _: telemetry.record_success("python_sdk", "browser"), range(20)))

    assert [event["event"] for event in capture_events] == [
        "celesto_oss_active",
        "celesto_oss_feature_used",
    ]


def test_import_does_not_create_telemetry_state(tmp_path: Path) -> None:
    environment = {**os.environ, "HOME": str(tmp_path), "CELESTO_NO_TELEMETRY": "1"}
    subprocess.run([sys.executable, "-c", "import celesto"], env=environment, check=True)
    assert not (tmp_path / ".celesto" / "telemetry.json").exists()


def test_cli_config_and_successful_local_command_only(
    capture_events: list[dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "0")
    from celesto.cli.commands import app

    monkeypatch.setattr(app, "maybe_print_update_notice", lambda **kwargs: None)
    monkeypatch.setattr(app, "run_doctor", lambda **kwargs: 0)
    monkeypatch.setattr(
        app,
        "_handlers",
        lambda: SimpleNamespace(_run_computer=lambda args: 0, _run_list=lambda **kwargs: 0),
    )
    runner = CliRunner()

    off = runner.invoke(build_cli(), ["config", "telemetry", "off"])
    assert off.exit_code == 0
    assert "Telemetry is off" in off.output
    assert "installation_id" not in json.loads(telemetry._STATE_PATH.read_text())
    assert runner.invoke(build_cli(), ["config", "telemetry", "on"]).exit_code == 0
    assert "Telemetry is on" in runner.invoke(build_cli(), ["config", "telemetry"]).output

    first = runner.invoke(build_cli(), ["doctor"])
    assert first.exit_code == 0
    assert "Opt out" in first.stderr
    assert capture_events == []

    monkeypatch.setattr(telemetry, "_notice_this_process", False)
    second = runner.invoke(build_cli(), ["computer", "list"])
    assert second.exit_code == 0
    assert [event["event"] for event in capture_events] == [
        "celesto_oss_active",
        "celesto_oss_feature_used",
    ]
    assert capture_events[0]["properties"]["surface"] == "cli"
    assert capture_events[1]["properties"]["feature"] == "computer"

    class Provider:
        id = None

        def start(self) -> None:
            return None

        def validate_command(self, command: str, timeout: int) -> None:
            return None

        def run(self, command: str, timeout: int) -> CommandResult:
            return CommandResult(stdout="ok", stderr="", exit_code=0)

    monkeypatch.setattr("celesto.sdk.make_provider", lambda *_args: Provider())

    def cli_calls_sdk(_args: object) -> int:
        Computer().run("echo nested")
        return 0

    monkeypatch.setattr(
        app,
        "_handlers",
        lambda: SimpleNamespace(_run_computer=cli_calls_sdk, _run_list=lambda **kwargs: 0),
    )
    nested = runner.invoke(build_cli(), ["computer", "list"])
    assert nested.exit_code == 0
    assert len(capture_events) == 2

    cloud = runner.invoke(build_cli(), ["computer", "list", "--cloud"])
    assert cloud.exit_code == 0
    assert len(capture_events) == 2

    monkeypatch.setattr(app, "run_doctor", lambda **kwargs: 1)
    failed = runner.invoke(build_cli(), ["doctor"])
    assert failed.exit_code == 0
    assert len(capture_events) == 2


def test_sdk_local_operation_and_cloud_exclusion(
    capture_events: list[dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "0")

    class Provider:
        id = None

        def start(self) -> None:
            return None

        def validate_command(self, command: str, timeout: int) -> None:
            return None

        def run(self, command: str, timeout: int) -> CommandResult:
            return CommandResult(stdout="ok", stderr="", exit_code=0)

    monkeypatch.setattr("celesto.sdk.make_provider", lambda *_args: Provider())
    Computer(provider="cloud").run("echo cloud-secret")
    assert not telemetry._STATE_PATH.exists()
    assert Computer().run("echo private-path") == CommandResult(stdout="ok", stderr="", exit_code=0)
    assert capture_events == []

    monkeypatch.setattr(telemetry, "_notice_this_process", False)
    Computer().run("echo private-path")
    assert len(capture_events) == 2
    assert capture_events[1]["properties"]["feature"] == "command_execution"
    assert "private-path" not in json.dumps(capture_events)

    Computer(provider="cloud").run("echo cloud-secret")
    assert len(capture_events) == 2


def test_failed_capture_retries_until_success(
    capture_events: list[dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "0")
    telemetry.begin_local_use("python_sdk")
    monkeypatch.setattr(telemetry, "_notice_this_process", False)
    responses = iter([OSError("offline"), 503, 200, 200])
    delivered: list[dict[str, Any]] = []

    def post(_url: str, *, json: dict[str, Any], timeout: float) -> SimpleNamespace:
        delivered.append(json)
        response = next(responses)
        if isinstance(response, OSError):
            raise response
        return SimpleNamespace(status_code=response)

    monkeypatch.setattr(httpx, "post", post)

    telemetry.record_success("python_sdk", "browser")
    state = json.loads(telemetry._STATE_PATH.read_text())
    assert state.get("active", {}).get("python_sdk") is None
    assert state.get("features", {}).get("python_sdk:browser") is None

    telemetry.record_success("python_sdk", "browser")
    assert len(delivered) == 4
    state = json.loads(telemetry._STATE_PATH.read_text())
    assert state["active"]["python_sdk"]
    assert state["features"]["python_sdk:browser"]

    telemetry.record_success("python_sdk", "browser")
    assert len(delivered) == 4


def test_opt_out_suppresses_a_queued_send(
    capture_events: list[dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PYTEST_CURRENT_TEST", "0")
    delivered: list[dict[str, Any]] = []
    queued: list[tuple[dict[str, Any], telemetry.Marker]] = []
    monkeypatch.setattr(httpx, "post", lambda _url, *, json, timeout: delivered.append(json))
    monkeypatch.setattr(telemetry, "_queue", lambda event, marker: queued.append((event, marker)))
    telemetry.begin_local_use("cli")
    monkeypatch.setattr(telemetry, "_notice_this_process", False)
    telemetry.record_success("cli", "computer")
    assert len(queued) == 2
    telemetry.set_enabled(False)

    for event, marker in queued:
        telemetry._send(event, marker)

    assert delivered == []
    assert capture_events == []

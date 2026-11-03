"""Opt-in, read-only check of `celesto ci` against a real Celesto backend.

It runs only GET commands with the stored login (or CELESTO_API_KEY): the
runner sizes, recent failed jobs, one job, and that job's log. Each
command's JSON output is saved under artifacts/ci-cli-live/ so the result
can be compared run to run.
"""

import json
import os
from pathlib import Path
from typing import Any

import pytest

from celesto.cli.main import main

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts" / "ci-cli-live"


def _ci(capsys: pytest.CaptureFixture[str], name: str, *args: str) -> dict[str, Any]:
    capsys.readouterr()
    code = main(["ci", *args, "--json"])
    output = capsys.readouterr().out
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / f"{name}.json").write_text(output)
    payload = json.loads(output)
    assert code == 0 and payload["ok"], output
    data: dict[str, Any] = payload["data"]
    return data


@pytest.mark.skipif(
    os.getenv("CELESTO_CI_LIVE") != "1",
    reason="Set CELESTO_CI_LIVE=1 to read CI jobs from a real Celesto backend.",
)
def test_ci_commands_read_real_jobs(capsys: pytest.CaptureFixture[str]) -> None:
    runners = _ci(capsys, "runners-list", "runners", "list")
    assert [runner["label"] for runner in runners["runners"]] == [
        "celesto-micro",
        "celesto-small",
        "celesto-standard",
        "celesto-memory",
        "celesto-large",
        "celesto-xl",
    ]

    failed = _ci(capsys, "jobs-list-failed", "jobs", "list", "--status", "failed", "--limit", "5")
    unscored = {"success", "neutral", "skipped", "cancelled", "stale", "completed", None}
    assert all(job["native_conclusion"] not in unscored for job in failed["jobs"])
    if not failed["jobs"]:
        pytest.skip("This organization has no failed CI jobs to read a log from.")

    job_id = str(failed["jobs"][0]["job_id"])
    shown = _ci(capsys, "jobs-show", "jobs", "show", job_id)
    assert str(shown["job_id"]) == job_id

    log = _ci(capsys, "logs", "logs", job_id)
    assert log["steps"], "A finished job should have at least one step."
    assert any(step["lines"] for step in log["steps"]), "A finished job's log should have lines."

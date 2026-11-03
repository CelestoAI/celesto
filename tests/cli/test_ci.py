"""`celesto ci` reads Celesto CI from the terminal, through the real client and HTTP.

Each test logs in with stored credentials that point at a local stub of the
backend's CI routes, then runs the command as a user would. The stub records
every request, so the tests also check what the CLI asks the backend for.

Ways it can go wrong, each covered below:
- A command calls the wrong route, drops the API key, or sends wrong filters.
- Human output hides a field or `--json` breaks the standard envelope.
- An error from the backend becomes a traceback or a message without a recovery command.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
from click.testing import CliRunner

from celesto.cli import _credentials
from celesto.cli.commands.app import build_cli
from celesto.cli.main import main

RUNNERS = {
    "runners": [
        {
            "label": "celesto-micro",
            "size": "micro",
            "vcpus": 1,
            "ram_mb": 2048,
            "disk_size_mb": 20480,
        },
        {"label": "celesto-xl", "size": "xl", "vcpus": 8, "ram_mb": 32768, "disk_size_mb": 102400},
    ]
}


class Backend:
    """A stub of the backend's CI routes: canned answers, recorded requests."""

    def __init__(self) -> None:
        self.routes: dict[str, tuple[int, Any]] = {}
        self.requests: list[dict[str, Any]] = []
        self.url = ""

    def serve(self, path: str, body: Any, status: int = 200) -> None:
        self.routes[path] = (status, body)


@pytest.fixture
def backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Backend]:
    stub = Backend()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - http.server's handler name
            parts = urlsplit(self.path)
            stub.requests.append(
                {
                    "path": parts.path,
                    "query": {key: values[-1] for key, values in parse_qs(parts.query).items()},
                    "authorization": self.headers.get("Authorization"),
                }
            )
            status, body = stub.routes.get(parts.path, (404, {"detail": "Not Found"}))
            payload = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - http.server's name
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    stub.url = f"http://127.0.0.1:{server.server_address[1]}"
    monkeypatch.delenv("CELESTO_API_KEY", raising=False)
    monkeypatch.setattr(_credentials, "CREDENTIALS_PATH", tmp_path / "credentials")
    _credentials.write_credentials(
        api_key="cel_test_key", email="ci@example.invalid", base_url=stub.url
    )
    try:
        yield stub
    finally:
        server.shutdown()
        server.server_close()


@dataclass
class Ran:
    exit_code: int
    output: str


Runner = Callable[..., Ran]


@pytest.fixture
def run(capsys: pytest.CaptureFixture[str]) -> Runner:
    """Run `celesto ci ...` through the CLI entry point, as the installed command does."""

    def invoke(*args: str) -> Ran:
        capsys.readouterr()
        code = main(["ci", *args])
        return Ran(code, capsys.readouterr().out)

    return invoke


def test_runners_list_prints_each_size(backend: Backend, run: Runner) -> None:
    backend.serve("/v1/integrations/github/actions/runners", RUNNERS)
    result = run("runners", "list")
    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[0].split() == ["LABEL", "VCPU", "RAM", "DISK"]
    assert lines[1].split() == ["celesto-micro", "1", "2", "GiB", "20", "GiB"]
    assert lines[2].split() == ["celesto-xl", "8", "32", "GiB", "100", "GiB"]
    assert backend.requests == [
        {
            "path": "/v1/integrations/github/actions/runners",
            "query": {},
            "authorization": "Bearer cel_test_key",
        }
    ]


def test_runners_list_json_uses_the_standard_envelope(backend: Backend, run: Runner) -> None:
    backend.serve("/v1/integrations/github/actions/runners", RUNNERS)
    result = run("runners", "list", "--json")
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {
        "ok": True,
        "command": "ci.runners.list",
        "exit_code": 0,
        "data": RUNNERS,
        "error": None,
    }


JOBS_PAGE = "/v1/integrations/github/actions/jobs/page"


def _job(job_id: int, status: str, **extra: Any) -> dict[str, Any]:
    return {
        "job_id": job_id,
        "status": status,
        "repository": "acme/api",
        "workflow_name": "tests",
        "job_name": "pytest",
        "head_branch": "main",
        "created_at": "2026-11-03T10:00:00Z",
        **extra,
    }


def _page(items: list[dict[str, Any]], total: int) -> dict[str, Any]:
    return {"items": items, "total": total, "page": 0, "page_size": 20, "counts": {}}


def test_jobs_list_sends_filters_and_prints_each_job(backend: Backend, run: Runner) -> None:
    backend.serve(JOBS_PAGE, _page([_job(812, "failure"), _job(811, "failure")], total=2))
    result = run(
        "jobs",
        "list",
        "--status",
        "failed",
        "--repo",
        "acme/api",
        "--workflow",
        "tests",
        "--search",
        "fix login",
        "--limit",
        "5",
    )
    assert result.exit_code == 0, result.output
    assert backend.requests[0]["query"] == {
        "tab": "failed",
        "q": "fix login",
        "repository": "acme/api",
        "workflow": "tests",
        "page": "0",
        "page_size": "5",
    }
    lines = result.output.splitlines()
    assert lines[0].split() == [
        "JOB",
        "STATUS",
        "REPOSITORY",
        "WORKFLOW",
        "JOB",
        "BRANCH",
        "CREATED",
    ]
    assert lines[1].split() == [
        "812",
        "failure",
        "acme/api",
        "tests",
        "pytest",
        "main",
        "2026-11-03T10:00:00Z",
    ]
    assert len(lines) == 3


def test_jobs_list_maps_every_status_name(backend: Backend, run: Runner) -> None:
    backend.serve(JOBS_PAGE, _page([], total=0))
    for name, tab in (
        ("in-progress", "in_progress"),
        ("needs-action", "needs_action"),
        ("completed", "completed"),
        ("passed", "passed"),
    ):
        assert run("jobs", "list", "--status", name).exit_code == 0
        assert backend.requests[-1]["query"]["tab"] == tab
    assert run("jobs", "list").exit_code == 0
    assert backend.requests[-1]["query"]["tab"] == "all"


def test_jobs_list_says_when_more_jobs_exist(backend: Backend, run: Runner) -> None:
    backend.serve(JOBS_PAGE, _page([_job(812, "success")], total=40))
    result = run("jobs", "list", "--limit", "1")
    assert result.exit_code == 0, result.output
    assert (
        "Showing 1 of 40 jobs. Run 'celesto ci jobs list --limit 100' to see more." in result.output
    )


def test_jobs_list_with_no_jobs_says_so(backend: Backend, run: Runner) -> None:
    backend.serve(JOBS_PAGE, _page([], total=0))
    result = run("jobs", "list", "--status", "failed")
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "No CI jobs match."


def test_jobs_list_rejects_a_limit_over_100(backend: Backend) -> None:
    result = CliRunner().invoke(build_cli(), ["ci", "jobs", "list", "--limit", "101"])
    assert result.exit_code == 2
    assert backend.requests == []


def test_jobs_list_json_returns_jobs_and_total(backend: Backend, run: Runner) -> None:
    job = _job(812, "failure")
    backend.serve(JOBS_PAGE, _page([job], total=1))
    result = run("jobs", "list", "--json")
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["command"] == "ci.jobs.list"
    assert payload["data"] == {"jobs": [job], "total": 1}


DETAIL = _job(
    812,
    "failure",
    status_message="The job failed.",
    head_sha="abc1234",
    size_id="standard",
    execution_started_at="2026-11-03T10:00:05Z",
    execution_completed_at="2026-11-03T10:02:05Z",
    github_job_url="https://github.com/acme/api/actions/runs/9/job/812",
)


def test_jobs_show_prints_the_job(backend: Backend, run: Runner) -> None:
    backend.serve("/v1/integrations/github/actions/jobs/812", DETAIL)
    result = run("jobs", "show", "812")
    assert result.exit_code == 0, result.output
    assert "Status:      failure (The job failed.)" in result.output
    assert "Repository:  acme/api" in result.output
    assert "Machine:     standard" in result.output
    assert "GitHub:      https://github.com/acme/api/actions/runs/9/job/812" in result.output
    assert backend.requests[0]["path"] == "/v1/integrations/github/actions/jobs/812"


def test_jobs_show_json_returns_the_backend_fields(backend: Backend, run: Runner) -> None:
    backend.serve("/v1/integrations/github/actions/jobs/812", DETAIL)
    result = run("jobs", "show", "812", "--json")
    assert json.loads(result.output)["data"] == DETAIL


def test_jobs_show_unknown_job_names_the_recovery_command(backend: Backend, run: Runner) -> None:
    result = run("jobs", "show", "999", "--json")
    assert result.exit_code == 1
    assert json.loads(result.output)["error"] == {
        "code": "ci_job_not_found",
        "message": "CI job 999 was not found. Run 'celesto ci jobs list' to see your jobs.",
    }

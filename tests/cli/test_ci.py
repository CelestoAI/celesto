"""`celesto ci` reads Celesto CI from the terminal, through the real client and HTTP.

Each test logs in with stored credentials that point at a local stub of the
backend's CI routes, then runs the command as a user would. The stub records
every request, so the tests also check what the CLI asks the backend for.

Ways it can go wrong, each covered below:
- A command calls the wrong route, drops the API key, or sends wrong filters.
- Human output hides a field or `--json` breaks the standard envelope.
- An error from the backend becomes a traceback or a message without a recovery command.
- Terminal output overflows, hides a job ID/status, or interprets names as markup.
- Styling wraps or alters raw log lines, or contaminates JSON with terminal codes.
"""

from __future__ import annotations

import io
import json
import os
import socket
import subprocess
import sys
import threading
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
from click.testing import CliRunner
from rich.cells import cell_len
from rich.text import Text

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
        "ID",
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


@pytest.mark.parametrize(
    ("width", "no_color"), [(60, False), (80, False), (120, False), (80, True)]
)
def test_terminal_jobs_are_scannable_and_point_to_details_and_logs(
    backend: Backend,
    run: Runner,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    width: int,
    no_color: bool,
) -> None:
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.setenv("TERM", "xterm-256color")
    if not no_color:
        monkeypatch.delenv("NO_COLOR")
    monkeypatch.setenv("COLUMNS", str(width))
    backend.serve(
        JOBS_PAGE,
        _page(
            [
                _job(
                    12345678901,
                    "setup_failed",
                    repository="acme/a-repository-with-a-long-name",
                    workflow_name="Integration tests across all supported platforms",
                    job_name="pytest [linux] with the production configuration",
                    head_branch="fix/a-long-branch-name",
                ),
                _job(812, "success", job_name="[linux]"),
            ],
            total=2,
        ),
    )
    result = run("jobs", "list")
    (tmp_path / f"jobs-{width}.ansi").write_text(result.output)
    plain = Text.from_ansi(result.output).plain
    assert result.exit_code == 0, plain
    assert all(cell_len(line) <= width for line in plain.splitlines()), plain
    assert "12345678901" in plain.splitlines()[1] and "setup_failed" in plain.splitlines()[1]
    assert "[linux]" in plain
    assert "celesto ci jobs show 12345678901" in plain
    assert "celesto ci logs 12345678901" in plain
    assert "ID" in plain.splitlines()[0]
    if not no_color:
        assert "\x1b[" in result.output


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


@pytest.mark.parametrize("limit", ["0", "101"])
def test_jobs_list_rejects_a_limit_outside_1_to_100(backend: Backend, limit: str) -> None:
    result = CliRunner().invoke(build_cli(), ["ci", "jobs", "list", "--limit", limit])
    assert result.exit_code == 2
    assert "--limit" in result.output and "1<=x<=100" in result.output
    assert backend.requests == []


def test_jobs_list_has_no_more_jobs_line_when_all_are_shown(backend: Backend, run: Runner) -> None:
    backend.serve(JOBS_PAGE, _page([_job(812, "success")], total=1))
    result = run("jobs", "list")
    assert "Showing" not in result.output


@pytest.mark.parametrize("terminal", [False, True])
def test_jobs_list_json_returns_jobs_and_total(
    backend: Backend, run: Runner, monkeypatch: pytest.MonkeyPatch, terminal: bool
) -> None:
    if terminal:
        monkeypatch.setenv("FORCE_COLOR", "1")
        monkeypatch.setenv("TERM", "xterm-256color")
        monkeypatch.delenv("NO_COLOR")
    job = _job(812, "failure")
    backend.serve(JOBS_PAGE, _page([job], total=1))
    result = run("jobs", "list", "--json")
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["command"] == "ci.jobs.list"
    assert payload["data"] == {"jobs": [job], "total": 1}
    assert "\x1b" not in result.output


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


@pytest.mark.parametrize("terminal", [False, True])
def test_jobs_show_prints_the_job(
    backend: Backend,
    run: Runner,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    terminal: bool,
) -> None:
    if terminal:
        monkeypatch.setenv("FORCE_COLOR", "1")
        monkeypatch.setenv("TERM", "xterm-256color")
        monkeypatch.delenv("NO_COLOR")
    backend.serve(
        "/v1/integrations/github/actions/jobs/812", {**DETAIL, "job_name": "pytest [linux]"}
    )
    result = run("jobs", "show", "812")
    (tmp_path / "job-show.ansi").write_text(result.output)
    assert result.exit_code == 0, result.output
    expected = [
        "Job:         812",
        "Status:      failure (The job failed.)",
        "Repository:  acme/api",
        "Workflow:    tests",
        "Job name:    pytest [linux]",
        "Branch:      main",
        "Commit:      abc1234",
        "Machine:     standard",
        "Created:     2026-11-03T10:00:00Z",
        "Started:     2026-11-03T10:00:05Z",
        "Finished:    2026-11-03T10:02:05Z",
        "GitHub:      https://github.com/acme/api/actions/runs/9/job/812",
    ]
    if terminal:
        expected.append("Logs: celesto ci logs 812")
    assert Text.from_ansi(result.output).plain.splitlines() == expected
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


JOB_812 = "/v1/integrations/github/actions/jobs/812"
STEPS = {
    "steps": [
        {"number": 1, "name": "Set up job", "status": "completed", "conclusion": "success"},
        {"number": 4, "name": "Run tests", "status": "completed", "conclusion": "failure"},
    ]
}


def _lines(*texts: str) -> list[dict[str, str]]:
    return [{"at": "2026-11-03T10:00:00Z", "text": text} for text in texts]


@pytest.fixture
def finished_job(backend: Backend) -> Backend:
    # `status` is Celesto's word and can lag; only GitHub's `native_status` says it finished.
    backend.serve(JOB_812, _job(812, "running", native_status="completed"))
    backend.serve(f"{JOB_812}/steps", STEPS)
    backend.serve(f"{JOB_812}/steps/1/log", {"lines": _lines("Runner ready"), "truncated": False})
    backend.serve(
        f"{JOB_812}/steps/4/log",
        {"lines": _lines("collected 3 items", "FAILED test_login"), "truncated": True},
    )
    return backend


@pytest.mark.parametrize("terminal", [False, True])
def test_logs_prints_every_step_in_order(
    finished_job: Backend,
    run: Runner,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    terminal: bool,
) -> None:
    if terminal:
        monkeypatch.setenv("FORCE_COLOR", "1")
        monkeypatch.setenv("TERM", "xterm-256color")
        monkeypatch.delenv("NO_COLOR")
        monkeypatch.setenv("COLUMNS", "60")
    raw_line = "[red] literal log [/red] https://example.com/" + "x" * 160
    finished_job.serve(
        f"{JOB_812}/steps/1/log", {"lines": _lines("Runner ready", raw_line), "truncated": False}
    )
    result = run("logs", "812")
    (tmp_path / "logs.ansi").write_text(result.output)
    assert result.exit_code == 0, result.output
    assert raw_line + "\n" in result.output
    assert Text.from_ansi(result.output).plain.splitlines() == [
        "── Step 1: Set up job (success) ──",
        "Runner ready",
        raw_line,
        "── Step 4: Run tests (failure) ──",
        "Only the last 5,000 lines of this step are shown.",
        "collected 3 items",
        "FAILED test_login",
    ]


def test_logs_step_prints_one_step(finished_job: Backend, run: Runner) -> None:
    result = run("logs", "812", "--step", "4")
    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[0] == "── Step 4: Run tests (failure) ──"
    assert "Runner ready" not in result.output
    assert "FAILED test_login" in result.output
    paths = [request["path"] for request in finished_job.requests]
    assert f"{JOB_812}/steps/4/log" in paths
    assert f"{JOB_812}/steps/1/log" not in paths


def test_logs_unknown_step_names_the_recovery_command(finished_job: Backend, run: Runner) -> None:
    result = run("logs", "812", "--step", "9", "--json")
    assert result.exit_code == 1
    assert json.loads(result.output)["error"] == {
        "code": "ci_step_not_found",
        "message": "Job 812 has no step 9. Run 'celesto ci logs 812' to see all steps.",
    }


def test_logs_json_returns_each_step_with_its_lines(finished_job: Backend, run: Runner) -> None:
    result = run("logs", "812", "--json")
    payload = json.loads(result.output)
    assert payload["command"] == "ci.logs"
    assert payload["data"]["job_id"] == 812
    assert payload["data"]["warnings"] == []
    assert [
        (step["number"], step["name"], step["conclusion"], step["truncated"])
        for step in payload["data"]["steps"]
    ] == [(1, "Set up job", "success", False), (4, "Run tests", "failure", True)]
    assert payload["data"]["steps"][1]["lines"] == _lines("collected 3 items", "FAILED test_login")


def test_logs_unknown_job_names_the_recovery_command(backend: Backend, run: Runner) -> None:
    result = run("logs", "999", "--json")
    assert result.exit_code == 1
    assert json.loads(result.output)["error"]["message"] == (
        "CI job 999 was not found. Run 'celesto ci jobs list' to see your jobs."
    )


RUNNING_NOTE = (
    "Job 812 is still running, so its log may be incomplete. "
    "Run 'celesto ci logs 812' again when it finishes."
)


@pytest.fixture
def running_job(backend: Backend) -> Backend:
    # Celesto gave up on setup, but GitHub reports the job unfinished; the note follows GitHub.
    backend.serve(JOB_812, _job(812, "setup_failed", native_status="in_progress"))
    backend.serve(
        f"{JOB_812}/steps",
        {
            "steps": [
                {"number": 1, "name": "Set up job", "status": "in_progress", "conclusion": None}
            ]
        },
    )
    backend.serve(f"{JOB_812}/steps/1/log", {"lines": [], "truncated": False})
    return backend


def test_logs_of_a_running_job_add_a_note(
    running_job: Backend, capsys: pytest.CaptureFixture[str]
) -> None:
    capsys.readouterr()
    code = main(["ci", "logs", "812"])
    out, err = capsys.readouterr()
    assert code == 0
    assert out.splitlines() == ["── Step 1: Set up job (in_progress) ──"]
    assert RUNNING_NOTE in " ".join(err.split())


def test_logs_of_a_running_job_warn_in_json(running_job: Backend, run: Runner) -> None:
    result = run("logs", "812", "--json")
    assert result.exit_code == 0
    assert json.loads(result.output)["data"]["warnings"] == [RUNNING_NOTE]


NAMED_KEY_REFUSAL = {
    "detail": {
        "error_code": "api_key_endpoint_not_allowed",
        "message": "This API key cannot access this endpoint; use the dashboard's default API key.",
    }
}
NAMED_KEY_MESSAGE = (
    "This API key can't read CI jobs. "
    "Run 'celesto auth login' with your dashboard's default API key."
)


@pytest.mark.parametrize(
    ("args", "route"),
    [
        (("jobs", "list"), JOBS_PAGE),
        (("jobs", "show", "812"), JOB_812),
        (("logs", "812"), JOB_812),
        (("runners", "list"), "/v1/integrations/github/actions/runners"),
    ],
)
def test_named_key_gets_the_recovery_message_in_json(
    backend: Backend, run: Runner, args: tuple[str, ...], route: str
) -> None:
    backend.serve(route, NAMED_KEY_REFUSAL, status=403)
    result = run(*args, "--json")
    assert result.exit_code == 1
    assert json.loads(result.output)["error"] == {
        "code": "api_key_endpoint_not_allowed",
        "message": NAMED_KEY_MESSAGE,
    }


def test_named_key_gets_the_recovery_message_for_people(
    backend: Backend, capsys: pytest.CaptureFixture[str]
) -> None:
    backend.serve("/v1/integrations/github/actions/runners", NAMED_KEY_REFUSAL, status=403)
    capsys.readouterr()
    code = main(["ci", "runners", "list"])
    assert code == 1
    assert NAMED_KEY_MESSAGE in " ".join(capsys.readouterr().err.replace("│", " ").split())


def _error(result: Ran) -> dict[str, Any]:
    assert result.exit_code == 1, result.output
    error: dict[str, Any] = json.loads(result.output)["error"]
    return error


def test_missing_login_says_to_log_in(backend: Backend, run: Runner) -> None:
    _credentials.CREDENTIALS_PATH.unlink()
    assert _error(run("runners", "list", "--json")) == {
        "code": "not_logged_in",
        "message": "Your Celesto login is missing or invalid. Run 'celesto auth login'.",
    }
    assert backend.requests == []


def test_unreadable_login_says_to_log_in(backend: Backend, run: Runner) -> None:
    _credentials.CREDENTIALS_PATH.write_text(
        json.dumps({"api_key": "cel_test_key", "email": "ci@example.invalid", "base_url": 7})
    )
    assert _error(run("runners", "list", "--json")) == {
        "code": "not_logged_in",
        "message": "Your Celesto login is missing or invalid. Run 'celesto auth login'.",
    }


def test_refused_key_says_to_log_in_again(backend: Backend, run: Runner) -> None:
    backend.serve("/v1/integrations/github/actions/runners", {"detail": "Unauthorized."}, 401)
    assert _error(run("runners", "list", "--json")) == {
        "code": "unauthorized",
        "message": "Your Celesto API key was refused. Run 'celesto auth login'.",
    }


@pytest.mark.parametrize("route", [f"{JOB_812}/steps", f"{JOB_812}/steps/4/log"])
def test_log_github_no_longer_has_points_at_github(
    finished_job: Backend, run: Runner, route: str
) -> None:
    finished_job.serve(
        JOB_812,
        _job(812, "failure", native_status="completed", github_job_url="https://github.com/j/812"),
    )
    finished_job.serve(route, {"detail": "GitHub no longer has this job"}, 404)
    assert _error(run("logs", "812", "--step", "4", "--json")) == {
        "code": "ci_log_unavailable",
        "message": "GitHub no longer has the log for job 812. "
        "Open https://github.com/j/812 to check it.",
    }


def test_github_outage_says_to_retry(finished_job: Backend, run: Runner) -> None:
    finished_job.serve(f"{JOB_812}/steps", {"detail": "GitHub is unavailable. Try again."}, 502)
    assert _error(run("logs", "812", "--json")) == {
        "code": "github_unavailable",
        "message": "GitHub is unavailable right now. Retry in a minute.",
    }


def test_lost_github_app_access_says_to_check_the_installation(
    finished_job: Backend, run: Runner
) -> None:
    finished_job.serve(
        f"{JOB_812}/steps",
        {"detail": "GitHub access is unavailable. Check the App installation."},
        502,
    )
    assert _error(run("logs", "812", "--json")) == {
        "code": "github_access_denied",
        "message": "Celesto's GitHub App can't read this repository. "
        "Check its installation in your GitHub organization's settings.",
    }


def test_a_gateway_502_is_not_blamed_on_github(backend: Backend, run: Runner) -> None:
    backend.serve(JOBS_PAGE, {"detail": "Bad Gateway"}, 502)
    assert _error(run("jobs", "list", "--json")) == {
        "code": "http_502",
        "message": "Celesto CI returned HTTP 502. Retry, then check 'celesto auth status'.",
    }


def test_runners_with_a_null_list_is_an_invalid_response(backend: Backend, run: Runner) -> None:
    backend.serve("/v1/integrations/github/actions/runners", {"runners": None})
    human = run("runners", "list")
    assert human.exit_code == 1 and "Traceback" not in human.output
    assert _error(run("runners", "list", "--json"))["code"] == "cloud_invalid_response"


def test_jobs_with_a_null_list_is_an_invalid_response(backend: Backend, run: Runner) -> None:
    backend.serve(JOBS_PAGE, {"items": None, "total": 0})
    assert _error(run("jobs", "list", "--json"))["code"] == "cloud_invalid_response"


def test_logs_with_a_null_step_list_is_an_invalid_response(
    finished_job: Backend, run: Runner
) -> None:
    finished_job.serve(f"{JOB_812}/steps", {"steps": None})
    assert _error(run("logs", "812", "--json"))["code"] == "cloud_invalid_response"


def test_logs_piped_into_a_reader_that_exits_early_ends_quietly(
    finished_job: Backend, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    sink = (tmp_path / "closed").open("w")

    class ClosedPipe(io.TextIOWrapper):
        def write(self, _text: str) -> int:
            raise BrokenPipeError

    monkeypatch.setattr(sys, "stdout", ClosedPipe(io.FileIO(sink.fileno(), "w", closefd=False)))
    assert main(["ci", "logs", "812"]) == 0
    sink.close()


@pytest.mark.parametrize(
    ("args", "route", "body"),
    [
        (("runners", "list"), "/v1/integrations/github/actions/runners", {"runners": [None]}),
        (("runners", "list"), "/v1/integrations/github/actions/runners", {"runners": [{}]}),
        (("jobs", "list"), JOBS_PAGE, {"items": ["812"], "total": 1}),
        (("logs", "812"), f"{JOB_812}/steps", {"steps": [None]}),
    ],
)
def test_malformed_items_are_an_invalid_response_not_a_traceback(
    backend: Backend, run: Runner, args: tuple[str, ...], route: str, body: Any
) -> None:
    backend.serve(JOB_812, _job(812, "failure", native_status="completed"))
    backend.serve(route, body)
    human = run(*args)
    assert human.exit_code == 1 and "Traceback" not in human.output
    # Items that aren't objects fail in --json too; an object missing fields
    # passes through there, since --json returns the backend's objects as-is.
    if body != {"runners": [{}]}:
        assert _error(run(*args, "--json"))["code"] == "cloud_invalid_response"


@pytest.mark.parametrize(
    ("args", "route", "body"),
    [
        (("runners", "list"), "/v1/integrations/github/actions/runners", RUNNERS),
        (
            ("jobs", "list"),
            JOBS_PAGE,
            {"items": [{"job_id": 812, "status": "failure"}], "total": 1},
        ),
        (("jobs", "show", "812"), JOB_812, {"job_id": 812, "status": "failure"}),
    ],
)
def test_text_output_into_a_closed_pipe_ends_quietly(
    backend: Backend,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    args: tuple[str, ...],
    route: str,
    body: Any,
) -> None:
    backend.serve(route, body)
    sink = (tmp_path / "closed").open("w")

    class ClosedPipe(io.TextIOWrapper):
        def write(self, _text: str) -> int:
            raise BrokenPipeError

    monkeypatch.setattr(sys, "stdout", ClosedPipe(io.FileIO(sink.fileno(), "w", closefd=False)))
    assert main(["ci", *args]) == 0
    sink.close()


def test_logs_into_a_pipe_that_closed_early_exits_cleanly(
    finished_job: Backend, tmp_path: Path
) -> None:
    """`celesto ci logs 812 | head -1` in a real process.

    Short output sits in Python's stdout buffer, so the broken pipe surfaces
    only at the final flush; a reader already gone makes that deterministic.
    """
    home = tmp_path / "home"
    (home / ".celesto").mkdir(parents=True)
    (home / ".celesto" / "credentials").write_text(_credentials.CREDENTIALS_PATH.read_text())
    env = {key: value for key, value in os.environ.items() if key != "CELESTO_API_KEY"}
    env["HOME"] = str(home)
    read_end, write_end = os.pipe()
    os.close(read_end)
    try:
        process = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; from celesto.cli.main import main; sys.exit(main())",
                "ci",
                "logs",
                "812",
            ],
            stdout=write_end,
            stderr=subprocess.PIPE,
            env=env,
            timeout=60,
        )
    finally:
        os.close(write_end)
    stderr = process.stderr.decode()
    assert process.returncode == 0, stderr
    assert "BrokenPipeError" not in stderr and "Traceback" not in stderr


def test_a_redirect_is_not_read_as_job_data(backend: Backend, run: Runner) -> None:
    backend.serve(JOB_812, {"job_id": 812, "status": "success"}, 302)
    assert _error(run("jobs", "show", "812", "--json")) == {
        "code": "http_302",
        "message": "Celesto CI returned HTTP 302. Retry, then check 'celesto auth status'.",
    }


@pytest.mark.parametrize("total", [None, "40", True])
def test_jobs_page_without_an_integer_total_is_an_invalid_response(
    backend: Backend, run: Runner, total: Any
) -> None:
    body: dict[str, Any] = {"items": [_job(812, "success")]}
    if total is not None:
        body["total"] = total
    backend.serve(JOBS_PAGE, body)
    assert _error(run("jobs", "list", "--json"))["code"] == "cloud_invalid_response"


def test_unreachable_backend_says_to_check_the_connection(backend: Backend, run: Runner) -> None:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        closed = probe.getsockname()[1]
    _credentials.write_credentials(
        api_key="cel_test_key", email="ci@example.invalid", base_url=f"http://127.0.0.1:{closed}"
    )
    assert _error(run("runners", "list", "--json")) == {
        "code": "cloud_transport_error",
        "message": "Could not reach Celesto (ConnectError). Check your connection and retry.",
    }


def test_unreadable_answer_says_to_retry_or_update(backend: Backend, run: Runner) -> None:
    backend.serve("/v1/integrations/github/actions/runners", ["not", "an", "object"])
    assert _error(run("runners", "list", "--json")) == {
        "code": "cloud_invalid_response",
        "message": "Celesto returned an invalid response. "
        "Retry, or run 'celesto update' if it keeps happening.",
    }


def test_other_statuses_name_the_status(backend: Backend, run: Runner) -> None:
    backend.serve(JOBS_PAGE, {"detail": "boom"}, 500)
    assert _error(run("jobs", "list", "--json")) == {
        "code": "http_500",
        "message": "Celesto CI returned HTTP 500. Retry, then check 'celesto auth status'.",
    }


@pytest.mark.parametrize(
    ("flag", "length", "limit"),
    [("--search", 201, 200), ("--repo", 256, 255), ("--workflow", 256, 255)],
)
def test_filters_longer_than_the_backend_allows_are_refused(
    backend: Backend, flag: str, length: int, limit: int
) -> None:
    result = CliRunner().invoke(build_cli(), ["ci", "jobs", "list", flag, "x" * length])
    assert result.exit_code == 2
    assert f"{flag} can be at most {limit} characters." in result.output
    assert backend.requests == []


def test_jobs_list_at_100_suggests_narrowing(backend: Backend, run: Runner) -> None:
    backend.serve(JOBS_PAGE, _page([_job(n, "success") for n in range(100)], total=340))
    result = run("jobs", "list", "--limit", "100")
    assert result.output.splitlines()[-1] == (
        "Showing 100 of 340 jobs. Narrow the list with --status, --repo or --search."
    )


ENV_NAMED_KEY_MESSAGE = (
    "This API key can't read CI jobs. Set CELESTO_API_KEY to your dashboard's "
    "default API key, or unset it and run 'celesto auth login'."
)


def _use_environment_key(monkeypatch: pytest.MonkeyPatch, backend: Backend, key: str) -> None:
    """Set CELESTO_API_KEY and point the transport's default base URL at the stub.

    With the variable set, the transport ignores the stored login's base URL,
    so its keyword default must change, or the request would go to production.
    """
    from celesto._cloud import _CloudComputer

    defaults = _CloudComputer.__init__.__kwdefaults__
    assert defaults is not None
    monkeypatch.setitem(defaults, "base_url", backend.url)
    monkeypatch.setenv("CELESTO_API_KEY", key)


def test_named_key_from_the_environment_says_to_replace_it(
    backend: Backend, run: Runner, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_environment_key(monkeypatch, backend, "cel_named_key")
    backend.serve(JOBS_PAGE, NAMED_KEY_REFUSAL, status=403)
    assert _error(run("jobs", "list", "--json"))["message"] == ENV_NAMED_KEY_MESSAGE


def test_refused_key_from_the_environment_says_to_replace_it(
    backend: Backend, run: Runner, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_environment_key(monkeypatch, backend, "cel_bad_key")
    backend.serve(JOBS_PAGE, {"detail": "Unauthorized."}, 401)
    assert _error(run("jobs", "list", "--json"))["message"] == (
        "Your Celesto API key was refused. Set CELESTO_API_KEY to a valid key, "
        "or unset it and run 'celesto auth login'."
    )


def test_more_jobs_hint_keeps_the_filters(backend: Backend, run: Runner) -> None:
    backend.serve(JOBS_PAGE, _page([_job(812, "failure")], total=9))
    result = run(
        "jobs",
        "list",
        "--status",
        "failed",
        "--repo",
        "acme/api",
        "--search",
        "fix login",
        "--limit",
        "1",
    )
    assert result.output.splitlines()[-1] == (
        "Showing 1 of 9 jobs. Run 'celesto ci jobs list --status failed --repo acme/api "
        "--search 'fix login' --limit 100' to see more."
    )


@pytest.mark.parametrize(
    ("args", "command", "recovery"),
    [
        (["ci", "jobs", "list", "--limit", "101"], "ci.jobs.list", "celesto ci jobs list --help"),
        (["ci", "runners", "list", "--bogus"], "ci.runners.list", "celesto ci runners list --help"),
        (["ci", "logs", "abc"], "ci.logs", "celesto ci logs --help"),
    ],
)
def test_usage_errors_name_the_ci_command(
    capsys: pytest.CaptureFixture[str], args: list[str], command: str, recovery: str
) -> None:
    capsys.readouterr()
    assert main([*args, "--json"]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == command
    assert payload["error"]["recovery"] == f"Run '{recovery}' for usage."

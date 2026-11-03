"""Handlers for ``celesto ci``: Celesto CI jobs, logs and machine sizes."""

from __future__ import annotations

import json
from types import ModuleType
from typing import Any

import httpx

from celesto._cloud import _CloudComputer
from celesto.cli.output import console_stderr, emit_error, emit_json, render_error


class CIError(Exception):
    """A failure the CLI reports with a code and a recovery command."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class _Connection:
    """The cloud transport's API key, base URL and organization, used for CI reads.

    CI routes answer plain JSON objects, so responses are read as JSON rather
    than through the generated models; the generated modules still build each
    request, so paths and parameters follow the backend schema.
    """

    def __init__(self) -> None:
        self._transport = _CloudComputer()

    def close(self) -> None:
        self._transport.close()

    def get(
        self, endpoint: ModuleType, *, job_id: int | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        if job_id is not None:
            kwargs["job_id"] = job_id
        request = endpoint._get_kwargs(
            x_current_organization=self._transport._organization, **kwargs
        )
        try:
            response = self._transport._client.get_httpx_client().request(**request)
        except httpx.TransportError as exc:
            raise CIError(
                "cloud_transport_error",
                f"Could not reach Celesto ({type(exc).__name__}). Check your connection and retry.",
            ) from None
        if response.status_code >= 400:
            raise _api_error(response.status_code, response.content, job_id=job_id)
        try:
            body = response.json()
        except ValueError:
            body = None
        if not isinstance(body, dict):
            raise CIError(
                "cloud_invalid_response",
                "Celesto returned an invalid response. "
                "Retry, or run 'celesto update' if it keeps happening.",
            )
        return body


def _api_error(status_code: int, content: bytes, *, job_id: int | None = None) -> CIError:
    # Interpret only known statuses and public error codes; never print
    # arbitrary server text, which can echo credentials.
    if status_code == 404 and job_id is not None:
        return CIError(
            "ci_job_not_found",
            f"CI job {job_id} was not found. Run 'celesto ci jobs list' to see your jobs.",
        )
    try:
        body = json.loads(content)
    except (ValueError, RecursionError):
        body = None
    detail = body.get("detail") if isinstance(body, dict) else None
    code = detail.get("error_code") if isinstance(detail, dict) else None
    if status_code == 403 and code == "api_key_endpoint_not_allowed":
        return CIError(
            code,
            "This API key can't read CI jobs. "
            "Run 'celesto auth login' with your dashboard's default API key.",
        )
    if status_code == 401:
        return CIError(
            "unauthorized", "Your Celesto API key was refused. Run 'celesto auth login'."
        )
    return CIError(
        f"http_{status_code}",
        f"Celesto CI returned HTTP {status_code}. Retry, then check 'celesto auth status'.",
    )


def _fail(command: str, error: Exception, *, json_output: bool) -> int:
    code = error.code if isinstance(error, CIError) else "invalid_configuration"
    if json_output:
        return emit_error(command, code, str(error))
    render_error(str(error))
    return 1


def _run(command: str, json_output: bool, read: Any) -> tuple[int, dict[str, Any] | None]:
    """Open a connection, run ``read(connection)``, and report any failure."""
    try:
        connection = _Connection()
    except ValueError as exc:
        return _fail(command, exc, json_output=json_output), None
    try:
        return 0, read(connection)
    except CIError as exc:
        return _fail(command, exc, json_output=json_output), None
    finally:
        connection.close()


def _gib(megabytes: int) -> str:
    return f"{megabytes / 1024:g} GiB"


def run_runners_list(*, json_output: bool) -> int:
    """Handle ``celesto ci runners list``."""
    from _celesto_cloud_api.api.git_hub_actions_on_celesto import (
        list_runners_v1_integrations_github_actions_runners_get as endpoint,
    )

    command = "ci.runners.list"
    code, data = _run(command, json_output, lambda connection: connection.get(endpoint))
    if data is None:
        return code
    if json_output:
        emit_json(command, 0, data=data)
        return 0
    print(f"{'LABEL':<18}  {'VCPU':>4}  {'RAM':>7}  {'DISK':>8}")
    for runner in data.get("runners", []):
        ram, disk = _gib(runner["ram_mb"]), _gib(runner["disk_size_mb"])
        print(f"{runner['label']:<18}  {runner['vcpus']:>4}  {ram:>7}  {disk:>8}")
    return 0


# `--status` names on the command line, and the jobs page tab each one reads.
STATUS_TABS = {
    "in-progress": "in_progress",
    "needs-action": "needs_action",
    "completed": "completed",
    "failed": "failed",
    "passed": "passed",
}


def run_jobs_list(
    *,
    status: str | None,
    repository: str | None,
    workflow: str | None,
    search: str,
    limit: int,
    json_output: bool,
) -> int:
    """Handle ``celesto ci jobs list``."""
    from _celesto_cloud_api.api.git_hub_actions_on_celesto import (
        page_jobs_v1_integrations_github_actions_jobs_page_get as endpoint,
    )
    from _celesto_cloud_api.models import PageJobsV1IntegrationsGithubActionsJobsPageGetTab as Tab
    from _celesto_cloud_api.types import UNSET

    command = "ci.jobs.list"
    code, data = _run(
        command,
        json_output,
        lambda connection: connection.get(
            endpoint,
            tab=Tab(STATUS_TABS[status]) if status else Tab.ALL,
            q=search,
            repository=repository or UNSET,
            workflow=workflow or UNSET,
            page=0,
            page_size=limit,
        ),
    )
    if data is None:
        return code
    jobs = data.get("items", [])
    total = data.get("total", len(jobs))
    if json_output:
        emit_json(command, 0, data={"jobs": jobs, "total": total})
        return 0
    if not jobs:
        print("No CI jobs match.")
        return 0
    rows = [
        [
            str(job.get("job_id", "")),
            str(job.get("status") or ""),
            str(job.get("repository") or ""),
            str(job.get("workflow_name") or "-"),
            str(job.get("job_name") or "-"),
            str(job.get("head_branch") or "-"),
            str(job.get("created_at") or ""),
        ]
        for job in jobs
    ]
    header = ["JOB", "STATUS", "REPOSITORY", "WORKFLOW", "JOB", "BRANCH", "CREATED"]
    widths = [max(len(row[i]) for row in [header, *rows]) for i in range(len(header))]
    for row in [header, *rows]:
        print(
            "  ".join(cell.ljust(width) for cell, width in zip(row, widths, strict=True)).rstrip()
        )
    if total > len(jobs):
        print(
            f"Showing {len(jobs)} of {total} jobs. "
            "Run 'celesto ci jobs list --limit 100' to see more."
        )
    return 0


def run_jobs_show(*, job_id: int, json_output: bool) -> int:
    """Handle ``celesto ci jobs show``."""
    from _celesto_cloud_api.api.git_hub_actions_on_celesto import (
        job_details_v1_integrations_github_actions_jobs_job_id_get as endpoint,
    )

    command = "ci.jobs.show"
    code, job = _run(
        command, json_output, lambda connection: connection.get(endpoint, job_id=job_id)
    )
    if job is None:
        return code
    if json_output:
        emit_json(command, 0, data=job)
        return 0
    status = str(job.get("status") or "")
    if job.get("status_message"):
        status += f" ({job['status_message']})"
    for label, value in (
        ("Job", job.get("job_id")),
        ("Status", status),
        ("Repository", job.get("repository")),
        ("Workflow", job.get("workflow_name")),
        ("Job name", job.get("job_name")),
        ("Branch", job.get("head_branch")),
        ("Commit", job.get("head_sha")),
        ("Machine", job.get("size_id")),
        ("Created", job.get("created_at")),
        ("Started", job.get("execution_started_at")),
        ("Finished", job.get("execution_completed_at")),
        ("GitHub", job.get("github_job_url")),
    ):
        if value not in (None, ""):
            print(f"{label + ':':<12} {value}")
    return 0


# The backend returns at most this many lines per step (github_actions_logs.py).
MAX_STEP_LINES = "5,000"


def run_logs(*, job_id: int, step: int | None, json_output: bool) -> int:
    """Handle ``celesto ci logs``: every step's log in order, or one step's."""
    from _celesto_cloud_api.api.git_hub_actions_on_celesto import (
        job_details_v1_integrations_github_actions_jobs_job_id_get as details_endpoint,
    )
    from _celesto_cloud_api.api.git_hub_actions_on_celesto import (
        job_step_log_v1_integrations_github_actions_jobs_job_id_steps_number_log_get as log_endpoint,  # noqa: E501 - generated module name
    )
    from _celesto_cloud_api.api.git_hub_actions_on_celesto import (
        job_steps_v1_integrations_github_actions_jobs_job_id_steps_get as steps_endpoint,
    )

    command = "ci.logs"

    def read(connection: _Connection) -> dict[str, Any]:
        job = connection.get(details_endpoint, job_id=job_id)
        steps = connection.get(steps_endpoint, job_id=job_id).get("steps", [])
        if step is not None:
            steps = [item for item in steps if item.get("number") == step]
            if not steps:
                raise CIError(
                    "ci_step_not_found",
                    f"Job {job_id} has no step {step}. "
                    f"Run 'celesto ci logs {job_id}' to see all steps.",
                )
        result = []
        for item in steps:
            log = connection.get(log_endpoint, job_id=job_id, number=item["number"])
            result.append(
                {
                    "number": item["number"],
                    "name": item.get("name"),
                    "status": item.get("status"),
                    "conclusion": item.get("conclusion"),
                    "lines": log.get("lines", []),
                    "truncated": bool(log.get("truncated")),
                }
            )
        warnings = []
        if job.get("native_status") != "completed":
            warnings.append(
                f"Job {job_id} is still running, so its log may be incomplete. "
                f"Run 'celesto ci logs {job_id}' again when it finishes."
            )
        return {"job_id": job_id, "steps": result, "warnings": warnings}

    code, data = _run(command, json_output, read)
    if data is None:
        return code
    if json_output:
        emit_json(command, 0, data=data)
        return 0
    for item in data["steps"]:
        print(
            f"── Step {item['number']}: {item['name']} ({item['conclusion'] or item['status']}) ──"
        )
        if item["truncated"]:
            print(f"Only the last {MAX_STEP_LINES} lines of this step are shown.")
        for line in item["lines"]:
            print(line.get("text", ""))
    for warning in data["warnings"]:
        console_stderr().print(warning, style="yellow", highlight=False)
    return 0

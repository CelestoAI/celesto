"""Handlers for ``celesto ci``: Celesto CI jobs, logs and machine sizes."""

from __future__ import annotations

from types import ModuleType
from typing import Any

import httpx

from celesto._cloud import _CloudComputer
from celesto.cli.output import emit_error, emit_json, render_error


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

    def get(self, endpoint: ModuleType, **kwargs: Any) -> dict[str, Any]:
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
            raise _api_error(response.status_code, response.content)
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


def _api_error(status_code: int, content: bytes) -> CIError:
    # Interpret only known statuses and public error codes; never print
    # arbitrary server text, which can echo credentials.
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


def _gib(megabytes: int) -> str:
    return f"{megabytes / 1024:g} GiB"


def run_runners_list(*, json_output: bool) -> int:
    """Handle ``celesto ci runners list``."""
    from _celesto_cloud_api.api.git_hub_actions_on_celesto import (
        list_runners_v1_integrations_github_actions_runners_get as endpoint,
    )

    command = "ci.runners.list"
    try:
        connection = _Connection()
    except ValueError as exc:
        return _fail(command, exc, json_output=json_output)
    try:
        data = connection.get(endpoint)
    except CIError as exc:
        return _fail(command, exc, json_output=json_output)
    finally:
        connection.close()
    if json_output:
        emit_json(command, 0, data=data)
        return 0
    print(f"{'LABEL':<18}  {'VCPU':>4}  {'RAM':>7}  {'DISK':>8}")
    for runner in data.get("runners", []):
        ram, disk = _gib(runner["ram_mb"]), _gib(runner["disk_size_mb"])
        print(f"{runner['label']:<18}  {runner['vcpus']:>4}  {ram:>7}  {disk:>8}")
    return 0

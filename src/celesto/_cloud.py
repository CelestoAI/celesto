"""Cloud computer orchestration above the generated HTTP client."""

from __future__ import annotations

import json
import math
import os
import time
from collections.abc import Callable, Iterator
from typing import Any, TypeVar
from urllib.parse import quote, urlsplit

import httpx

from _celesto_cloud_api.api.computers import (
    create_computer_v1_computers_post as create,
)
from _celesto_cloud_api.api.computers import (
    create_terminal_session_v1_computers_computer_id_terminals_post as create_terminal,
)
from _celesto_cloud_api.api.computers import (
    delete_computer_v1_computers_computer_id_delete as delete,
)
from _celesto_cloud_api.api.computers import (
    exec_on_computer_v1_computers_computer_id_exec_post as execute,
)
from _celesto_cloud_api.api.computers import (
    get_computer_v1_computers_computer_id_get as retrieve,
)
from _celesto_cloud_api.api.computers import (
    list_computer_published_ports_v1_computers_computer_id_published_ports_get as list_ports,
)
from _celesto_cloud_api.api.computers import (
    publish_computer_port_v1_computers_computer_id_published_ports_post as publish_port,
)
from _celesto_cloud_api.api.computers import (
    unpublish_computer_port_v1_computers_computer_id_published_ports_port_delete as unpublish_port,
)
from _celesto_cloud_api.client import AuthenticatedClient
from _celesto_cloud_api.errors import UnexpectedStatus
from _celesto_cloud_api.models.computer_create_request import ComputerCreateRequest
from _celesto_cloud_api.models.computer_exec_request import ComputerExecRequest
from _celesto_cloud_api.models.computer_exec_response import ComputerExecResponse
from _celesto_cloud_api.models.computer_published_port_create_request import (
    ComputerPublishedPortCreateRequest,
)
from _celesto_cloud_api.models.computer_published_port_response import ComputerPublishedPortResponse
from _celesto_cloud_api.models.computer_response import ComputerResponse
from _celesto_cloud_api.models.computer_terminal_session_request import (
    ComputerTerminalSessionRequest,
)
from _celesto_cloud_api.models.computer_terminal_session_response import (
    ComputerTerminalSessionResponse,
)
from _celesto_cloud_api.types import UNSET, Unset
from celesto._streaming import iter_bounded_lines, iter_sse_data, parse_command_event
from celesto._terminal import TerminalConnection, cloud_terminal_connection
from celesto.exceptions import CelestoError, CloudAPIError, VMNotFoundError
from celesto.types import CommandEvent, CommandExitEvent, CommandResult, PublishedPort

T = TypeVar("T")
_MAX_ERROR_BODY_BYTES = 64 * 1024


class _CloudComputer:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = "https://api.celesto.ai",
        organization_id: str | None = None,
        startup_timeout: float = 120,
        cleanup_timeout: float = 120,
        vcpus: int | None = None,
        ram_mb: int | None = None,
        disk_size_mb: int | None = None,
        image: str = "ubuntu-desktop-24.04",
        template_id: str | None = None,
        template_version: str | None = None,
        external_volume_enabled: bool = False,
    ) -> None:
        key = api_key if api_key is not None else os.environ.get("CELESTO_API_KEY")
        if not isinstance(key, str) or not key.strip():
            raise ValueError("Set CELESTO_API_KEY or pass api_key= to use a cloud computer.")
        url = urlsplit(base_url)
        local_http = url.scheme == "http" and url.hostname in {"localhost", "127.0.0.1", "::1"}
        if (
            not url.hostname
            or (url.scheme != "https" and not local_http)
            or url.username
            or url.password
            or url.query
            or url.fragment
            or url.path not in ("", "/")
        ):
            raise ValueError(
                "base_url must be an HTTPS origin without /v1; HTTP is allowed locally."
            )
        for name, value in (
            ("startup_timeout", startup_timeout),
            ("cleanup_timeout", cleanup_timeout),
        ):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value <= 0
            ):
                raise ValueError(f"{name} must be a positive, finite number of seconds.")
        self._client = AuthenticatedClient(
            base_url=base_url.rstrip("/"),
            token=key,
            timeout=httpx.Timeout(30),
            raise_on_unexpected_status=True,
        )
        self._organization = organization_id if organization_id is not None else UNSET
        self._body = ComputerCreateRequest(
            vcpus=vcpus if vcpus is not None else UNSET,
            ram_mb=ram_mb if ram_mb is not None else UNSET,
            disk_size_mb=disk_size_mb if disk_size_mb is not None else UNSET,
            image=image,
            template_id=template_id if template_id is not None else UNSET,
            template_version=template_version if template_version is not None else UNSET,
            external_volume_enabled=external_volume_enabled,
        )
        self._startup_timeout = startup_timeout
        self._cleanup_timeout = cleanup_timeout
        self.vm_id: str | None = None

    def _call(
        self,
        endpoint: Callable[..., Any],
        expected: type[T],
        *,
        retain_error_detail: bool = True,
        uncertain_mutation: str | None = None,
        **kwargs: Any,
    ) -> T:
        try:
            response = endpoint(
                client=self._client, x_current_organization=self._organization, **kwargs
            )
        except UnexpectedStatus as exc:
            if exc.status_code == 404 and self.vm_id is not None:
                raise VMNotFoundError(self.vm_id) from None
            raise self._api_error(
                exc.status_code, exc.content if retain_error_detail else b""
            ) from None
        except httpx.TransportError as exc:
            raise CelestoError(
                f"Cloud request failed ({type(exc).__name__}); its outcome may be unknown. "
                "Check your computers before retrying; no request was replayed."
            ) from None
        except (ValueError, KeyError, TypeError):
            raise self._invalid_response(uncertain_mutation) from None
        if response.status_code >= 400:
            raise self._api_error(
                response.status_code, response.content if retain_error_detail else b""
            )
        if not isinstance(response.parsed, expected):
            raise self._invalid_response(uncertain_mutation)
        # Generated list parsers iterate any JSON value, including an empty object.
        if expected is list and not isinstance(json.loads(response.content), list):
            raise self._invalid_response(uncertain_mutation)
        return response.parsed

    @staticmethod
    def _invalid_response(uncertain_mutation: str | None = None) -> CelestoError:
        if uncertain_mutation is not None:
            return CelestoError(
                f"Cloud returned an invalid response after trying to {uncertain_mutation}. "
                "The operation may have succeeded; call published_ports() before retrying."
            )
        return CelestoError(
            "Cloud returned an invalid response; check the API version before retrying."
        )

    @staticmethod
    def _api_error(status_code: int, content: bytes) -> CloudAPIError:
        detail = None
        if status_code == 400:
            try:
                body = json.loads(content)
            except (ValueError, RecursionError):
                pass
            else:
                if isinstance(body, dict) and isinstance(body.get("detail"), str):
                    detail = body["detail"]
        return CloudAPIError(status_code, detail=detail)

    def _get(self) -> ComputerResponse:
        return self._call(retrieve.sync_detailed, ComputerResponse, computer_id=self.vm_id)

    def start(self) -> None:
        # Exactly one create request. Never retry a potentially billable allocation.
        computer = self._call(create.sync_detailed, ComputerResponse, body=self._body)
        self.vm_id = computer.id
        deadline = time.monotonic() + self._startup_timeout
        while computer.status != "running":
            if computer.status not in {"creating", "starting", "restoring", "pending"}:
                raise CelestoError(f"Computer '{self.vm_id}' is {computer.status}; call delete().")
            self._wait(deadline, "start")
            computer = self._get()

    @staticmethod
    def validate_command(command: str, timeout: int) -> None:
        if len(command) > 10000 or timeout > 300:
            raise ValueError(
                "Cloud commands allow at most 10,000 characters and a 300-second timeout."
            )

    def run(self, command: str, timeout: int = 30) -> CommandResult:
        self.validate_command(command, timeout)
        self._client.get_httpx_client().timeout = httpx.Timeout(timeout + 10)
        try:
            result = self._call(
                execute.sync_detailed,
                ComputerExecResponse,
                computer_id=self.vm_id,
                body=ComputerExecRequest(command=command, timeout=timeout),
            )
        finally:
            self._client.get_httpx_client().timeout = httpx.Timeout(30)
        return CommandResult(stdout=result.stdout, stderr=result.stderr, exit_code=result.exit_code)

    @staticmethod
    def _published_port(
        result: ComputerPublishedPortResponse, *, uncertain_mutation: str | None = None
    ) -> PublishedPort:
        try:
            # Convert only documented fields; generated UNSET and extra fields stay private.
            return PublishedPort(
                computer_id=result.computer_id,
                port=result.port,
                status=result.status,
                id=None if isinstance(result.id, Unset) else result.id,
                url=None if isinstance(result.url, Unset) else result.url,
                created_at=None if isinstance(result.created_at, Unset) else result.created_at,
            )
        except ValueError:
            raise _CloudComputer._invalid_response(uncertain_mutation) from None

    def publish_port(self, port: int) -> PublishedPort:
        mutation = f"publish port {port}"
        try:
            result = self._call(
                publish_port.sync_detailed,
                ComputerPublishedPortResponse,
                retain_error_detail=False,
                uncertain_mutation=mutation,
                computer_id=self.vm_id,
                body=ComputerPublishedPortCreateRequest(port=port),
            )
        except CloudAPIError as exc:
            if exc.status_code == 400:
                raise CloudAPIError(
                    400,
                    recovery=f"Port {port} cannot be published; choose another port and retry.",
                ) from None
            raise
        return self._published_port(result, uncertain_mutation=mutation)

    def published_ports(self) -> list[PublishedPort]:
        results = self._call(
            list_ports.sync_detailed,
            list,
            retain_error_detail=False,
            computer_id=self.vm_id,
        )
        return [self._published_port(result) for result in results]

    def unpublish_port(self, port: int) -> PublishedPort:
        mutation = f"unpublish port {port}"
        result = self._call(
            unpublish_port.sync_detailed,
            ComputerPublishedPortResponse,
            retain_error_detail=False,
            uncertain_mutation=mutation,
            computer_id=self.vm_id,
            port=port,
        )
        return self._published_port(result, uncertain_mutation=mutation)

    def run_stream(self, command: str, timeout: int = 30) -> Iterator[CommandEvent]:
        """Execute a command and yield parsed cloud SSE events as they arrive."""
        self.validate_command(command, timeout)
        return self._iter_command_events(command, timeout)

    def terminal(self, *, terminal_id: str | None = None) -> TerminalConnection:
        """Create or reauthorize a durable cloud terminal session."""
        response = self._call(
            create_terminal.sync_detailed,
            ComputerTerminalSessionResponse,
            computer_id=self.vm_id,
            body=ComputerTerminalSessionRequest(
                terminal_id=terminal_id if terminal_id is not None else UNSET
            ),
        )
        return cloud_terminal_connection(
            terminal_id=response.terminal_id,
            gateway_url=response.gateway_url,
            token=response.token,
            expires_at=response.expires_at,
        )

    def _iter_command_events(self, command: str, timeout: int) -> Iterator[CommandEvent]:
        client = self._client.get_httpx_client()
        headers = {"Accept": "text/event-stream"}
        if isinstance(self._organization, str):
            headers["x-current-organization"] = self._organization
        path = f"/v1/computers/{quote(str(self.vm_id), safe='')}/exec/stream"
        saw_exit = False
        try:
            with client.stream(
                "POST",
                path,
                headers=headers,
                json=ComputerExecRequest(command=command, timeout=timeout).to_dict(),
                timeout=httpx.Timeout(timeout + 10),
            ) as response:
                if response.status_code >= 400:
                    content = bytearray()
                    for chunk in response.iter_bytes():
                        content.extend(chunk[: _MAX_ERROR_BODY_BYTES - len(content)])
                        if len(content) >= _MAX_ERROR_BODY_BYTES:
                            break
                    if response.status_code == 404 and self.vm_id is not None:
                        raise VMNotFoundError(self.vm_id)
                    raise self._api_error(response.status_code, bytes(content))
                lines = iter_bounded_lines(response.iter_bytes(chunk_size=64 * 1024))
                for data in iter_sse_data(lines):
                    event = parse_command_event(data)
                    if isinstance(event, CommandExitEvent):
                        saw_exit = True
                        response.close()
                    yield event
                    if saw_exit:
                        break
        except httpx.TransportError as exc:
            raise CelestoError(
                f"Cloud command stream failed ({type(exc).__name__}); the command may still "
                "be running. Check your computers before retrying."
            ) from None
        if not saw_exit:
            raise CelestoError("Command stream ended before the command exited.")

    def _wait(self, deadline: float, action: str) -> None:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise CelestoError(
                f"Computer '{self.vm_id}' did not {action} in time; "
                "inspect it in the cloud dashboard or retry delete()."
            )
        time.sleep(min(0.5, remaining))
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise CelestoError(f"Computer '{self.vm_id}' did not {action} in time; retry delete().")
        self._client.get_httpx_client().timeout = httpx.Timeout(min(30, remaining))

    def delete(self) -> None:
        if self.vm_id is None:
            return
        deadline = time.monotonic() + self._cleanup_timeout
        self._client.get_httpx_client().timeout = httpx.Timeout(min(30, self._cleanup_timeout))
        try:
            try:
                computer = self._call(
                    delete.sync_detailed, ComputerResponse, computer_id=self.vm_id
                )
            except CloudAPIError as exc:
                if exc.status_code != 409:
                    raise
                computer = self._get()
                if computer.status not in {"deleting", "deleted"}:
                    raise
            while computer.status != "deleted":
                self._wait(deadline, "delete")
                computer = self._get()
        except VMNotFoundError:
            return

    def close(self) -> None:
        self._client.get_httpx_client().close()

    def attach(self, computer_id: str) -> None:
        self.vm_id = computer_id
        try:
            computer = self._get()
            if computer.status == "deleted":
                raise VMNotFoundError(computer_id)
        except BaseException:
            self.close()
            raise

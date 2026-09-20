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
    create_browser_connection_v1_computers_computer_id_browser_post as connect_browser,
)
from _celesto_cloud_api.api.computers import (
    create_computer_v1_computers_post as create,
)
from _celesto_cloud_api.api.computers import (
    create_display_connection_v1_computers_computer_id_display_post as connect_display,
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
from _celesto_cloud_api.client import AuthenticatedClient
from _celesto_cloud_api.errors import UnexpectedStatus
from _celesto_cloud_api.models.computer_browser_connection_response import (
    ComputerBrowserConnectionResponse,
)
from _celesto_cloud_api.models.computer_create_request import ComputerCreateRequest
from _celesto_cloud_api.models.computer_display_connection_request import (
    ComputerDisplayConnectionRequest,
)
from _celesto_cloud_api.models.computer_display_connection_request_mode import (
    ComputerDisplayConnectionRequestMode,
)
from _celesto_cloud_api.models.computer_display_connection_response import (
    ComputerDisplayConnectionResponse,
)
from _celesto_cloud_api.models.computer_exec_request import ComputerExecRequest
from _celesto_cloud_api.models.computer_exec_response import ComputerExecResponse
from _celesto_cloud_api.models.computer_response import ComputerResponse
from _celesto_cloud_api.types import UNSET
from celesto._connection_info import DisplayMode, cloud_connection_info, validate_display_mode
from celesto._streaming import iter_bounded_lines, iter_sse_data, parse_command_event
from celesto.exceptions import CelestoError, CloudAPIError, VMNotFoundError
from celesto.types import (
    BrowserConnection,
    CommandEvent,
    CommandExitEvent,
    CommandResult,
    DisplayConnection,
)

T = TypeVar("T")
_MAX_ERROR_BODY_BYTES = 64 * 1024
_CONNECTION_TIMEOUT = 30.0


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

    def _call(self, endpoint: Callable[..., Any], expected: type[T], **kwargs: Any) -> T:
        try:
            response = endpoint(
                client=self._client, x_current_organization=self._organization, **kwargs
            )
        except UnexpectedStatus as exc:
            if exc.status_code == 404 and self.vm_id is not None:
                raise VMNotFoundError(self.vm_id) from None
            raise self._api_error(exc.status_code, exc.content) from None
        except httpx.TransportError as exc:
            raise CelestoError(
                f"Cloud request failed ({type(exc).__name__}); its outcome may be unknown. "
                "Check your computers before retrying; no request was replayed."
            ) from None
        except (ValueError, KeyError, TypeError):
            raise CelestoError(
                "Cloud returned an invalid response; check the API version before retrying."
            ) from None
        if response.status_code >= 400:
            raise self._api_error(response.status_code, response.content)
        if not isinstance(response.parsed, expected):
            raise CelestoError("Cloud returned an unexpected response; check the API version.")
        return response.parsed

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

    def run_stream(self, command: str, timeout: int = 30) -> Iterator[CommandEvent]:
        """Execute a command and yield parsed cloud SSE events as they arrive."""
        self.validate_command(command, timeout)
        return self._iter_command_events(command, timeout)

    def _connection(self, endpoint: Callable[..., Any], expected: type[T], **kwargs: Any) -> T:
        """Poll state, then issue exactly once; never replay credential issuance."""
        deadline = time.monotonic() + _CONNECTION_TIMEOUT
        client = self._client.get_httpx_client()
        original_timeout = client.timeout

        def remaining() -> float:
            value = deadline - time.monotonic()
            if value <= 0:
                raise CelestoError(
                    f"Computer '{self.vm_id}' is not ready; request a new connection."
                )
            return value

        try:
            while True:
                client.timeout = httpx.Timeout(remaining())
                computer = self._get()
                if computer.status == "running":
                    break
                if computer.status not in {"creating", "starting", "restoring", "pending"}:
                    raise CelestoError(
                        f"Computer '{self.vm_id}' is not running; start it in the cloud dashboard."
                    )
                time.sleep(min(0.5, remaining()))
            client.timeout = httpx.Timeout(remaining())
            result = self._call(endpoint, expected, computer_id=self.vm_id, **kwargs)
            remaining()
            return result
        except CloudAPIError as exc:
            # Even documented 400 details may contain a connection credential.
            raise CloudAPIError(exc.status_code) from None
        finally:
            client.timeout = original_timeout

    def browser(self) -> BrowserConnection:
        result = self._connection(connect_browser.sync_detailed, ComputerBrowserConnectionResponse)
        url, expiry = cloud_connection_info(result.gateway_url, result.token, result.expires_at)
        return BrowserConnection(url=url, expires_at=expiry)

    def display(self, *, mode: DisplayMode = "read_only") -> DisplayConnection:
        validate_display_mode(mode)
        result = self._connection(
            connect_display.sync_detailed,
            ComputerDisplayConnectionResponse,
            body=ComputerDisplayConnectionRequest(mode=ComputerDisplayConnectionRequestMode(mode)),
        )
        if result.mode != mode:
            raise CelestoError("Cloud returned a different display mode; request a new connection.")
        url, expiry = cloud_connection_info(result.gateway_url, result.token, result.expires_at)
        return DisplayConnection(url=url, expires_at=expiry, mode=mode)

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

"""Cloud computer orchestration above the generated HTTP client."""

from __future__ import annotations

import json
import math
import os
import time
from collections.abc import Callable
from typing import Any, TypeVar
from urllib.parse import urlsplit

import httpx

from _celesto_cloud_api.api.computers import (
    create_computer_v1_computers_post as create,
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
from _celesto_cloud_api.models.computer_create_request import ComputerCreateRequest
from _celesto_cloud_api.models.computer_exec_request import ComputerExecRequest
from _celesto_cloud_api.models.computer_exec_response import ComputerExecResponse
from _celesto_cloud_api.models.computer_response import ComputerResponse
from _celesto_cloud_api.types import UNSET
from celesto.exceptions import CelestoError, CloudAPIError, VMNotFoundError
from celesto.types import CommandResult

T = TypeVar("T")


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

"""Cloud computer orchestration above the generated HTTP client."""

from __future__ import annotations

import json
import math
import os
import re
import time
import uuid
from collections.abc import Callable, Iterator, Mapping
from typing import Any, Literal, TypeVar
from urllib.parse import urlsplit

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
    start_computer_v1_computers_computer_id_start_post as resume,
)
from _celesto_cloud_api.api.computers import (
    stop_computer_v1_computers_computer_id_stop_post as stop,
)
from _celesto_cloud_api.api.computers import (
    unpublish_computer_port_v1_computers_computer_id_published_ports_port_delete as unpublish_port,
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
from celesto._connection_info import DisplayMode, cloud_connection_info, validate_display_mode
from celesto._terminal import TerminalConnection, cloud_terminal_connection
from celesto.exceptions import CelestoError, CloudAPIError, CloudOperationError, VMNotFoundError
from celesto.types import (
    BrowserConnection,
    CommandEvent,
    CommandExitEvent,
    CommandOutputEvent,
    CommandResult,
    CommandStartedEvent,
    DisplayConnection,
    PublishedPort,
)

T = TypeVar("T")
_CONNECTION_TIMEOUT = 30.0


_DEFAULT_CLOUD_BASE_URL = "https://api.celesto.ai"


class _CloudComputer:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = _DEFAULT_CLOUD_BASE_URL,
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
            from celesto.cli._credentials import read_credentials

            stored = read_credentials()
            if stored:
                key = stored["api_key"]
                # Only substitute the stored base_url when the caller left
                # base_url at its default; an explicit base_url (including an
                # explicit production URL) always wins.
                if base_url == _DEFAULT_CLOUD_BASE_URL and stored.get("base_url"):
                    base_url = stored["base_url"]
        if not isinstance(key, str) or not key.strip():
            raise ValueError(
                "Set CELESTO_API_KEY, pass api_key=, or run "
                "'celesto auth login' to use a cloud computer."
            )
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
        response_context: dict[str, str | None] | None = None,
        operation: str = "request",
        **kwargs: Any,
    ) -> T:
        request_id = None
        reference = kwargs.get("idempotency_key")
        idem = reference if isinstance(reference, str) else None

        def check_response(response: httpx.Response) -> None:
            nonlocal request_id
            request_id = self._request_id(response.headers)
            if response_context is not None:
                response_context["request_id"] = request_id
            if response.status_code >= 400:
                # Capture HTTP errors before a generated error-body parser can
                # fail and hide their status. Never retain raw request/response.
                response.read()
                if response.status_code == 404 and self.vm_id is not None:
                    raise VMNotFoundError(self.vm_id, list_command="celesto computer list --cloud")
                raise self._api_error(
                    response.status_code,
                    response.content,
                    retain_error_detail=retain_error_detail,
                    operation=operation,
                    computer_id=self.vm_id,
                    request_id=request_id,
                    idempotency_key=idem,
                )

        hooks = self._client.get_httpx_client().event_hooks["response"]
        hooks.append(check_response)
        try:
            try:
                response = endpoint(
                    client=self._client, x_current_organization=self._organization, **kwargs
                )
            except UnexpectedStatus as exc:
                if exc.status_code == 404 and self.vm_id is not None:
                    raise VMNotFoundError(
                        self.vm_id, list_command="celesto computer list --cloud"
                    ) from None
                raise self._api_error(
                    exc.status_code,
                    exc.content,
                    retain_error_detail=retain_error_detail,
                    operation=operation,
                    computer_id=self.vm_id,
                    request_id=request_id,
                    idempotency_key=idem,
                ) from None
            except httpx.TransportError as exc:
                raise self._operation_error(
                    "cloud_transport_error",
                    operation,
                    computer_id=self.vm_id,
                    request_id=request_id,
                    idempotency_key=idem,
                    reason=(
                        f"Cloud {operation} request failed ({type(exc).__name__}); "
                        "its outcome may be unknown."
                    ),
                ) from None
            except (ValueError, KeyError, TypeError):
                raise self._invalid_response(
                    uncertain_mutation,
                    operation=operation,
                    computer_id=self.vm_id,
                    request_id=request_id,
                    idempotency_key=idem,
                ) from None
            if response.status_code >= 400:
                raise self._api_error(
                    response.status_code,
                    response.content,
                    retain_error_detail=retain_error_detail,
                    operation=operation,
                    computer_id=self.vm_id,
                    request_id=self._request_id(getattr(response, "headers", {})),
                    idempotency_key=idem,
                )
            if not isinstance(response.parsed, expected) or (
                expected is list and not isinstance(json.loads(response.content), list)
            ):
                raise self._invalid_response(
                    uncertain_mutation,
                    operation=operation,
                    computer_id=self.vm_id,
                    request_id=request_id,
                    idempotency_key=idem,
                )
            return response.parsed
        finally:
            hooks.remove(check_response)

    @staticmethod
    def _request_id(headers: Mapping[str, str]) -> str | None:
        # Cloud trace IDs and UUID request IDs are safe correlation references;
        # arbitrary header values (including credential-shaped ones) stay private.
        for name in ("x-request-id", "x-cloud-trace-context"):
            value = headers.get(name, "")
            if re.fullmatch(r"[0-9a-fA-F]{32}(?:/\d+)?(?:;o=[01])?", value):
                return value.split("/", 1)[0].split(";", 1)[0]
            if re.fullmatch(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", value):
                return value
        return None

    @staticmethod
    def _operation_error(
        code: str,
        operation: str,
        *,
        computer_id: str | None = None,
        request_id: str | None = None,
        idempotency_key: str | None = None,
        reason: str,
    ) -> CloudOperationError:
        idem = idempotency_key
        target = f"computer '{computer_id}'" if computer_id else "your computers"
        if operation in {"publish_port", "unpublish_port"}:
            recovery = "The operation may have succeeded; call published_ports() before retrying."
        elif operation == "run":
            recovery = (
                f"The command may have executed on {target}; "
                "confirm its result before rerunning it."
            )
        elif operation == "delete":
            recovery = f"Inspect {target} in the cloud dashboard before retrying delete()."
        elif operation in {"request", "get", "published_ports"}:
            recovery = f"Inspect {target} in the cloud dashboard; retry once, then contact support."
        else:
            recovery = (
                f"The operation may have succeeded; inspect {target} in the cloud dashboard "
                f"before retrying {operation}."
            )
        return CloudOperationError(
            f"{reason} {recovery}",
            code=code,
            operation=operation,
            computer_id=computer_id,
            request_id=request_id,
            idempotency_key=idem,
            recovery_action="inspect",
            side_effects="none"
            if operation in {"request", "get", "published_ports"}
            else "unknown",
        )

    @staticmethod
    def _invalid_response(
        uncertain_mutation: str | None = None,
        *,
        operation: str = "request",
        computer_id: str | None = None,
        request_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> CloudOperationError:
        idem = idempotency_key
        if uncertain_mutation and operation == "request":
            operation = (
                "unpublish_port" if uncertain_mutation.startswith("unpublish") else "publish_port"
            )
        return _CloudComputer._operation_error(
            "cloud_invalid_response",
            operation,
            computer_id=computer_id,
            request_id=request_id,
            idempotency_key=idem,
            reason="Cloud returned an invalid response.",
        )

    @staticmethod
    def _api_error(
        status_code: int,
        content: bytes,
        *,
        retain_error_detail: bool = True,
        operation: str | None = None,
        computer_id: str | None = None,
        request_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> CloudAPIError:
        idem = idempotency_key
        detail = None
        recovery = None
        try:
            body = json.loads(content)
        except (ValueError, RecursionError):
            body = None
        public_detail = body.get("detail") if isinstance(body, dict) else None
        if status_code == 400 and retain_error_detail and isinstance(public_detail, str):
            detail = public_detail
        # Interpret only known public codes and exact legacy messages. Never
        # print arbitrary server text: responses can echo credentials or commands.
        if status_code == 403:
            if isinstance(public_detail, dict):
                code = public_detail.get("error_code")
                if code == "api_key_scope_required":
                    required_scope = public_detail.get("required_scope")
                    permission = (
                        {
                            "computers:read": "See your computers",
                            "computers:exec": "Create, start, stop computers and run commands",
                            "computers:admin": "Delete computers",
                        }.get(required_scope)
                        if isinstance(required_scope, str)
                        else None
                    )
                    if permission:
                        recovery = (
                            f"This API key needs '{permission}' permission; create a key with "
                            "that permission in the dashboard and update "
                            "CELESTO_API_KEY or api_key=."
                        )
                elif code == "organization_access_denied":
                    recovery = (
                        "This API key's owner cannot access its organization; ask an "
                        "organization owner to restore membership."
                    )
                elif code == "api_key_endpoint_not_allowed":
                    recovery = (
                        "This API key cannot access this endpoint; use the dashboard's "
                        "default API key for this operation."
                    )
                elif code == "trial_micro_only":
                    recovery = (
                        "The free trial allows Micro computers only; choose Micro in the "
                        "dashboard or add prepaid credit."
                    )
                elif code == "promotional_size_not_allowed":
                    recovery = (
                        "Your promotional credit does not cover this computer size; "
                        "choose an eligible size in the dashboard or add prepaid credit."
                    )
            elif public_detail == "Scoped credentials are restricted to MCP":
                recovery = (
                    "This server accepts scoped keys through MCP only; use the dashboard's "
                    "default API key for the Python SDK."
                )
            elif public_detail == "Account suspended. Contact support.":
                recovery = "Your account is suspended; contact Celesto support to restore access."
            elif isinstance(public_detail, str) and public_detail.startswith(
                "Access denied to organization "
            ):
                recovery = (
                    "This API key cannot access the selected organization; use the key's "
                    "organization or update organization_id=."
                )
            elif public_detail == "Insufficient permissions. Required: write":
                recovery = (
                    "Your organization role cannot change computers; "
                    "ask an owner to grant write access."
                )
        elif status_code == 402 and isinstance(public_detail, dict):
            code = public_detail.get("error_code")
            if code in ("trial_expired", "trial_credit_depleted", "prepaid_credit_depleted"):
                recovery = (
                    "Your trial has ended or credit has run out; add credit in the cloud dashboard."
                )
            elif code in ("trial_not_started", "usage_subscription_required"):
                recovery = "Start the free trial or add prepaid credit in the cloud dashboard."
            elif code in ("prepaid_credit_required", "payment_failed", "payment_pending"):
                recovery = "Complete payment or add prepaid credit in the cloud dashboard."
        elif status_code == 429 and isinstance(public_detail, dict):
            code = public_detail.get("error_code")
            if code == "trial_retained_sandbox_limit_reached":
                recovery = (
                    "The free trial allows one sandbox at a time, including stopped sandboxes. "
                    "Reuse your existing sandbox, delete it in the cloud dashboard, or add "
                    "prepaid credit before creating another."
                )
            elif code == "concurrency_limit_reached":
                limit = public_detail.get("running_limit")
                reason = (
                    f"Your organization can run at most {limit} sandboxes at once"
                    if type(limit) is int and 1 <= limit <= 1000
                    else "Your organization has reached its running sandbox limit"
                )
                recovery = (
                    f"{reason}; stop or delete a running sandbox in the cloud dashboard "
                    "before starting another."
                )
        known_codes = {
            403: {
                "api_key_scope_required",
                "organization_access_denied",
                "api_key_endpoint_not_allowed",
                "trial_micro_only",
                "promotional_size_not_allowed",
            },
            402: {
                "trial_expired",
                "trial_credit_depleted",
                "prepaid_credit_depleted",
                "trial_not_started",
                "usage_subscription_required",
                "prepaid_credit_required",
                "payment_failed",
                "payment_pending",
            },
            429: {"trial_retained_sandbox_limit_reached", "concurrency_limit_reached"},
        }
        raw_code = public_detail.get("error_code") if isinstance(public_detail, dict) else None
        recognized_code = (
            raw_code
            if isinstance(raw_code, str) and raw_code in known_codes.get(status_code, set())
            else f"http_{status_code}"
        )
        scope = public_detail.get("required_scope") if isinstance(public_detail, dict) else None
        scope = (
            scope
            if isinstance(scope, str)
            and scope in {"computers:read", "computers:exec", "computers:admin"}
            else None
        )
        limit = public_detail.get("running_limit") if isinstance(public_detail, dict) else None
        limit = limit if type(limit) is int and 1 <= limit <= 1000 else None
        validation: list[dict[str, str]] = []
        if status_code == 422:
            recognized_code = "validation_error"
            allowed_fields = {
                "vcpus",
                "ram_mb",
                "disk_size_mb",
                "image",
                "template_id",
                "template_version",
                "external_volume_enabled",
                "command",
                "timeout",
                "port",
                "mode",
                "terminal_id",
            }
            allowed_constraints = {
                "greater_than",
                "greater_than_equal",
                "less_than",
                "less_than_equal",
                "int_parsing",
                "int_type",
                "string_type",
                "string_too_long",
                "string_too_short",
                "bool_parsing",
                "bool_type",
                "missing",
                "literal_error",
            }
            errors = body.get("errors") if isinstance(body, dict) else None
            if isinstance(errors, list):
                for item in errors[:20]:
                    if not isinstance(item, dict):
                        continue
                    loc, constraint = item.get("loc"), item.get("type")
                    if (
                        isinstance(loc, list)
                        and len(loc) == 2
                        and loc[0] == "body"
                        and isinstance(loc[1], str)
                        and loc[1] in allowed_fields
                        and isinstance(constraint, str)
                        and constraint in allowed_constraints
                    ):
                        validation.append({"field": loc[1], "code": constraint})
            fields = ", ".join(dict.fromkeys(item["field"] for item in validation))
            recovery = (
                f"Correct {fields} and retry."
                if fields
                else (
                    "Check the operation parameters and retry; "
                    "contact Celesto support if they are valid."
                )
            )
            if validation and validation[0] == {"field": "vcpus", "code": "greater_than"}:
                recovery = (
                    "vcpus must be a positive integer; set vcpus to a positive integer and retry."
                )
        if status_code == 401:
            recovery = (
                "Supply a valid Celesto API key through api_key= or "
                "CELESTO_API_KEY before retrying."
            )
        mutating = operation not in {None, "request", "get", "published_ports"}
        side_effects: Literal["none", "unknown"] = (
            "unknown" if status_code >= 500 and mutating else "none"
        )
        action: Literal["fix_and_retry", "inspect", "ask_human"] = "fix_and_retry"
        if status_code >= 500:
            action = "inspect" if mutating else "ask_human"
            recovery = (
                "The operation may have succeeded; inspect your computers in the cloud "
                "dashboard before retrying."
                if mutating
                else "Contact Celesto support with the request ID if the problem continues."
            )
        elif status_code == 429:
            action = "inspect" if recognized_code in known_codes[429] else "ask_human"
            if recognized_code == "http_429":
                recovery = (
                    "The server is limiting requests; inspect your cloud account limits "
                    "before retrying, or ask Celesto support which limit applies."
                )
        return CloudAPIError(
            status_code,
            detail=detail,
            recovery=recovery,
            code=recognized_code,
            operation=operation,
            computer_id=computer_id,
            request_id=request_id,
            idempotency_key=idem,
            recovery_action=action,
            side_effects=side_effects,
            required_scope=scope if recognized_code == "api_key_scope_required" else None,
            running_limit=limit if recognized_code == "concurrency_limit_reached" else None,
            validation_errors=tuple(validation),
        )

    def _get(self) -> ComputerResponse:
        return self._call(
            retrieve.sync_detailed, ComputerResponse, operation="get", computer_id=self.vm_id
        )

    def start(self) -> None:
        # Exactly one create request. Never retry a potentially billable allocation.
        computer = self._call(
            create.sync_detailed,
            ComputerResponse,
            operation="create",
            body=self._body,
            idempotency_key=uuid.uuid4().hex,
        )
        self.vm_id = computer.id
        deadline = time.monotonic() + self._startup_timeout
        while computer.status != "running":
            if computer.status not in {"creating", "starting", "restoring", "pending"}:
                raise CelestoError(f"Computer '{self.vm_id}' is {computer.status}; call delete().")
            self._wait(deadline, "start")
            computer = self._get()

    def stop(self) -> None:
        if self.vm_id is None:
            raise CelestoError("This computer has not started; call start() first.")
        computer = self._call(
            stop.sync_detailed,
            ComputerResponse,
            operation="stop",
            computer_id=self.vm_id,
            uncertain_mutation=f"stop computer {self.vm_id}",
        )
        deadline = time.monotonic() + self._startup_timeout
        while computer.status != "stopped":
            if computer.status != "stopping":
                raise CelestoError(
                    f"Computer '{self.vm_id}' is {computer.status}; check the cloud dashboard."
                )
            self._wait(deadline, "stop")
            computer = self._get()

    def resume(self) -> None:
        if self.vm_id is None:
            raise CelestoError("This computer has not started; call start() first.")
        computer = self._call(
            resume.sync_detailed,
            ComputerResponse,
            operation="resume",
            computer_id=self.vm_id,
            uncertain_mutation=f"resume computer {self.vm_id}",
        )
        deadline = time.monotonic() + self._startup_timeout
        while computer.status != "running":
            if computer.status != "starting":
                raise CelestoError(
                    f"Computer '{self.vm_id}' is {computer.status}; check the cloud dashboard."
                )
            self._wait(deadline, "resume")
            computer = self._get()

    @staticmethod
    def validate_command(command: str, timeout: int) -> None:
        if len(command) > 10000 or timeout > 300:
            raise ValueError(
                "Cloud commands allow at most 10,000 characters and a 300-second timeout."
            )

    def _execute_command(self, command: str, timeout: int) -> ComputerExecResponse:
        self.validate_command(command, timeout)
        self._client.get_httpx_client().timeout = httpx.Timeout(timeout + 10)
        try:
            return self._call(
                execute.sync_detailed,
                ComputerExecResponse,
                operation="run",
                computer_id=self.vm_id,
                body=ComputerExecRequest(command=command, timeout=timeout),
            )
        finally:
            self._client.get_httpx_client().timeout = httpx.Timeout(30)

    def run(self, command: str, timeout: int = 30) -> CommandResult:
        result = self._execute_command(command, timeout)
        return CommandResult(stdout=result.stdout, stderr=result.stderr, exit_code=result.exit_code)

    @staticmethod
    def _published_port(
        result: ComputerPublishedPortResponse,
        *,
        uncertain_mutation: str | None = None,
        operation: str = "published_ports",
        computer_id: str | None = None,
        request_id: str | None = None,
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
            raise _CloudComputer._invalid_response(
                uncertain_mutation,
                operation=operation,
                computer_id=computer_id,
                request_id=request_id,
            ) from None

    def publish_port(self, port: int) -> PublishedPort:
        context: dict[str, str | None] = {}
        mutation = f"publish port {port}"
        try:
            result = self._call(
                publish_port.sync_detailed,
                ComputerPublishedPortResponse,
                operation="publish_port",
                retain_error_detail=False,
                uncertain_mutation=mutation,
                response_context=context,
                computer_id=self.vm_id,
                body=ComputerPublishedPortCreateRequest(port=port),
            )
        except CloudAPIError as exc:
            if exc.status_code == 400:
                raise CloudAPIError(
                    400,
                    recovery=f"Port {port} cannot be published; choose another port and retry.",
                    code=exc.code,
                    operation=exc.operation,
                    computer_id=exc.computer_id,
                    request_id=exc.request_id,
                ) from None
            raise
        return self._published_port(
            result,
            uncertain_mutation=mutation,
            operation="publish_port",
            computer_id=self.vm_id,
            request_id=context.get("request_id"),
        )

    def published_ports(self) -> list[PublishedPort]:
        context: dict[str, str | None] = {}
        results = self._call(
            list_ports.sync_detailed,
            list,
            operation="published_ports",
            response_context=context,
            retain_error_detail=False,
            computer_id=self.vm_id,
        )
        return [
            self._published_port(
                result, computer_id=self.vm_id, request_id=context.get("request_id")
            )
            for result in results
        ]

    def unpublish_port(self, port: int) -> PublishedPort:
        context: dict[str, str | None] = {}
        mutation = f"unpublish port {port}"
        result = self._call(
            unpublish_port.sync_detailed,
            ComputerPublishedPortResponse,
            operation="unpublish_port",
            retain_error_detail=False,
            uncertain_mutation=mutation,
            response_context=context,
            computer_id=self.vm_id,
            port=port,
        )
        return self._published_port(
            result,
            uncertain_mutation=mutation,
            operation="unpublish_port",
            computer_id=self.vm_id,
            request_id=context.get("request_id"),
        )

    def run_stream(self, command: str, timeout: int = 30) -> Iterator[CommandEvent]:
        """Yield command events from the cloud's completed exec response."""
        self.validate_command(command, timeout)
        return self._iter_command_events(command, timeout)

    def _connection(
        self, endpoint: Callable[..., Any], expected: type[T], *, operation: str, **kwargs: Any
    ) -> T:
        """Poll state, then issue exactly once; never replay credential issuance."""
        deadline = time.monotonic() + _CONNECTION_TIMEOUT
        client = self._client.get_httpx_client()
        original_timeout = client.timeout
        issued = False
        context: dict[str, str | None] = {}

        def remaining() -> float:
            value = deadline - time.monotonic()
            if value <= 0:
                raise CloudOperationError(
                    f"Computer '{self.vm_id}' connection did not finish in time; "
                    "inspect its state in the cloud dashboard before requesting a new connection.",
                    code="cloud_operation_timeout",
                    operation=operation,
                    computer_id=self.vm_id,
                    request_id=context.get("request_id"),
                    recovery_action="inspect",
                    side_effects="unknown" if issued else "none",
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
            issued = True
            result = self._call(
                endpoint,
                expected,
                operation=operation,
                response_context=context,
                retain_error_detail=False,
                computer_id=self.vm_id,
                **kwargs,
            )
            remaining()
            return result
        finally:
            client.timeout = original_timeout

    def browser(self) -> BrowserConnection:
        result = self._connection(
            connect_browser.sync_detailed, ComputerBrowserConnectionResponse, operation="browser"
        )
        url, expiry = cloud_connection_info(result.gateway_url, result.token, result.expires_at)
        return BrowserConnection(url=url, expires_at=expiry)

    def display(self, *, mode: DisplayMode = "read_only") -> DisplayConnection:
        validate_display_mode(mode)
        result = self._connection(
            connect_display.sync_detailed,
            ComputerDisplayConnectionResponse,
            operation="display",
            body=ComputerDisplayConnectionRequest(mode=ComputerDisplayConnectionRequestMode(mode)),
        )
        if result.mode != mode:
            raise CelestoError("Cloud returned a different display mode; request a new connection.")
        url, expiry = cloud_connection_info(result.gateway_url, result.token, result.expires_at)
        return DisplayConnection(url=url, expires_at=expiry, mode=mode)

    def terminal(self, *, terminal_id: str | None = None) -> TerminalConnection:
        """Create or reauthorize a durable cloud terminal session."""
        response = self._call(
            create_terminal.sync_detailed,
            ComputerTerminalSessionResponse,
            operation="terminal",
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
        started_at = int(time.time() * 1000)
        result = self._execute_command(command, timeout)
        command_id = (
            result.command_id
            if isinstance(result.command_id, str) and result.command_id
            else f"local-{uuid.uuid4().hex}"
        )
        yield CommandStartedEvent(
            command_id=command_id,
            started_at_unix_ms=started_at,
            timeout_seconds=timeout,
        )
        if result.stdout:
            yield CommandOutputEvent(type="stdout", data=result.stdout)
        if result.stderr:
            yield CommandOutputEvent(type="stderr", data=result.stderr)
        yield CommandExitEvent(
            exit_code=result.exit_code,
            command_id=command_id,
            duration_ms=result.duration_ms if isinstance(result.duration_ms, int) else None,
            timed_out=result.timed_out if isinstance(result.timed_out, bool) else False,
        )

    def _wait(self, deadline: float, action: str) -> None:
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(0.5, remaining))
            remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise self._operation_error(
                "cloud_operation_timeout",
                action,
                computer_id=self.vm_id,
                reason=f"Computer '{self.vm_id}' did not {action} in time.",
            )
        self._client.get_httpx_client().timeout = httpx.Timeout(min(30, remaining))

    def delete(self) -> None:
        if self.vm_id is None:
            return
        deadline = time.monotonic() + self._cleanup_timeout
        self._client.get_httpx_client().timeout = httpx.Timeout(min(30, self._cleanup_timeout))
        try:
            try:
                computer = self._call(
                    delete.sync_detailed,
                    ComputerResponse,
                    operation="delete",
                    computer_id=self.vm_id,
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
                raise VMNotFoundError(computer_id, list_command="celesto computer list --cloud")
        except BaseException:
            self.close()
            raise

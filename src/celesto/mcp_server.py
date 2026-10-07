"""MCP tools for computers on this machine."""

from __future__ import annotations

import time
from typing import Any

from celesto.cli.service import CLIService
from celesto.exceptions import OperationTimeoutError, VMAlreadyExistsError, VMNotFoundError
from celesto.types import CommandExitEvent, CommandOutputEvent, GuestOS

_MAX_OUTPUT_CHARS = 16_384


def _info(vm: Any) -> dict[str, str]:
    info = vm.info
    return {"name": info.vm_id, "state": info.status.value}


def _expand_allowed_host_patterns(hosts: list[str]) -> list[str]:
    """Keep configured Host values and add the SDK's explicit wildcard-port pattern."""
    expanded: list[str] = []
    for configured in hosts:
        if configured not in expanded:
            expanded.append(configured)
        if configured.endswith(":*"):
            continue

        hostname: str | None = None
        if configured.startswith("[") and "]:" in configured:
            bracket, _, port = configured.partition("]:")
            if port.isdigit():
                hostname = f"{bracket}]"
        elif configured.startswith("[") and configured.endswith("]"):
            if f"{configured}:*" not in expanded:
                expanded.append(f"{configured}:*")
            continue
        elif configured.count(":") == 1:
            host_part, _, port = configured.rpartition(":")
            if port.isdigit():
                hostname = host_part

        if hostname is not None:
            if hostname not in expanded:
                expanded.append(hostname)
        elif ":" not in configured and f"{configured}:*" not in expanded:
            expanded.append(f"{configured}:*")

    return expanded


def _tool_error(name: str, exc: Exception, action: str) -> Exception:
    from mcp.server.mcpserver.exceptions import ToolError

    if isinstance(exc, VMNotFoundError):
        return ToolError(
            f"No computer named '{name}' was found. Run 'celesto computer list --all' to find one."
        )
    if isinstance(exc, VMAlreadyExistsError):
        return ToolError(
            f"Computer '{name}' already exists. Run 'celesto computer info {name}' to inspect it."
        )
    if action == "create":
        return ToolError(
            f"Could not create computer '{name}'. Run 'celesto doctor', then "
            "'celesto computer list --all' to check its state."
        )
    return ToolError(
        f"Could not {action} computer '{name}'. "
        f"Run 'celesto computer list --all' to check its current state."
    )


def create_server() -> Any:
    """Create a stdio MCP server sharing the CLI's persistent inventory."""
    try:
        from mcp.server import MCPServer
        from mcp.server.mcpserver.exceptions import ToolError
        from mcp.types import ToolAnnotations
    except ImportError as exc:
        raise RuntimeError(
            "MCP support is missing. Run 'uv tool install \"celesto[mcp]\"' to install it."
        ) from exc

    server = MCPServer("Celesto")
    service = CLIService()

    @server.tool(annotations=ToolAnnotations(destructive_hint=False, open_world_hint=True))
    def computer_create(name: str) -> dict[str, str]:
        """Create and start a local Linux computer. Its files persist until deletion."""
        try:
            from celesto.facade import _build_auto_config

            config, ssh_key_path = _build_auto_config(vm_name=name, os=GuestOS.UBUNTU)
            vm = service.create_vm(config, ssh_key_path=ssh_key_path)
            vm.start()
            vm.wait_for_ready(timeout=30)
            return _info(vm)
        except Exception as exc:
            raise _tool_error(name, exc, "create") from exc

    @server.tool(annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False))
    def computer_list() -> dict[str, list[dict[str, str]]]:
        """List all local computers, including stopped computers."""
        try:
            with service.manager() as manager:
                computers = [
                    {"name": vm.vm_id, "state": manager.refresh_status(vm).status.value}
                    for vm in manager.list_vms()
                ]
            return {"computers": sorted(computers, key=lambda item: item["name"])}
        except Exception as exc:
            raise ToolError(
                f"Could not list computers: {exc}. Run 'celesto computer list --all' to check them."
            ) from exc

    @server.tool(annotations=ToolAnnotations(destructive_hint=True, open_world_hint=True))
    def computer_exec(name: str, command: str, timeout: int = 30) -> dict[str, Any]:
        """Run a shell command inside a running computer and return its exit code and output."""
        if not 1 <= timeout <= 300:
            raise ToolError(
                f"Timeout must be between 1 and 300 seconds for '{name}'. "
                f"Run 'celesto computer exec {name} --help' to see command options."
            )
        try:
            output = {"stdout": "", "stderr": ""}
            truncated = {"stdout": False, "stderr": False}
            exit_event: CommandExitEvent | None = None
            start = time.monotonic()
            for event in service.vm_from_id(name).run_stream(command, timeout=timeout):
                if isinstance(event, CommandOutputEvent):
                    current = output[event.type]
                    remaining = _MAX_OUTPUT_CHARS - len(current)
                    output[event.type] += event.data[:remaining]
                    truncated[event.type] |= len(event.data) > remaining
                elif isinstance(event, CommandExitEvent):
                    exit_event = event
            if exit_event is None:
                raise ToolError(
                    f"Command in computer '{name}' ended without a result. "
                    f"Run 'celesto computer list --all' to check its state."
                )
            if exit_event.timed_out:
                raise ToolError(
                    f"Command in computer '{name}' exceeded {timeout} seconds. "
                    f"Run 'celesto computer exec {name} --help' to set a longer timeout."
                )
            return {
                "name": name,
                "exit_code": exit_event.exit_code,
                "stdout": output["stdout"],
                "stderr": output["stderr"],
                "stdout_truncated": truncated["stdout"],
                "stderr_truncated": truncated["stderr"],
                "timeout_seconds": timeout,
                "duration_ms": exit_event.duration_ms
                if exit_event.duration_ms is not None
                else int((time.monotonic() - start) * 1000),
            }
        except OperationTimeoutError as exc:
            raise ToolError(
                f"Command in computer '{name}' exceeded {timeout} seconds. "
                f"Run 'celesto computer exec {name} --help' to set a longer timeout."
            ) from exc
        except ToolError:
            raise
        except Exception as exc:
            raise _tool_error(name, exc, "run a command in") from exc

    @server.tool(annotations=ToolAnnotations(destructive_hint=False, open_world_hint=True))
    def computer_start(name: str) -> dict[str, str]:
        """Start a stopped local computer, keeping its files."""
        try:
            vm = service.vm_from_id(name).start()
            vm.wait_for_ready(timeout=30)
            return _info(vm)
        except Exception as exc:
            raise _tool_error(name, exc, "start") from exc

    @server.tool(annotations=ToolAnnotations(destructive_hint=False, open_world_hint=True))
    def computer_stop(name: str) -> dict[str, str]:
        """Stop a local computer while keeping its files for later."""
        try:
            vm = service.vm_from_id(name).stop()
            return _info(vm)
        except Exception as exc:
            raise _tool_error(name, exc, "stop") from exc

    @server.tool(annotations=ToolAnnotations(destructive_hint=True, open_world_hint=True))
    def computer_delete(name: str) -> dict[str, str]:
        """Permanently delete a local computer and its files."""
        try:
            service.vm_from_id(name).delete()
            return {"name": name, "state": "deleted"}
        except Exception as exc:
            raise _tool_error(name, exc, "delete") from exc

    from celesto.mcp_server_extra import register_extra_tools

    register_extra_tools(server, service, ToolAnnotations, ToolError)

    return server


class _CloudOnlyToolRegistry:
    """Register only Cloud computer tools on a wrapped MCP server."""

    def __init__(self, server: Any) -> None:
        self._server = server

    def tool(self, *args: Any, **kwargs: Any) -> Any:
        register = self._server.tool(*args, **kwargs)

        def register_cloud_tool(function: Any) -> Any:
            if function.__name__.startswith("cloud_computer_"):
                return register(function)
            return function

        return register_cloud_tool


def _validate_cloud_api_key(api_key: str, api_base_url: str) -> bool | None:
    """Check a caller key against Celesto Cloud; None means the auth API is unavailable."""
    import httpx

    from _celesto_cloud_api.api.users.get_info_v1_users_info_get import sync_detailed
    from _celesto_cloud_api.client import AuthenticatedClient

    client = AuthenticatedClient(
        base_url=api_base_url.rstrip("/"),
        token=api_key,
        timeout=httpx.Timeout(10),
        raise_on_unexpected_status=False,
    )
    try:
        response = sync_detailed(client=client)
        if response.status_code in (401, 403):
            return False
        if response.status_code != 200 or response.parsed is None:
            return None
        return not response.parsed.access_suspended
    except httpx.TransportError:
        return None
    finally:
        client.get_httpx_client().close()


class _CelestoAPIKeyMiddleware:
    """Require and validate a Celesto API key on every remote MCP request."""

    def __init__(self, app: Any, *, api_base_url: str) -> None:
        self.app = app
        self.api_base_url = api_base_url

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        from starlette.concurrency import run_in_threadpool
        from starlette.requests import Request
        from starlette.responses import JSONResponse

        request = Request(scope, receive=receive)
        if request.url.path == "/healthz":
            await JSONResponse({"status": "ok"})(scope, receive, send)
            return

        authorization = request.headers.get("authorization", "")
        scheme, separator, api_key = authorization.partition(" ")
        if scheme.lower() != "bearer" or not separator or not api_key.strip():
            response = JSONResponse(
                {"error": "Send a Celesto API key in the Authorization Bearer header."},
                status_code=401,
                headers={"WWW-Authenticate": 'Bearer realm="Celesto Cloud MCP"'},
            )
            await response(scope, receive, send)
            return

        valid = await run_in_threadpool(_validate_cloud_api_key, api_key.strip(), self.api_base_url)
        if valid is None:
            response = JSONResponse(
                {"error": "Celesto Cloud authentication is temporarily unavailable."},
                status_code=503,
            )
            await response(scope, receive, send)
            return
        if not valid:
            response = JSONResponse(
                {"error": "The Celesto API key is invalid or its account is suspended."},
                status_code=401,
                headers={"WWW-Authenticate": 'Bearer realm="Celesto Cloud MCP"'},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


def create_cloud_http_app(
    *,
    host: str = "127.0.0.1",
    allowed_hosts: list[str] | None = None,
    allowed_origins: list[str] | None = None,
) -> Any:
    """Build a Cloud-only stateless Streamable HTTP app protected by caller API keys."""
    try:
        from mcp.server import MCPServer
        from mcp.server.mcpserver.exceptions import ToolError
        from mcp.server.transport_security import TransportSecuritySettings
        from mcp.types import ToolAnnotations
    except ImportError as exc:
        raise RuntimeError(
            "MCP support is missing. Run 'uv tool install \"celesto[mcp]\"' to install it."
        ) from exc

    from starlette.responses import JSONResponse

    from celesto._cloud import _DEFAULT_CLOUD_BASE_URL
    from celesto.mcp_server_extra import register_extra_tools

    if allowed_hosts:
        host_allowlist = _expand_allowed_host_patterns(allowed_hosts)
    elif host in {"127.0.0.1", "localhost", "::1"}:
        host_allowlist = ["127.0.0.1:*", "localhost:*", "[::1]:*"]
    else:
        raise ValueError(
            "A non-loopback MCP server needs an explicit allowed hostname. "
            "Pass --allowed-host for the hostname used by its HTTPS endpoint."
        )

    if allowed_origins is not None:
        origin_allowlist = allowed_origins
    elif host in {"127.0.0.1", "localhost", "::1"}:
        origin_allowlist = [
            "http://127.0.0.1:*",
            "http://localhost:*",
            "http://[::1]:*",
        ]
    else:
        origin_allowlist = []

    security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=host_allowlist,
        allowed_origins=origin_allowlist,
    )
    server = MCPServer(
        "Celesto Cloud",
        instructions=(
            "These tools manage Celesto Cloud computers for the account authenticated "
            "by this request. They do not manage computers on this server's machine."
        ),
    )
    # No local tool is registered on the remote endpoint.
    register_extra_tools(
        _CloudOnlyToolRegistry(server),
        service=None,
        annotations=ToolAnnotations,
        tool_error=ToolError,
    )
    app = server.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
        transport_security=security,
        host=host,
    )

    async def health(_request: Any) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    app.add_route("/healthz", health, methods=["GET"])
    app.add_middleware(_CelestoAPIKeyMiddleware, api_base_url=_DEFAULT_CLOUD_BASE_URL)

    async def health(_request: Any) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    app.add_route("/healthz", health, methods=["GET"])
    return app


def serve_cloud_http(
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    allowed_hosts: list[str] | None = None,
    allowed_origins: list[str] | None = None,
) -> None:
    """Serve the remote Cloud MCP endpoint over Streamable HTTP."""
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError(
            "HTTP MCP support is missing. Install it with 'uv tool install \"celesto[mcp]\"'."
        ) from exc

    app = create_cloud_http_app(
        host=host,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )
    uvicorn.run(app, host=host, port=port, log_level="info")


def run() -> None:
    """Run until the MCP client closes standard input."""
    create_server().run()

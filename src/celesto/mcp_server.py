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


def run() -> None:
    """Run until the MCP client closes standard input."""
    create_server().run()

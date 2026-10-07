"""Additional local computer, browser, and desktop MCP tools."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import asdict
from functools import wraps
from pathlib import Path
from typing import Any

from celesto.cli.service import CLIService


def register_extra_tools(
    server: Any, service: CLIService, annotations: Any, tool_error: Any
) -> None:
    """Register local operations beyond the core computer lifecycle."""
    from celesto import CloudComputer
    from celesto._providers.cloud import get_cloud_computer, list_cloud_computers
    from celesto.browser import _BrowserSandbox, _DesktopSandbox
    from celesto.host.doctor import generate_doctor_report
    from celesto.types import BrowserSessionConfig

    cloud_output_cap = 16_384

    def tool(*, annotations: Any) -> Any:
        def register(function: Any) -> Any:
            @wraps(function)
            def guarded(*args: Any, **kwargs: Any) -> Any:
                try:
                    return function(*args, **kwargs)
                except tool_error:
                    raise
                except Exception as exc:
                    subject = kwargs.get("name") or kwargs.get("session_id") or "resource"
                    function_name = function.__name__
                    if function_name.startswith("cloud_computer_"):
                        recovery = "celesto computer list --cloud"
                        if isinstance(exc, ValueError) and "CELESTO_API_KEY" in str(exc):
                            raise tool_error(
                                "Cloud access is not configured. Run 'celesto auth login', "
                                "then restart the MCP connection."
                            ) from exc
                    elif function_name.startswith("browser_") or function_name.startswith(
                        "desktop_"
                    ):
                        recovery = "celesto browser list"
                    else:
                        recovery = "celesto computer list --all"
                    raise tool_error(
                        f"Could not complete {function_name.replace('_', ' ')} for "
                        f"'{subject}'. Run '{recovery}' to check its state."
                    ) from exc

            return server.tool(annotations=annotations)(guarded)

        return register

    @tool(annotations=annotations(read_only_hint=True, open_world_hint=False))
    def computer_info(name: str) -> dict[str, Any]:
        """Inspect a local computer's state, operating system, resources, and network."""
        info = service.vm_from_id(name).refresh().info
        return {
            "name": info.vm_id,
            "state": info.status.value,
            "os": info.config.guest_os.value,
            "backend": info.config.backend,
            "vcpus": info.config.vcpu_count,
            "memory_mib": info.config.memory,
            "network": info.network.model_dump(mode="json") if info.network else None,
        }

    @tool(annotations=annotations(read_only_hint=True, open_world_hint=False))
    def computer_logs(name: str, lines: int = 100) -> dict[str, Any]:
        """Read recent startup and runtime logs for a local computer."""
        if not 1 <= lines <= 500:
            raise tool_error("Log lines must be between 1 and 500.")
        vm = service.vm_from_id(name)
        path = vm.data_dir / f"{name}.log"
        if not path.exists():
            return {"name": name, "lines": [], "message": "No logs are available yet."}
        from celesto.utils import tail_file

        tail, _, _ = tail_file(path, lines)
        return {"name": name, "lines": tail}

    @tool(annotations=annotations(destructive_hint=False, open_world_hint=False))
    def computer_pause(name: str) -> dict[str, str]:
        """Pause a running computer while keeping its files."""
        vm = service.vm_from_id(name).pause()
        return {"name": vm.vm_id, "state": vm.info.status.value}

    @tool(annotations=annotations(destructive_hint=False, open_world_hint=False))
    def computer_resume(name: str) -> dict[str, str]:
        """Resume a paused computer."""
        vm = service.vm_from_id(name).resume()
        vm.wait_for_ready(timeout=30)
        return {"name": vm.vm_id, "state": vm.info.status.value}

    @tool(annotations=annotations(destructive_hint=True, open_world_hint=True))
    def computer_upload(name: str, local_path: str, computer_path: str) -> dict[str, str]:
        """Copy a local file into a running computer, overwriting the destination if present."""
        result = service.vm_from_id(name).upload_file(local_path, computer_path)
        return {
            "name": name,
            "local_path": str(Path(local_path).expanduser()),
            "computer_path": result,
        }

    @tool(annotations=annotations(destructive_hint=True, open_world_hint=True))
    def computer_download(name: str, computer_path: str, local_path: str) -> dict[str, str]:
        """Copy a computer file to the local path, overwriting it if present."""
        result = service.vm_from_id(name).download_file(computer_path, local_path)
        return {"name": name, "computer_path": computer_path, "local_path": result}

    @tool(annotations=annotations(read_only_hint=True, open_world_hint=False))
    def computer_snapshot_list(name: str) -> dict[str, Any]:
        """List saved snapshots for a local computer."""
        with service.manager() as manager:
            snapshots = manager.list_snapshots(vm_id=name)
        return {"name": name, "snapshots": [item.model_dump(mode="json") for item in snapshots]}

    @tool(annotations=annotations(destructive_hint=False, open_world_hint=False))
    def computer_snapshot_create(
        name: str, snapshot_name: str | None = None, snapshot_type: str = "full"
    ) -> dict[str, Any]:
        """Save a computer snapshot that can be restored later."""
        if snapshot_type not in {"full", "disk"}:
            raise tool_error("Snapshot type must be 'full' or 'disk'.")
        snapshot = service.vm_from_id(name).snapshot(
            snapshot_id=snapshot_name, snapshot_type=snapshot_type
        )
        return snapshot.model_dump(mode="json")

    @tool(annotations=annotations(destructive_hint=True, open_world_hint=False))
    def computer_snapshot_restore(snapshot_name: str, resume: bool = False) -> dict[str, Any]:
        """Restore a saved snapshot to its original computer, replacing its current state."""
        with service.manager() as manager:
            info = manager.restore_snapshot(snapshot_name, resume_vm=resume)
        if resume:
            service.vm_from_id(info.vm_id).wait_for_ready(timeout=30)
        return {"name": info.vm_id, "state": info.status.value}

    @tool(annotations=annotations(destructive_hint=True, open_world_hint=False))
    def computer_snapshot_delete(snapshot_name: str) -> dict[str, str]:
        """Permanently delete a saved snapshot and its files."""
        with service.manager() as manager:
            manager.delete_snapshot(snapshot_name)
        return {"snapshot": snapshot_name, "state": "deleted"}

    @tool(annotations=annotations(destructive_hint=True, open_world_hint=False))
    def computer_env_set(name: str, variables: dict[str, str]) -> dict[str, Any]:
        """Set persistent environment variables in a running computer."""
        keys = service.vm_from_id(name).set_env_vars(variables)
        return {"name": name, "set": keys}

    @tool(annotations=annotations(read_only_hint=True, open_world_hint=False))
    def computer_env_list(name: str) -> dict[str, Any]:
        """List Celesto-managed environment variables in a running computer."""
        return {"name": name, "variables": service.vm_from_id(name).list_env_vars()}

    @tool(annotations=annotations(destructive_hint=True, open_world_hint=False))
    def computer_env_unset(name: str, keys: list[str]) -> dict[str, Any]:
        """Remove persistent environment variables from a running computer."""
        removed = service.vm_from_id(name).unset_env_vars(keys)
        return {"name": name, "removed": sorted(removed)}

    @tool(annotations=annotations(destructive_hint=True, open_world_hint=True))
    def computer_port_expose(
        name: str, computer_port: int, local_port: int | None = None
    ) -> dict[str, int | str]:
        """Forward a computer TCP port to localhost on this machine."""
        from celesto.cli.main import _port_forward_operation_lock, _track_port_forward

        with _port_forward_operation_lock(name):
            vm = service.vm_from_id(name)
            exposed = vm.expose_local(computer_port, local_port)
            try:
                _track_port_forward(vm, name, exposed, computer_port)
            except Exception:
                vm.unexpose_local(exposed, computer_port)
                raise
        return {"name": name, "local_port": exposed, "computer_port": computer_port}

    @tool(annotations=annotations(destructive_hint=True, open_world_hint=True))
    def computer_port_close(name: str, local_port: int, computer_port: int) -> dict[str, str | int]:
        """Close a localhost port forward for a computer."""
        import os
        import signal
        import subprocess

        from celesto.cli.main import (
            _load_port_forwards,
            _port_forward_operation_lock,
            _remove_port_forward,
        )

        with _port_forward_operation_lock(name):
            record = next(
                (
                    item
                    for item in _load_port_forwards(name)
                    if item["host_port"] == local_port and item["guest_port"] == computer_port
                ),
                None,
            )
            if record is not None and record.get("transport") == "ssh_tunnel" and record.get("pid"):
                result = subprocess.run(
                    ["ps", "-p", str(record["pid"]), "-o", "command="],
                    capture_output=True,
                    text=True,
                )
                command = result.stdout.strip()
                forward_spec = f"127.0.0.1:{local_port}:127.0.0.1:{computer_port}"
                executable = Path(command.split()[0]).name if command else ""
                if executable == "ssh" and forward_spec in command:
                    with suppress(ProcessLookupError):
                        os.kill(int(record["pid"]), signal.SIGTERM)
            else:
                service.vm_from_id(name).unexpose_local(local_port, computer_port)
            _remove_port_forward(name, local_port, computer_port)
        return {"name": name, "local_port": local_port, "computer_port": computer_port}

    @tool(annotations=annotations(read_only_hint=True, open_world_hint=False))
    def computer_port_list(name: str) -> dict[str, Any]:
        """List localhost port forwards configured for a computer."""
        from celesto.cli.main import _load_port_forwards

        return {"name": name, "forwards": _load_port_forwards(name)}

    @tool(annotations=annotations(read_only_hint=True, open_world_hint=False))
    def computer_templates() -> dict[str, Any]:
        """List local computer templates available in Celesto."""
        return {
            "templates": [
                {
                    "name": "linux-desktop",
                    "description": (
                        "Linux desktop with Chromium, a terminal, files, and a text editor."
                    ),
                }
            ]
        }

    @tool(annotations=annotations(read_only_hint=True, open_world_hint=False))
    def computer_doctor() -> dict[str, Any]:
        """Check whether this machine has the runtime dependencies Celesto needs."""
        report = generate_doctor_report()
        return {
            "backend": report.backend_resolved,
            "system": report.system,
            "architecture": report.arch,
            "checks": [asdict(check) for check in report.checks],
            "failures": len(report.failures),
            "warnings": len(report.warnings),
        }

    @tool(annotations=annotations(destructive_hint=False, open_world_hint=True))
    def cloud_computer_create() -> dict[str, str]:
        """Create a persistent Celesto Cloud computer using the signed-in account."""
        computer = CloudComputer(lifetime="persistent")
        try:
            computer.start()
            return {"name": str(computer.id), "provider": "cloud", "state": "running"}
        finally:
            computer.close()

    @tool(annotations=annotations(read_only_hint=True, open_world_hint=True))
    def cloud_computer_list(limit: int = 50) -> dict[str, Any]:
        """List Celesto Cloud computers visible to the signed-in account."""
        if not 1 <= limit <= 100:
            raise tool_error("Cloud computer list limit must be between 1 and 100.")
        computers, possibly_truncated = list_cloud_computers(limit=limit)
        return {
            "provider": "cloud",
            "computers": computers,
            "limit": limit,
            "possibly_truncated": possibly_truncated,
        }

    @tool(annotations=annotations(read_only_hint=True, open_world_hint=True))
    def cloud_computer_info(name: str) -> dict[str, Any]:
        """Inspect a Celesto Cloud computer's state and resource configuration."""
        info = get_cloud_computer(name)
        return {"provider": "cloud", **info}

    @tool(annotations=annotations(destructive_hint=True, open_world_hint=True))
    def cloud_computer_exec(name: str, command: str, timeout: int = 30) -> dict[str, Any]:
        """Run a command in a Celesto Cloud computer and return its output and exit code."""
        if not 1 <= timeout <= 300:
            raise tool_error(f"Timeout must be between 1 and 300 seconds for '{name}'.")
        computer = CloudComputer.get(name)
        try:
            result = computer.run(command, timeout=timeout)
            return {
                "name": name,
                "provider": "cloud",
                "exit_code": result.exit_code,
                "stdout": result.stdout[:cloud_output_cap],
                "stderr": result.stderr[:cloud_output_cap],
                "stdout_truncated": len(result.stdout) > cloud_output_cap,
                "stderr_truncated": len(result.stderr) > cloud_output_cap,
                "timeout_seconds": timeout,
            }
        finally:
            computer.close()

    @tool(annotations=annotations(destructive_hint=False, open_world_hint=True))
    def cloud_computer_start(name: str) -> dict[str, str]:
        """Resume a stopped Celesto Cloud computer."""
        computer = CloudComputer.get(name)
        try:
            computer.resume()
            return {"name": name, "provider": "cloud", "state": "running"}
        finally:
            computer.close()

    @tool(annotations=annotations(destructive_hint=False, open_world_hint=True))
    def cloud_computer_stop(name: str) -> dict[str, str]:
        """Stop a Celesto Cloud computer while retaining its files."""
        computer = CloudComputer.get(name)
        try:
            computer.stop()
            return {"name": name, "provider": "cloud", "state": "stopped"}
        finally:
            computer.close()

    @tool(annotations=annotations(destructive_hint=True, open_world_hint=True))
    def cloud_computer_delete(name: str) -> dict[str, str]:
        """Permanently delete a Celesto Cloud computer and its files."""
        computer = CloudComputer.get(name)
        try:
            computer.delete()
            return {"name": name, "provider": "cloud", "state": "deleted"}
        finally:
            computer.close()

    @tool(annotations=annotations(destructive_hint=True, open_world_hint=True))
    def cloud_computer_port_publish(name: str, port: int) -> dict[str, Any]:
        """Publish an HTTP port on a Celesto Cloud computer and return its public URL."""
        computer = CloudComputer.get(name)
        try:
            published = computer.publish_port(port)
            return {"name": name, "provider": "cloud", **published.model_dump(mode="json")}
        finally:
            computer.close()

    @tool(annotations=annotations(read_only_hint=True, open_world_hint=True))
    def cloud_computer_port_list(name: str) -> dict[str, Any]:
        """List public ports for a Celesto Cloud computer."""
        computer = CloudComputer.get(name)
        try:
            ports = computer.published_ports()
            return {
                "name": name,
                "provider": "cloud",
                "ports": [port.model_dump(mode="json") for port in ports],
            }
        finally:
            computer.close()

    @tool(annotations=annotations(destructive_hint=True, open_world_hint=True))
    def cloud_computer_port_unpublish(name: str, port: int) -> dict[str, Any]:
        """Remove a public port from a Celesto Cloud computer."""
        computer = CloudComputer.get(name)
        try:
            published = computer.unpublish_port(port)
            return {"name": name, "provider": "cloud", **published.model_dump(mode="json")}
        finally:
            computer.close()

    @tool(annotations=annotations(destructive_hint=False, open_world_hint=True))
    def browser_create(live: bool = False, timeout_minutes: int = 30) -> dict[str, Any]:
        """Start a local browser sandbox; live mode also returns a view URL."""
        config = BrowserSessionConfig(
            mode="live" if live else "headless", timeout_minutes=timeout_minutes
        )
        session = _BrowserSandbox(config, state_manager=service.state_manager())
        try:
            session.start()
            return _browser_details(session)
        except Exception:
            with suppress(Exception):
                session.delete()
            raise

    @tool(annotations=annotations(read_only_hint=True, open_world_hint=False))
    def browser_list() -> dict[str, Any]:
        """List local browser sandboxes."""
        state = service.state_manager()
        browsers = []
        for item in state.list_browser_sessions():
            config = state.get_browser_session_config(item.session_id)
            if config.mode == "desktop":
                continue
            with _BrowserSandbox.from_id(item.session_id, state_manager=state) as session:
                browsers.append(_browser_details(session))
        return {"browsers": browsers}

    @tool(annotations=annotations(read_only_hint=True, open_world_hint=True))
    def browser_open(session_id: str) -> dict[str, Any]:
        """Return connection and view URLs for a browser sandbox."""
        state = service.state_manager()
        with _BrowserSandbox.from_id(session_id, state_manager=state) as session:
            return _browser_details(session)

    @tool(annotations=annotations(read_only_hint=True, open_world_hint=True))
    def browser_logs(session_id: str, lines: int = 100) -> dict[str, str]:
        """Read recent logs from a browser sandbox."""
        if not 1 <= lines <= 500:
            raise tool_error("Log lines must be between 1 and 500.")
        state = service.state_manager()
        with _BrowserSandbox.from_id(session_id, state_manager=state) as session:
            return {"session_id": session_id, "logs": session.logs(tail=lines)}

    @tool(annotations=annotations(destructive_hint=True, open_world_hint=True))
    def browser_stop(session_id: str) -> dict[str, str]:
        """Stop and delete a browser sandbox and its temporary files."""
        state = service.state_manager()
        session = _BrowserSandbox.from_id(session_id, state_manager=state)
        session.delete()
        return {"session_id": session_id, "state": "deleted"}

    @tool(annotations=annotations(read_only_hint=True, open_world_hint=False))
    def desktop_list() -> dict[str, Any]:
        """List local desktop sessions."""
        state = service.state_manager()
        desktops = []
        for item in state.list_browser_sessions():
            config = state.get_browser_session_config(item.session_id)
            if config.mode != "desktop":
                continue
            with _DesktopSandbox.from_id(item.session_id, state_manager=state) as session:
                desktops.append(_browser_details(session))
        return {"desktops": desktops}

    @tool(annotations=annotations(destructive_hint=False, open_world_hint=True))
    def desktop_create(timeout_minutes: int = 30) -> dict[str, Any]:
        """Start a visible Linux desktop and return its view and display URLs."""
        config = BrowserSessionConfig(mode="desktop", timeout_minutes=timeout_minutes)
        session = _DesktopSandbox(config, state_manager=service.state_manager())
        try:
            session.start()
            return _browser_details(session)
        except Exception:
            with suppress(Exception):
                session.delete()
            raise

    @tool(annotations=annotations(read_only_hint=True, open_world_hint=True))
    def desktop_open(session_id: str) -> dict[str, Any]:
        """Return the view and display URLs for an existing desktop session."""
        state = service.state_manager()
        with _DesktopSandbox.from_id(session_id, state_manager=state) as session:
            return _browser_details(session)

    @tool(annotations=annotations(destructive_hint=True, open_world_hint=True))
    def desktop_stop(session_id: str) -> dict[str, str]:
        """Stop and delete a desktop session and its temporary files."""
        state = service.state_manager()
        session = _DesktopSandbox.from_id(session_id, state_manager=state)
        session.delete()
        return {"session_id": session_id, "state": "deleted"}


def _browser_details(session: Any) -> dict[str, Any]:
    info = session.info
    return {
        "session_id": info.session_id,
        "computer_name": info.vm_id,
        "state": info.status.value,
        "cdp_url": info.cdp_url,
        "view_url": info.live_url,
        "display_url": info.vnc_url,
        "profile_id": info.profile_id,
    }

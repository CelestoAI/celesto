"""Attach browser/display clients to an existing local computer."""

from __future__ import annotations

import json
import shlex
import socket
import time
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

import httpx

from celesto._connection_info import DisplayMode
from celesto.exceptions import CelestoError
from celesto.types import BrowserConnection, BrowserSessionConfig, DisplayConnection, VMState

if TYPE_CHECKING:
    from celesto.facade import Celesto

_TIMEOUT = 30.0
_MAX_DISCOVERY = 64 * 1024
_HELPER = Path(__file__).parent / "images" / "guest_connections.py"


def validate_template_options(options: dict[str, Any]) -> None:
    allowed = {
        "backend",
        "data_dir",
        "socket_dir",
        "memory",
        "disk_size",
        "internet_settings",
        "mounts",
        "writable_mounts",
        "ssh_key_path",
        "ssh_user",
        "ssh_password",
        "comm_channel",
        "callbacks",
    }
    unknown = options.keys() - allowed
    if unknown:
        raise ValueError(
            f"Local browser-agent does not support {', '.join(sorted(unknown))}; "
            "omit those options."
        )
    _template_config(options)  # Validate before downloading an image or allocating a VM.


def _template_config(options: dict[str, Any]) -> BrowserSessionConfig:
    from celesto._network_policy import parse_network_policy
    from celesto.facade import _parse_mount_specs

    disk = options.get("disk_size") if options.get("disk_size") is not None else 8192
    if isinstance(disk, bool) or not isinstance(disk, int) or disk < 8192:
        raise ValueError("Local browser-agent needs disk_size of at least 8192 MiB.")
    policy = options.get("internet_settings")
    return BrowserSessionConfig(
        mode="computer",
        backend=options.get("backend") or "auto",
        mem_size_mib=options.get("memory") if options.get("memory") is not None else 2048,
        disk_size_mib=disk,
        internet_settings=parse_network_policy(policy) if policy is not None else None,
        workspace_mounts=_parse_mount_specs(
            options.get("mounts") or [], writable=options.get("writable_mounts", False)
        ),
    )


def template_runtime_options(options: dict[str, Any]) -> dict[str, Any]:
    from celesto.browser import _build_browser_vm_config

    config, key = _build_browser_vm_config(
        session_id=f"sbx-{uuid4().hex[:8]}",
        browser_config=_template_config(options),
        ssh_key_path=options.get("ssh_key_path"),
        forward_ports=False,
    )
    passthrough = {
        name: value
        for name, value in options.items()
        if name
        in {
            "data_dir",
            "socket_dir",
            "state_manager",
            "ssh_user",
            "ssh_password",
            "comm_channel",
            "callbacks",
        }
    }
    return {**passthrough, "config": config, "ssh_key_path": key}


def _remaining(deadline: float) -> float:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise CelestoError("The connection did not become ready in time; request a new connection.")
    return remaining


def _guest(vm: Celesto, args: list[str], deadline: float) -> dict[str, Any]:
    command = shlex.join(["python3", "-c", _HELPER.read_text(), *args])
    try:
        result = vm.run(command, timeout=max(1, int(_remaining(deadline))), shell="raw")
        _remaining(deadline)
        if not result.ok or len(result.stdout) > _MAX_DISCOVERY:
            raise ValueError
        payload = json.loads(result.stdout)
        if not isinstance(payload, dict):
            raise ValueError
        return payload
    except Exception:
        raise CelestoError(
            f"Computer '{vm.vm_id}' could not prepare a connection; "
            f"run 'celesto sandbox ssh {vm.vm_id}' to inspect /var/log/smolvm-browser."
        ) from None


def probe_capabilities(vm: Celesto, kind: str, deadline: float | None = None) -> None:
    deadline = deadline if deadline is not None else time.monotonic() + _TIMEOUT
    if vm.refresh().status != VMState.RUNNING:
        raise CelestoError(
            f"Computer '{vm.vm_id}' is not running; run 'celesto sandbox start {vm.vm_id}'."
        )
    caps = _guest(vm, ["capabilities"], deadline)
    if caps.get("version") != 1 or caps.get(kind) is not True:
        raise CelestoError(
            f"Computer '{vm.vm_id}' does not support this connection; "
            "create a Computer(local=True, template_id='browser-agent')."
        )


def local_connection(
    vm: Celesto,
    kind: str,
    forwards: dict[int, int],
) -> BrowserConnection | DisplayConnection:
    from celesto.browser import _guest_browser_proxy_endpoint

    deadline = time.monotonic() + _TIMEOUT
    probe_capabilities(vm, kind, deadline)
    info = vm.info
    if info.network is not None and info.network.mode == "bridge":
        raise CelestoError(
            f"Computer '{vm.vm_id}' cannot provide local connections with bridged networking; "
            "create a Computer(local=True, template_id='browser-agent') with default networking."
        )
    policy = info.config.internet_settings
    if (
        policy is not None
        and policy.has_explicit_restrictions is True
        and info.config.backend != "qemu"
    ):
        raise CelestoError(
            f"Computer '{vm.vm_id}' cannot provide connections with this network configuration; "
            "create a browser-agent computer with backend='qemu'."
        )
    proxy = _guest_browser_proxy_endpoint(vm.info)
    args = ["ensure", kind, str(_remaining(deadline))]
    if proxy is not None:
        args.append(proxy)
    result = _guest(vm, args, deadline)
    port = {"browser": 9223, "read_only": 6081, "read_write": 6082}[kind]
    if result.get("port") != port:
        raise CelestoError("The computer returned an invalid connection; request a new connection.")
    previous = forwards.get(port)
    if previous is not None and not _forward_alive(previous):
        vm.unexpose_local(previous, port)
        forwards.pop(port)
        previous = None
    host_port = previous
    try:
        # Linux can run commands over vsock without ever preparing network SSH.
        # Loopback-only graphical services still need an SSH tunnel (and, with
        # QEMU slirp, its host-to-guest SSH forward) before exposing their port.
        vm._ensure_ssh_for_operation(
            action="connect to browser or display", timeout=_remaining(deadline)
        )
        host_port = vm.expose_local(port, host_port=previous, guest_loopback=True)
        _remaining(deadline)
        if kind == "browser":
            # Ignore HTTP proxy environment variables and never follow redirects.
            with (
                httpx.Client(trust_env=False, follow_redirects=False) as client,
                client.stream(
                    "GET",
                    f"http://127.0.0.1:{host_port}/json/version",
                    timeout=_remaining(deadline),
                ) as response,
            ):
                response.raise_for_status()
                data = bytearray()
                for chunk in response.iter_bytes():
                    _remaining(deadline)
                    data.extend(chunk)
                    if len(data) > _MAX_DISCOVERY:
                        raise ValueError
            ws = urlsplit(json.loads(data)["webSocketDebuggerUrl"])
            if ws.scheme != "ws" or not ws.hostname or ws.username or ws.password or ws.fragment:
                raise ValueError
            if not ws.path.startswith("/devtools/browser/"):
                raise ValueError
            url = urlunsplit(("ws", f"127.0.0.1:{host_port}", ws.path, ws.query, ""))
            connection: BrowserConnection | DisplayConnection = BrowserConnection(url, None)
        else:
            mode: DisplayMode = "read_only" if kind == "read_only" else "read_write"
            connection = DisplayConnection(f"ws://127.0.0.1:{host_port}/", None, mode)
        _remaining(deadline)
    except Exception:
        if host_port is not None and host_port != previous:
            with suppress(Exception):
                vm.unexpose_local(host_port, port)
        raise CelestoError(
            f"Computer '{vm.vm_id}' could not connect; "
            f"run 'celesto sandbox ssh {vm.vm_id}' to inspect /var/log/smolvm-browser."
        ) from None
    forwards[port] = host_port
    return connection


def _forward_alive(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.25):
            return True
    except OSError:
        return False

# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""Run one credential proxy per sandbox and wire the guest to it.

``attach`` starts this sandbox's proxy process, points the guest's proxy
address at it, and installs the CA, host routes, placeholder env, and
placeholder files in the guest. ``detach`` stops it. ``control`` changes a
running proxy (D-15). ``status`` reports whether protection is running
(D-16). See docs/designs/sandbox-credential-injection.md (D-04, D-05, D-07,
D-14-D-16).
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import select
import shutil
import signal
import socket
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from celesto.credentials import guest
from celesto.credentials._runtime_paths import (
    PROXY_GUEST_IP,
    ProxyPaths,
    ensure_dirs,
    proxy_paths,
)
from celesto.credentials.types import Binding, CredentialPlan, LocalRoute
from celesto.exceptions import CelestoError

logger = logging.getLogger(__name__)

_HANDSHAKE_TIMEOUT = 20.0
_STOP_TIMEOUT = 5.0
_LAUNCHER_MODULE = "celesto.runtime._credential_proxy"

# The launcher gets only what it needs from the host env. Real API keys in the
# user's terminal (OPENAI_API_KEY, ...) must not leak into a child's env.
_ENV_ALLOWLIST = (
    "PATH",
    "HOME",
    "USER",
    "LOGNAME",
    "LANG",
    "LC_ALL",
    "TMPDIR",
    "VIRTUAL_ENV",
    "PYTHONPATH",
    "SSH_AUTH_SOCK",
    "XDG_CONFIG_HOME",
    "XDG_STATE_HOME",
    "CODEX_HOME",
    "CLAUDE_CONFIG_DIR",
)

ProxyState = Literal["not_configured", "inactive", "running", "stopped"]


class CredentialsUnsupported(CelestoError):  # noqa: N818 - name fixed by the build contract
    """This sandbox's network can't route credentials to a proxy (D-07).

    The sandbox keeps running; no credentials are delivered. The message is
    user-facing and names the recovery command.
    """


@dataclass(frozen=True)
class ProxyHandle:
    """A running per-sandbox proxy."""

    sandbox_id: str
    pid: int
    vm_pid: int
    address: str
    ca_cert_pem: str = field(repr=False)
    control_socket: Path
    proxy_socket: Path | None
    log_path: Path


@dataclass(frozen=True)
class ProxyStatus:
    """Whether a sandbox's credential protection is running."""

    sandbox_id: str
    state: ProxyState
    pid: int | None = None
    message: str | None = None
    """User-facing D-16 message when protection stopped; otherwise ``None``."""
    stats: dict[str, Any] = field(default_factory=dict)


def stopped_message(sandbox_id: str) -> str:
    """D-16 message for a sandbox whose proxy is gone while it runs."""
    return (
        f"Credential protection stopped for {sandbox_id}. Run 'celesto computer stop "
        f"{sandbox_id}' and 'celesto computer start {sandbox_id}' to restore it."
    )


# ---------------------------------------------------------------------------
# Backend support (D-07)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Route:
    kind: Literal["slirp", "tap"]
    tap_device: str | None = None
    host_ip: str | None = None


def _resolve_route(vm_info: Any, backend: str) -> _Route:
    name = vm_info.vm_id
    network = vm_info.network
    if network is not None and network.mode == "bridge":
        raise CredentialsUnsupported(
            f"Credentials can't be protected in {name} because it uses bridge networking, "
            f"so Celesto didn't put any in it. Run 'celesto computer delete {name}' and create "
            "it again without '--network bridge' to use them.",
            {"vm_id": name, "reason": "bridge"},
        )
    settings = vm_info.config.internet_settings
    restricted = (settings is not None and settings.mode != "open") or (
        network is not None and network.egress_proxy_host_port is not None
    )
    if network is None or restricted:
        raise CredentialsUnsupported(
            f"Credentials can't be protected in {name} because its internet access is "
            f"limited, so Celesto didn't put any in it. Run 'celesto computer delete {name}' "
            "and create it again with full internet access to use them.",
            {"vm_id": name, "reason": "restricted_network"},
        )
    if backend == "qemu" and vm_info.config.qemu_network != "tap":
        return _Route("slirp")
    if backend in {"qemu", "firecracker"} and network.gateway_ip and network.tap_device:
        return _Route("tap", tap_device=network.tap_device, host_ip=network.gateway_ip)
    raise CredentialsUnsupported(
        f"Credentials can't be protected in {name} on the {backend} backend yet, so "
        f"Celesto didn't put any in it. Run 'celesto computer delete {name}' and create it "
        "again with '--backend qemu' to use them.",
        {"vm_id": name, "reason": "backend", "backend": backend},
    )


# ---------------------------------------------------------------------------
# Launch spec
# ---------------------------------------------------------------------------


def _as_dict(item: Any) -> dict[str, Any]:
    if is_dataclass(item) and not isinstance(item, type):
        return asdict(item)
    return dict(item)


def _binding_dict(binding: Binding | dict[str, Any]) -> dict[str, Any]:
    data = _as_dict(binding)
    return {
        "name": str(data["name"]),
        "placeholder": str(data["placeholder"]),
        "hosts": [str(h) for h in data["hosts"]],
        "headers": [
            {"header": str(_as_dict(r)["header"]), "form": str(_as_dict(r)["form"])}
            for r in data["headers"]
        ],
    }


def _route_dict(route: LocalRoute | dict[str, Any]) -> dict[str, str]:
    data = _as_dict(route)
    return {key: str(data[key]) for key in ("host", "path", "handler")}


def plan_hosts(plan: CredentialPlan) -> list[str]:
    """Every host the guest must route to the proxy for *plan*."""
    hosts = {h for b in plan.bindings for h in b.hosts}
    hosts.update(r.host for r in plan.local_routes)
    return sorted(hosts)


def _launcher_env() -> dict[str, str]:
    env = {key: os.environ[key] for key in _ENV_ALLOWLIST if key in os.environ}
    env["PYTHONUNBUFFERED"] = "1"
    return env


def _read_state(paths: ProxyPaths) -> dict[str, Any] | None:
    try:
        data = json.loads(paths.state_file.read_text())
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _pid_alive(pid: int | None) -> bool:
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _is_our_launcher(pid: int) -> bool:
    """Guard against PID reuse before signalling a recorded proxy PID."""
    try:
        result = subprocess.run(
            ["ps", "-o", "command=", "-p", str(pid)],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return _LAUNCHER_MODULE in result.stdout


def _terminate(pid: int) -> None:
    if not _pid_alive(pid) or not _is_our_launcher(pid):
        return
    with contextlib.suppress(ProcessLookupError):
        os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + _STOP_TIMEOUT
    while time.monotonic() < deadline and _pid_alive(pid):
        with contextlib.suppress(ChildProcessError):
            os.waitpid(pid, os.WNOHANG)
        time.sleep(0.05)
    if _pid_alive(pid):
        with contextlib.suppress(ProcessLookupError):
            os.kill(pid, signal.SIGKILL)


def _spawn(
    spec: dict[str, Any], paths: ProxyPaths
) -> tuple[subprocess.Popen[bytes], dict[str, str]]:
    launcher_log = open(paths.launcher_log, "ab")  # noqa: SIM115 - handed to the child
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", _LAUNCHER_MODULE],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=launcher_log,
            env=_launcher_env(),
            cwd=str(paths.state_dir),
            start_new_session=True,
        )
    finally:
        launcher_log.close()
    assert process.stdin is not None and process.stdout is not None
    try:
        process.stdin.write(json.dumps(spec).encode())
        process.stdin.close()
        ready, _, _ = select.select([process.stdout], [], [], _HANDSHAKE_TIMEOUT)
        line = process.stdout.readline() if ready else b""
        process.stdout.close()
        info = json.loads(line) if line.strip() else None
    except (OSError, ValueError):
        info = None
    if not isinstance(info, dict) or "ca_cert_pem" not in info:
        with contextlib.suppress(ProcessLookupError):
            process.kill()
        with contextlib.suppress(subprocess.TimeoutExpired):
            process.wait(timeout=_STOP_TIMEOUT)
        raise CelestoError(
            f"Celesto couldn't start credential protection for {spec['sandbox_id']}. "
            f"Run 'celesto computer stop {spec['sandbox_id']}' and "
            f"'celesto computer start {spec['sandbox_id']}' to try again.",
            {"vm_id": spec["sandbox_id"], "launcher_log": str(paths.launcher_log)},
        )
    return process, {"address": str(info["address"]), "ca_cert_pem": str(info["ca_cert_pem"])}


def _require_proxy_build(sandbox_id: str) -> None:
    try:
        from celesto_core import credential_proxy
    except ImportError:
        available = False
    else:
        available = credential_proxy.available()
    if not available:
        raise CelestoError(
            f"This Celesto install can't protect credentials in {sandbox_id}. "
            "Run 'uv tool upgrade celesto' to update it, then start the computer again.",
            {"vm_id": sandbox_id, "reason": "celesto_core_without_proxy"},
        )


def _port_of(address: str) -> int:
    return int(address.rsplit(":", 1)[-1])


# ---------------------------------------------------------------------------
# Guest plumbing through the facade
# ---------------------------------------------------------------------------


def _guest_env_writer(vm: Any) -> Any:
    def write(values: dict[str, str]) -> None:
        channel = vm._control_env_channel()
        if channel is not None:
            channel.set_managed_env(values)
            return
        from celesto.env import inject_env_vars

        inject_env_vars(vm._ensure_ssh_for_env(), values)

    return write


def _guest_env_remover(vm: Any) -> Any:
    def remove(keys: list[str]) -> None:
        channel = vm._control_env_channel()
        if channel is not None:
            channel.unset_managed_env(keys)
            return
        from celesto.env import read_env_vars

        ssh = vm._ensure_ssh_for_env()
        current = read_env_vars(ssh)
        remaining = {k: v for k, v in current.items() if k not in set(keys)}
        from celesto.env import inject_env_vars

        inject_env_vars(ssh, remaining, merge=False)

    return remove


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def attach(
    vm: Any,
    plan: CredentialPlan,
    *,
    test_hooks: dict[str, Any] | None = None,
) -> ProxyHandle:
    """Start this sandbox's proxy and install the plan in the guest.

    *vm* is a running :class:`celesto.facade.Celesto`. Calling ``attach``
    again replaces the running proxy with a fresh one (new CA, D-14) and
    reinstalls the guest side. Raises :class:`CredentialsUnsupported` when
    the sandbox's network can't be protected (D-07); nothing is started or
    written to the guest in that case.

    *test_hooks* is for tests only (see ``celesto.runtime._credential_proxy``).
    """
    sandbox_id = str(vm.vm_id)
    manager = vm._sdk
    vm_info = manager.get(sandbox_id)
    backend = manager._backend_for_vm(vm_info)
    route = _resolve_route(vm_info, backend)
    if vm_info.pid is None or not _pid_alive(vm_info.pid):
        raise CelestoError(
            f"{sandbox_id} isn't running. Run 'celesto computer start {sandbox_id}' first.",
            {"vm_id": sandbox_id},
        )
    _require_proxy_build(sandbox_id)

    data_dir = Path(manager.data_dir)
    detach(sandbox_id, data_dir=data_dir, network=manager.network)
    paths = proxy_paths(data_dir, sandbox_id)
    ensure_dirs(paths)

    listen = f"unix:{paths.proxy_socket}" if route.kind == "slirp" else f"tcp:{route.host_ip}:0"
    spec: dict[str, Any] = {
        "sandbox_id": sandbox_id,
        "listen": listen,
        "log_path": str(paths.log_path),
        "control_socket": str(paths.control_socket),
        "vm_pid": int(vm_info.pid),
        "bindings": [_binding_dict(b) for b in plan.bindings],
        "local_routes": [_route_dict(r) for r in plan.local_routes],
        "real_values": dict(plan.real_values),
        "ssh": {
            # The launcher env is scrubbed; hand W6's filter the host agent.
            "host_agent_socket": os.environ.get("SSH_AUTH_SOCK"),
            "data_dir": str(data_dir),
            **dict(getattr(plan, "ssh", None) or {}),
        },
    }
    if test_hooks:
        spec["test_hooks"] = dict(test_hooks)

    process, info = _spawn(spec, paths)
    del spec
    state = {
        "pid": process.pid,
        "vm_pid": int(vm_info.pid),
        "address": info["address"],
        "route": route.kind,
        "tap_device": route.tap_device,
        "started_at": datetime.now(UTC).isoformat(),
    }
    paths.state_file.write_text(json.dumps(state))
    os.chmod(paths.state_file, 0o600)

    try:
        if route.kind == "tap":
            assert route.tap_device is not None and route.host_ip is not None
            manager.network.apply_credential_forward(
                route.tap_device,
                guest_proxy_ip=PROXY_GUEST_IP,
                proxy_host_ip=route.host_ip,
                proxy_port=_port_of(info["address"]),
            )
        guest.install(
            vm._ensure_control_for_file_transfer(),
            sandbox_id=sandbox_id,
            ca_cert_pem=info["ca_cert_pem"],
            hosts=plan_hosts(plan),
            env={**_ssh_guest_env(), **plan.guest_env},
            files=plan.guest_files,
            set_env=_guest_env_writer(vm),
        )
        finish_guest_setup(vm)
    except BaseException:
        detach(sandbox_id, data_dir=data_dir, network=manager.network)
        raise

    for warning in plan.missing:
        logger.warning("%s", warning)
    return ProxyHandle(
        sandbox_id=sandbox_id,
        pid=process.pid,
        vm_pid=int(vm_info.pid),
        address=info["address"],
        ca_cert_pem=info["ca_cert_pem"],
        control_socket=paths.control_socket,
        proxy_socket=paths.proxy_socket if route.kind == "slirp" else None,
        log_path=paths.log_path,
    )


def _ssh_guest_env() -> dict[str, str]:
    try:
        from celesto.credentials import ssh
    except ImportError:
        return {}
    return dict(ssh.guest_env())


def finish_guest_setup(vm: Any) -> None:
    """Install guest config that later config copies could overwrite (D-13).

    ``attach`` runs this itself. A caller that copies host configs (for
    example a ``~/.gitconfig``) into the guest after ``attach`` must call it
    again afterwards, so the GitHub SSH-to-HTTPS rewrite survives.
    """
    try:
        from celesto.credentials import ssh
    except ImportError:
        return
    guest.run_script(
        vm._ensure_control_for_file_transfer(),
        ssh.guest_setup_script(),
        what="setting up SSH",
        sandbox_id=str(vm.vm_id),
    )


def detach(sandbox_id: str, *, data_dir: Path | None = None, network: Any = None) -> None:
    """Stop this sandbox's proxy (if any) and remove its sockets and forward.

    Safe to call when nothing is running. The proxy log is kept.
    """
    paths = proxy_paths(_data_dir(data_dir), sandbox_id)
    state = _read_state(paths)
    if state is not None:
        pid = state.get("pid")
        if isinstance(pid, int):
            _terminate(pid)
        tap = state.get("tap_device")
        if state.get("route") == "tap" and isinstance(tap, str) and network is not None:
            with contextlib.suppress(Exception):
                network.remove_credential_forward(tap)
    for path in (paths.state_file, paths.control_socket, paths.proxy_socket):
        with contextlib.suppress(FileNotFoundError):
            path.unlink()


def forget(sandbox_id: str, *, data_dir: Path | None = None, network: Any = None) -> None:
    """Detach and delete everything kept for a deleted sandbox, logs included."""
    detach(sandbox_id, data_dir=data_dir, network=network)
    paths = proxy_paths(_data_dir(data_dir), sandbox_id)
    shutil.rmtree(paths.state_dir, ignore_errors=True)
    if paths.socket_dir != paths.state_dir / "run":
        shutil.rmtree(paths.socket_dir, ignore_errors=True)


def control(
    sandbox_id: str,
    op: str,
    *,
    data_dir: Path | None = None,
    timeout: float = 5.0,
    vm: Any = None,
    **kw: Any,
) -> dict[str, Any]:
    """Send one control request to this sandbox's running proxy (D-15).

    Ops: ``status``; ``set_binding(binding: dict, real_value: str)``;
    ``remove_binding(name: str)``. Returns the proxy's JSON reply, which for
    set/remove includes ``hosts`` (every host the guest should now route).
    ``status`` returns ``bindings`` (``[{name, has_value}]``), ``missing``,
    ``last_used``, ``hosts``, and ``stats``.

    Pass the running sandbox as *vm* (a :class:`celesto.facade.Celesto`) to
    also rewrite the guest's ``/etc/hosts`` block after a set/remove, so new
    hosts route to the proxy and dropped ones stop. The placeholder env is
    the caller's to update (see :func:`update_guest`).

    Raises :class:`CelestoError` with the D-16 message when no proxy answers.
    """
    if op not in {"status", "set_binding", "remove_binding"}:
        raise ValueError(f"Unknown credential proxy op: {op!r}")
    request: dict[str, Any] = {"op": op}
    if op == "set_binding":
        request["binding"] = _binding_dict(kw["binding"])
        request["real_value"] = kw.get("real_value")
    elif op == "remove_binding":
        request["name"] = str(kw["name"])
    paths = proxy_paths(_data_dir(data_dir), sandbox_id)
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
            conn.settimeout(timeout)
            conn.connect(str(paths.control_socket))
            conn.sendall(json.dumps(request).encode() + b"\n")
            data = b""
            while not data.endswith(b"\n"):
                chunk = conn.recv(65536)
                if not chunk:
                    break
                data += chunk
        reply = json.loads(data.decode())
    except (OSError, ValueError) as exc:
        raise CelestoError(stopped_message(sandbox_id), {"vm_id": sandbox_id}) from exc
    if not isinstance(reply, dict) or not reply.get("ok"):
        error = reply.get("error") if isinstance(reply, dict) else None
        raise CelestoError(
            f"Credential protection for {sandbox_id} refused the change ({error}).",
            {"vm_id": sandbox_id, "op": op},
        )
    if vm is not None and op != "status":
        update_guest(vm, hosts=[str(h) for h in reply.get("hosts", [])])
    return reply


def update_guest(
    vm: Any,
    *,
    hosts: list[str],
    set_env: dict[str, str] | None = None,
    unset_env: list[str] | None = None,
) -> None:
    """Apply a live change to the guest: host routes and placeholder env (D-15)."""
    sandbox_id = str(vm.vm_id)
    guest.write_hosts(vm._ensure_control_for_file_transfer(), hosts, sandbox_id=sandbox_id)
    if set_env:
        _guest_env_writer(vm)(dict(set_env))
    if unset_env:
        _guest_env_remover(vm)(list(unset_env))


def status(
    sandbox_id: str,
    *,
    data_dir: Path | None = None,
    vm_info: Any = None,
) -> ProxyStatus:
    """Report whether credential protection is running for *sandbox_id* (D-16).

    ``not_configured``: this sandbox never had a proxy. ``inactive``: the VM
    that had one is no longer running. ``running``: the proxy answers.
    ``stopped``: the VM runs but its proxy is gone; ``message`` says how to
    restore it. Pass *vm_info* to also catch a VM restarted without one.
    """
    paths = proxy_paths(_data_dir(data_dir), sandbox_id)
    state = _read_state(paths)
    if state is None:
        return ProxyStatus(sandbox_id, "not_configured")
    vm_pid = state.get("vm_pid")
    vm_running = _pid_alive(vm_pid if isinstance(vm_pid, int) else None)
    if vm_info is not None:
        status_value = getattr(vm_info.status, "value", vm_info.status)
        live_pid = vm_info.pid if status_value == "running" else None
        if live_pid is None:
            return ProxyStatus(sandbox_id, "inactive")
        if live_pid != vm_pid:
            return ProxyStatus(sandbox_id, "stopped", message=stopped_message(sandbox_id))
        vm_running = _pid_alive(live_pid)
    if not vm_running:
        return ProxyStatus(sandbox_id, "inactive")
    pid = state.get("pid") if isinstance(state.get("pid"), int) else None
    try:
        reply = control(sandbox_id, "status", data_dir=data_dir, timeout=2.0)
    except CelestoError:
        return ProxyStatus(sandbox_id, "stopped", pid=pid, message=stopped_message(sandbox_id))
    raw_stats = reply.get("stats")
    stats: dict[str, Any] = raw_stats if isinstance(raw_stats, dict) else {}
    return ProxyStatus(sandbox_id, "running", pid=pid, stats=stats)


def log_path(sandbox_id: str, *, data_dir: Path | None = None) -> Path:
    """Path of the sandbox's credential activity log (D-18)."""
    return proxy_paths(_data_dir(data_dir), sandbox_id).log_path


def attach_on_start(vm: Any) -> ProxyHandle | None:
    """Re-protect a sandbox at start when it has credentials (D-09).

    Builds the plan from the computer's user secrets (D-20); does nothing for
    a computer with no credentials.
    Re-raises :class:`CredentialsUnsupported` for the caller to report.
    """
    from celesto.credentials.plan import build_plan

    plan = build_plan(vm.vm_id, vm._sdk.state)
    if not (plan.bindings or plan.local_routes or plan.guest_env or plan.guest_files):
        return None
    return attach(vm, plan)


def _data_dir(data_dir: Path | None) -> Path:
    if data_dir is not None:
        return Path(data_dir)
    from celesto.vm import resolve_data_dir

    return resolve_data_dir(None)


__all__ = [
    "CredentialsUnsupported",
    "ProxyHandle",
    "ProxyStatus",
    "attach",
    "attach_on_start",
    "control",
    "detach",
    "finish_guest_setup",
    "forget",
    "log_path",
    "plan_hosts",
    "status",
    "stopped_message",
    "update_guest",
]

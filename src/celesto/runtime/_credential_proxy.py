# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""Per-sandbox credential proxy process.

Started by :func:`celesto.credentials.runtime.attach` as
``python -m celesto.runtime._credential_proxy``. It:

1. reads one LaunchSpec JSON document from stdin (never argv or env, because
   it carries real values);
2. runs ``celesto_core.credential_proxy.CredentialProxy`` for this sandbox
   only, with a fresh in-memory CA;
3. prints one JSON line ``{"address", "ca_cert_pem"}`` on stdout;
4. serves a private (0600) control socket for live changes (D-15);
5. exits, stopping the proxy, when the sandbox's VM process exits (D-16).

LaunchSpec fields: ``sandbox_id``, ``listen``, ``log_path``,
``control_socket``, ``vm_pid``, ``bindings``, ``local_routes``,
``real_values``, and an optional ``ssh`` (W6) entry.

Test-only field ``test_hooks``: ``upstream_hosts`` ({host: "ip:port"}) and
``upstream_ca_pem`` make the proxy reach a local TLS stub instead of the
real host. Only the parent process can set them, because the LaunchSpec
arrives only on this process's stdin.

Nothing this process writes to stderr or its log may hold a real value or a
placeholder.
"""

from __future__ import annotations

import contextlib
import importlib
import json
import os
import signal
import socket
import subprocess
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

_WATCH_INTERVAL = 1.0
_MAX_REQUEST = 1 << 20


def _pid_alive(pid: int) -> bool:
    """True while *pid* runs. A zombie (exited, not yet reaped) counts as gone."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    proc_stat = Path(f"/proc/{pid}/stat")
    if proc_stat.exists():
        with contextlib.suppress(OSError, IndexError):
            return proc_stat.read_text().rsplit(")", 1)[1].split()[0] != "Z"
        return True
    try:
        state = subprocess.run(
            ["ps", "-o", "stat=", "-p", str(pid)],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return True
    return bool(state) and not state.startswith("Z")


def _bound_hosts(bindings: dict[str, dict[str, Any]], routes: list[dict[str, Any]]) -> list[str]:
    hosts = {str(h) for b in bindings.values() for h in b.get("hosts", [])}
    hosts.update(str(r["host"]) for r in routes)
    return sorted(hosts)


class _Launcher:
    def __init__(self, spec: dict[str, Any], proxy: Any) -> None:
        self.spec = spec
        self.proxy = proxy
        self.lock = threading.Lock()
        self.bindings: dict[str, dict[str, Any]] = {
            str(b["name"]): dict(b) for b in spec.get("bindings", [])
        }
        self.routes: list[dict[str, Any]] = list(spec.get("local_routes", []))
        self.real_values: dict[str, str] = spec.setdefault("real_values", {})
        self.stopping = threading.Event()

    # -- control socket ---------------------------------------------------

    def handle(self, request: dict[str, Any]) -> dict[str, Any]:
        op = request.get("op")
        with self.lock:
            if op == "status":
                stats = self.proxy.stats()
                return {
                    "ok": True,
                    "pid": os.getpid(),
                    "vm_pid": self.spec.get("vm_pid"),
                    "bindings": [
                        {"name": name, "has_value": bool(self.real_values.get(name))}
                        for name in sorted(self.bindings)
                    ],
                    "missing": sorted(n for n in self.bindings if not self.real_values.get(n)),
                    "last_used": dict(stats.get("last_used") or {}),
                    "hosts": _bound_hosts(self.bindings, self.routes),
                    "stats": stats,
                }
            if op == "set_binding":
                binding = dict(request["binding"])
                name = str(binding["name"])
                real_value = request.get("real_value")
                candidate = {**self.bindings, name: binding}
                self.proxy.set_bindings(list(candidate.values()))
                self.bindings = candidate
                if isinstance(real_value, str):
                    self.real_values[name] = real_value
                else:
                    self.real_values.pop(name, None)
                return {"ok": True, "hosts": _bound_hosts(self.bindings, self.routes)}
            if op == "remove_binding":
                name = str(request["name"])
                remaining = {k: v for k, v in self.bindings.items() if k != name}
                self.real_values.pop(name, None)
                self.proxy.set_bindings(list(remaining.values()))
                self.bindings = remaining
                return {"ok": True, "hosts": _bound_hosts(self.bindings, self.routes)}
        return {"ok": False, "error": f"unknown op {op!r}"}

    def _serve_one(self, conn: socket.socket) -> None:
        with conn:
            conn.settimeout(10)
            data = b""
            while b"\n" not in data and len(data) < _MAX_REQUEST:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                data += chunk
            try:
                response = self.handle(json.loads(data.decode()))
            except Exception as exc:  # noqa: BLE001 - report, never echo the request
                response = {"ok": False, "error": type(exc).__name__}
            conn.sendall(json.dumps(response).encode() + b"\n")

    def serve_control(self, path: Path) -> socket.socket:
        with contextlib.suppress(FileNotFoundError):
            path.unlink()
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        old_umask = os.umask(0o177)
        try:
            server.bind(str(path))
        finally:
            os.umask(old_umask)
        os.chmod(path, 0o600)
        server.listen(8)

        def loop() -> None:
            while not self.stopping.is_set():
                try:
                    conn, _ = server.accept()
                except OSError:
                    return
                threading.Thread(target=self._serve_one, args=(conn,), daemon=True).start()

        threading.Thread(target=loop, daemon=True).start()
        return server


def _optional_hook(module: str, attr: str) -> Callable[..., Any] | None:
    try:
        loaded = importlib.import_module(module)
    except ImportError:
        return None
    hook = getattr(loaded, attr, None)
    return hook if callable(hook) else None


def run(spec: dict[str, Any], out: Any) -> int:
    from celesto_core.credential_proxy import CredentialProxy

    hooks = spec.get("test_hooks") or {}
    listen = str(spec["listen"])
    if listen.startswith("unix:"):
        with contextlib.suppress(FileNotFoundError):
            Path(listen[5:]).unlink()
    proxy = CredentialProxy(
        listen=listen,
        log_path=str(spec["log_path"]),
        _upstream_ca_pem=hooks.get("upstream_ca_pem"),
        _upstream_hosts=hooks.get("upstream_hosts"),
    )
    launcher = _Launcher(spec, proxy)
    control_path = Path(spec["control_socket"])
    server: socket.socket | None = None
    ssh_service: Any = None
    try:
        proxy.set_bindings(list(launcher.bindings.values()))
        proxy.set_local_routes(launcher.routes)
        real_values = launcher.real_values
        proxy.set_resolver(lambda name: real_values.get(name))
        serve_ssh = _optional_hook("celesto.credentials.ssh", "serve")
        if serve_ssh is not None:
            ssh_service = serve_ssh(spec)
        info = proxy.start()
        if listen.startswith("unix:"):
            os.chmod(listen[5:], 0o600)
        server = launcher.serve_control(control_path)

        def _stop(*_args: Any) -> None:
            launcher.stopping.set()

        signal.signal(signal.SIGTERM, _stop)
        signal.signal(signal.SIGINT, _stop)
        signal.signal(signal.SIGHUP, signal.SIG_IGN)

        out.write(json.dumps({"address": info["address"], "ca_cert_pem": info["ca_cert_pem"]}))
        out.write("\n")
        out.flush()
        out.close()

        vm_pid = int(spec["vm_pid"])
        while not launcher.stopping.is_set() and _pid_alive(vm_pid):
            launcher.stopping.wait(_WATCH_INTERVAL)
        return 0
    finally:
        launcher.stopping.set()
        if server is not None:
            server.close()
        if ssh_service is not None:
            with contextlib.suppress(Exception):
                ssh_service.stop()
        proxy.stop()
        with contextlib.suppress(FileNotFoundError):
            control_path.unlink()
        if listen.startswith("unix:"):
            with contextlib.suppress(FileNotFoundError):
                Path(listen[5:]).unlink()


def main() -> int:
    spec = json.loads(sys.stdin.read())
    sys.stdin.close()
    # Keep a private handle on stdout for the one handshake line; anything
    # else printed by accident goes to stderr (the launcher log), never to a
    # closed pipe.
    out = os.fdopen(os.dup(1), "w")
    os.dup2(2, 1)
    try:
        return run(spec, out)
    except Exception as exc:  # noqa: BLE001 - the parent reports a clear error
        # Only the type: a message could quote a spec value.
        print(f"credential proxy failed: {type(exc).__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""Where one sandbox's credential proxy keeps its sockets, pid file, and log.

Kept free of heavy imports: the QEMU argv builder imports it to point the
guest's proxy address at this sandbox's own proxy socket.
"""

from __future__ import annotations

import hashlib
import os
import re
import shlex
import stat
import sys
from dataclasses import dataclass
from pathlib import Path

PROXY_GUEST_IP = "10.0.2.100"
"""Address the guest's ``/etc/hosts`` maps bound hosts to (port 443)."""

PROXY_GUEST_IPV6 = "::ffff:10.0.2.100"
"""IPv4-mapped form, so an IPv6-only lookup still lands on the proxy."""

PROXY_GUEST_PORT = 443

# macOS limits sun_path to 104 bytes, Linux to 108; leave headroom.
_MAX_SOCKET_PATH = 100
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


@dataclass(frozen=True)
class ProxyPaths:
    """Files for one sandbox's credential proxy."""

    state_dir: Path
    """Durable per-sandbox dir: log, launcher state, launcher stderr."""
    socket_dir: Path
    """Private (0700) dir holding the Unix sockets."""

    @property
    def proxy_socket(self) -> Path:
        return self.socket_dir / "proxy.sock"

    @property
    def control_socket(self) -> Path:
        return self.socket_dir / "control.sock"

    @property
    def log_path(self) -> Path:
        return self.state_dir / "proxy.log"

    @property
    def launcher_log(self) -> Path:
        return self.state_dir / "launcher.log"

    @property
    def state_file(self) -> Path:
        return self.state_dir / "proxy.json"


def _check_id(sandbox_id: str) -> str:
    if not _SAFE_ID.match(sandbox_id):
        raise ValueError(f"Invalid computer name: {sandbox_id!r}")
    return sandbox_id


def proxy_paths(data_dir: Path, sandbox_id: str) -> ProxyPaths:
    """Return the proxy file layout for *sandbox_id* without creating anything."""
    state_dir = Path(data_dir) / "credentials" / _check_id(sandbox_id)
    socket_dir = state_dir / "run"
    if len(str(socket_dir / "control.sock")) > _MAX_SOCKET_PATH:
        digest = hashlib.sha256(str(state_dir.resolve()).encode()).hexdigest()[:16]
        socket_dir = Path("/tmp") / f"celesto-cred-{os.getuid()}" / digest
    return ProxyPaths(state_dir=state_dir, socket_dir=socket_dir)


def _private_dir(path: Path) -> None:
    """Create *path* (and a short-path parent) as 0700 dirs owned by this user."""
    for directory in (
        (path.parent, path) if path.parent.name.startswith("celesto-cred-") else (path,)
    ):
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = directory.lstat()
        if stat.S_ISLNK(info.st_mode) or info.st_uid != os.getuid():
            raise PermissionError(f"Refusing to use {directory}: it is not a private directory.")
        os.chmod(directory, 0o700)


def ensure_dirs(paths: ProxyPaths) -> None:
    """Create the state and socket dirs with owner-only permissions."""
    _private_dir(paths.state_dir)
    _private_dir(paths.socket_dir)


def relay_script() -> Path:
    """Path of the stdlib-only relay QEMU runs for each guest connection."""
    return Path(__file__).resolve().parent.parent / "runtime" / "_credential_relay.py"


def relay_command(data_dir: Path, sandbox_id: str) -> str:
    """Shell-quoted command QEMU's ``guestfwd`` runs per guest connection.

    ``-I -S`` keeps start-up fast and stops the relay importing anything from
    the current directory or the user's site-packages.
    """
    socket = proxy_paths(data_dir, sandbox_id).proxy_socket
    return " ".join(
        shlex.quote(part) for part in (sys.executable, "-I", "-S", str(relay_script()), str(socket))
    )

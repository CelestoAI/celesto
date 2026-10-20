# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""SSH for sandboxes without copying SSH keys in (D-13).

Two pieces:

- GitHub SSH URLs go over HTTPS. The guest's global git config rewrites
  ``git@github.com:`` and ``ssh://git@github.com/`` to ``https://github.com/``
  so pushes use the HTTPS token injection instead of an SSH key.
- Other SSH uses a filtered agent. A per-sandbox filter sits in front of the
  host's ``SSH_AUTH_SOCK`` (ssh-agent, 1Password, ...). It lists only the
  keys the user allowed with ``celesto computer ssh-key add`` and only lets
  them sign. Every other agent request (add, remove, lock, unlock,
  extensions) is refused. Unlocking stays on the host.

Guest transport: the filter runs on the host and reaches the guest through
SSH agent forwarding on a dedicated SSH connection to the guest (paramiko,
``auth-agent-req@openssh.com``). The guest's sshd creates the agent socket
for that session; a long-lived command in the session links it to the fixed
path :data:`GUEST_AGENT_SOCKET`. Agent channels the guest opens are served
in-process by :class:`AgentFilter`, so the filter never listens on a host
TCP port (slirp guests can reach host loopback via ``10.0.2.2``) and needs no
host socket at all. This works for every backend that has guest SSH,
including macOS QEMU slirp; a vsock relay can replace it on Linux later.
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import logging
import os
import shlex
import socket
import struct
import threading
import time
from collections.abc import Callable, Collection
from dataclasses import dataclass
from typing import Any, Protocol

from celesto.credentials.types import GuestFile

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Guest side
# ---------------------------------------------------------------------------

GUEST_AGENT_SOCKET = "/run/celesto/ssh-agent.sock"
"""Fixed guest path of the filtered agent socket (a symlink to sshd's socket)."""

GITHUB_HTTPS_BASE = "https://github.com/"
GITHUB_SSH_PREFIXES: tuple[str, ...] = ("git@github.com:", "ssh://git@github.com/")

GUEST_SSH_CONFIG_PATH = "/etc/ssh/ssh_config.d/50-celesto-agent.conf"


def guest_git_config() -> str:
    """Return the gitconfig block that sends GitHub SSH URLs over HTTPS.

    Repos are untouched; git rewrites the URL at use time. Install it into the
    guest's global git config (``/root/.gitconfig``) after any host git config
    has been copied in, e.g. with :func:`guest_setup_script`.
    """
    lines = [f'[url "{GITHUB_HTTPS_BASE}"]']
    lines.extend(f"\tinsteadOf = {prefix}" for prefix in GITHUB_SSH_PREFIXES)
    return "\n".join(lines) + "\n"


def guest_env() -> dict[str, str]:
    """Managed guest env so login shells and ``ssh-add`` find the agent."""
    return {"SSH_AUTH_SOCK": GUEST_AGENT_SOCKET}


def guest_ssh_config() -> str:
    """OpenSSH client config so ``ssh``/``git``/``scp`` find the agent from any exec path.

    Raw exec does not source the login profile, so ``SSH_AUTH_SOCK`` may be
    unset there. The ``Match exec`` keeps a guest user's own
    ``SSH_AUTH_SOCK`` working when it is set.
    """
    return (
        "# Managed by Celesto: use the sandbox's filtered SSH agent.\n"
        'Match exec "test -z $SSH_AUTH_SOCK"\n'
        f"    IdentityAgent {GUEST_AGENT_SOCKET}\n"
    )


def guest_files() -> list[GuestFile]:
    """Static guest files for the filtered agent."""
    return [GuestFile(path=GUEST_SSH_CONFIG_PATH, content=guest_ssh_config().encode(), mode=0o644)]


def guest_setup_script() -> str:
    """Idempotent shell script that installs the guest side of D-13.

    Run it as root after preset host configs are copied (so a copied
    ``~/.gitconfig`` cannot drop the rewrite). It adds the GitHub rewrite to
    the global git config without touching other entries, and writes the
    OpenSSH client config. ``SSH_AUTH_SOCK`` itself goes into the managed env
    (:func:`guest_env`).
    """
    git_cmds = []
    for prefix in GITHUB_SSH_PREFIXES:
        value_regex = "^" + prefix.replace(".", "\\.") + "$"
        git_cmds.append(
            "HOME=/root git config --global --replace-all "
            f"{shlex.quote(f'url.{GITHUB_HTTPS_BASE}.insteadOf')} "
            f"{shlex.quote(prefix)} {shlex.quote(value_regex)}"
        )
    ssh_config = guest_ssh_config()
    return "\n".join(
        [
            "set -e",
            "mkdir -p /run/celesto",
            "chmod 0755 /run/celesto",
            "if command -v git >/dev/null 2>&1; then",
            *(f"  {cmd}" for cmd in git_cmds),
            "fi",
            f"mkdir -p {shlex.quote(os.path.dirname(GUEST_SSH_CONFIG_PATH))}",
            f"cat > {shlex.quote(GUEST_SSH_CONFIG_PATH)} <<'CELESTO_EOF'",
            ssh_config.rstrip("\n"),
            "CELESTO_EOF",
            f"chmod 0644 {shlex.quote(GUEST_SSH_CONFIG_PATH)}",
            "",
        ]
    )


# ---------------------------------------------------------------------------
# Public keys
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PublicKey:
    """One SSH public key, as stored per sandbox (never a private key)."""

    key_type: str
    blob: bytes
    comment: str
    fingerprint: str

    def line(self) -> str:
        """Return the ``authorized_keys``-style line for this key."""
        encoded = base64.b64encode(self.blob).decode("ascii")
        return f"{self.key_type} {encoded} {self.comment}".strip()


def fingerprint(blob: bytes) -> str:
    """Return the OpenSSH ``SHA256:`` fingerprint of a key blob."""
    digest = base64.b64encode(hashlib.sha256(blob).digest()).decode("ascii")
    return "SHA256:" + digest.rstrip("=")


def looks_like_private_key(text: str) -> bool:
    """True when *text* is a private key file rather than a public one."""
    return "PRIVATE KEY" in text


def parse_public_key(text: str) -> PublicKey:
    """Parse the first key in an OpenSSH ``.pub`` file.

    Raises:
        ValueError: If *text* is not an SSH public key.
    """
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 2)
        if len(parts) < 2:
            break
        key_type, encoded = parts[0], parts[1]
        comment = parts[2].strip() if len(parts) > 2 else ""
        try:
            blob = base64.b64decode(encoded, validate=True)
            embedded_type, _rest = _read_string(blob, 0)
        except (ValueError, struct.error) as exc:
            raise ValueError("not an SSH public key") from exc
        if embedded_type.decode("ascii", "replace") != key_type:
            raise ValueError("not an SSH public key")
        return PublicKey(key_type, blob, comment, fingerprint(blob))
    raise ValueError("not an SSH public key")


# ---------------------------------------------------------------------------
# Agent protocol (draft-miller-ssh-agent)
# ---------------------------------------------------------------------------

SSH_AGENT_FAILURE = 5
SSH_AGENTC_REQUEST_IDENTITIES = 11
SSH_AGENT_IDENTITIES_ANSWER = 12
SSH_AGENTC_SIGN_REQUEST = 13
SSH_AGENT_SIGN_RESPONSE = 14

MAX_MESSAGE_BYTES = 256 * 1024
"""Same cap as OpenSSH's agent; larger frames close the connection."""

LIST_TIMEOUT_SECONDS = 10.0
SIGN_TIMEOUT_SECONDS = 120.0
"""Signing may wait for the user to approve on the host (1Password, Touch ID)."""

_FAILURE = bytes([SSH_AGENT_FAILURE])


class _Stream(Protocol):
    def recv(self, n: int) -> bytes: ...
    def sendall(self, data: bytes) -> Any: ...


def _read_string(data: bytes, offset: int) -> tuple[bytes, int]:
    if offset + 4 > len(data):
        raise ValueError("truncated string")
    (length,) = struct.unpack_from(">I", data, offset)
    start = offset + 4
    end = start + length
    if end > len(data):
        raise ValueError("truncated string")
    return data[start:end], end


def _string(data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + data


def _recv_exact(stream: _Stream, n: int) -> bytes | None:
    """Read exactly *n* bytes, or ``None`` on EOF."""
    chunks: list[bytes] = []
    remaining = n
    while remaining:
        chunk = stream.recv(min(remaining, 65536))
        if not chunk:
            return None
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _read_frame(stream: _Stream) -> bytes | None:
    """Read one framed agent message body; ``None`` on EOF or an oversized frame."""
    header = _recv_exact(stream, 4)
    if header is None:
        return None
    (length,) = struct.unpack(">I", header)
    if length > MAX_MESSAGE_BYTES:
        return None
    if length == 0:
        return b""
    return _recv_exact(stream, length)


def _frame(body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + body


class AgentFilter:
    """Serve the SSH agent protocol, exposing only allowed keys of an upstream agent.

    Args:
        upstream: Path of the host agent socket (``SSH_AUTH_SOCK``), or
            ``None`` when the host has no agent.
        allowed: Returns the allowed key fingerprints. Called on every
            request, so allow-list changes apply without a restart.
    """

    def __init__(self, upstream: str | None, allowed: Callable[[], Collection[str]]) -> None:
        self.upstream = upstream
        self._allowed = allowed

    # -- serving -----------------------------------------------------------

    def handle(self, stream: _Stream) -> None:
        """Answer requests on *stream* until it closes. Never raises."""
        try:
            while True:
                body = _read_frame(stream)
                if body is None:
                    return
                stream.sendall(_frame(self.respond(body)))
        except Exception:  # noqa: BLE001 - one bad client must not kill the server
            logger.debug("SSH agent filter connection ended with an error", exc_info=True)

    def respond(self, body: bytes) -> bytes:
        """Return the reply body for one request body."""
        if not body:
            return _FAILURE
        try:
            if body[0] == SSH_AGENTC_REQUEST_IDENTITIES and len(body) == 1:
                return self._identities()
            if body[0] == SSH_AGENTC_SIGN_REQUEST:
                return self._sign(body)
        except Exception:  # noqa: BLE001 - any upstream oddity is a plain failure
            logger.debug("SSH agent filter request failed", exc_info=True)
        return _FAILURE

    # -- requests ----------------------------------------------------------

    def _allowed_set(self) -> set[str]:
        try:
            return set(self._allowed())
        except Exception:  # noqa: BLE001 - unreadable allow list means nothing allowed
            logger.debug("Could not read allowed SSH keys", exc_info=True)
            return set()

    def _upstream_identities(self) -> list[tuple[bytes, bytes]]:
        reply = self._upstream(bytes([SSH_AGENTC_REQUEST_IDENTITIES]), LIST_TIMEOUT_SECONDS)
        if not reply or reply[0] != SSH_AGENT_IDENTITIES_ANSWER or len(reply) < 5:
            return []
        (count,) = struct.unpack_from(">I", reply, 1)
        offset = 5
        keys: list[tuple[bytes, bytes]] = []
        for _ in range(count):
            blob, offset = _read_string(reply, offset)
            comment, offset = _read_string(reply, offset)
            keys.append((blob, comment))
        if offset != len(reply):
            return []
        return keys

    def _identities(self) -> bytes:
        allowed = self._allowed_set()
        keys = (
            [(b, c) for b, c in self._upstream_identities() if fingerprint(b) in allowed]
            if allowed
            else []
        )
        out = [bytes([SSH_AGENT_IDENTITIES_ANSWER]), struct.pack(">I", len(keys))]
        for blob, comment in keys:
            out.append(_string(blob))
            out.append(_string(comment))
        return b"".join(out)

    def _sign(self, body: bytes) -> bytes:
        blob, offset = _read_string(body, 1)
        data, offset = _read_string(body, offset)
        if offset + 4 != len(body):
            return _FAILURE
        (flags,) = struct.unpack_from(">I", body, offset)
        if fingerprint(blob) not in self._allowed_set():
            return _FAILURE
        request = bytes([SSH_AGENTC_SIGN_REQUEST]) + _string(blob) + _string(data)
        reply = self._upstream(request + struct.pack(">I", flags), SIGN_TIMEOUT_SECONDS)
        if not reply or reply[0] != SSH_AGENT_SIGN_RESPONSE:
            return _FAILURE
        signature, end = _read_string(reply, 1)
        if end != len(reply):
            return _FAILURE
        return bytes([SSH_AGENT_SIGN_RESPONSE]) + _string(signature)

    def _upstream(self, body: bytes, timeout: float) -> bytes | None:
        """Send one request to the host agent on a fresh connection."""
        if not self.upstream:
            return None
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
                conn.settimeout(timeout)
                conn.connect(self.upstream)
                conn.sendall(_frame(body))
                return _read_frame(conn)
        except OSError:
            logger.debug("Host SSH agent is not reachable at %s", self.upstream, exc_info=True)
            return None


def host_agent_fingerprints(socket_path: str | None) -> set[str] | None:
    """Fingerprints loaded in the host agent, or ``None`` if it is unreachable."""
    if not socket_path:
        return None
    probe = AgentFilter(socket_path, allowed=lambda: ())
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
            conn.settimeout(LIST_TIMEOUT_SECONDS)
            conn.connect(socket_path)
    except OSError:
        return None
    return {fingerprint(blob) for blob, _comment in probe._upstream_identities()}


# ---------------------------------------------------------------------------
# Serving
# ---------------------------------------------------------------------------


class UnixAgentServer:
    """Serve an :class:`AgentFilter` on a private (0600) Unix socket."""

    def __init__(self, agent_filter: AgentFilter, path: str) -> None:
        self.agent_filter = agent_filter
        self.path = path
        self._sock: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stopped = threading.Event()

    def start(self) -> None:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(self.path)
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        old_umask = os.umask(0o177)
        try:
            sock.bind(self.path)
        finally:
            os.umask(old_umask)
        os.chmod(self.path, 0o600)
        sock.listen(16)
        self._sock = sock
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()

    def _accept_loop(self) -> None:
        assert self._sock is not None
        while not self._stopped.is_set():
            try:
                conn, _ = self._sock.accept()
            except OSError:
                return
            threading.Thread(target=self._serve_one, args=(conn,), daemon=True).start()

    def _serve_one(self, conn: socket.socket) -> None:
        with conn:
            self.agent_filter.handle(conn)

    def stop(self) -> None:
        self._stopped.set()
        if self._sock is not None:
            with contextlib.suppress(OSError):
                self._sock.shutdown(socket.SHUT_RDWR)
            self._sock.close()
            self._sock = None
        with contextlib.suppress(FileNotFoundError):
            os.unlink(self.path)


def _link_command(guest_socket: str) -> str:
    """Guest command that links sshd's agent socket to *guest_socket* and stays alive."""
    target = shlex.quote(guest_socket)
    directory = shlex.quote(os.path.dirname(guest_socket))
    tmp = shlex.quote(f"{guest_socket}.$$")
    # $SSH_AUTH_SOCK is set by sshd because agent forwarding was requested.
    return (
        f'[ -n "$SSH_AUTH_SOCK" ] || exit 3; '
        f"mkdir -p {directory} && chmod 0755 {directory} && "
        f'ln -sfn "$SSH_AUTH_SOCK" {tmp} && mv -fT {tmp} {target} && '
        "echo celesto-agent-ready && exec sleep 2147483647"
    )


class GuestAgentForward:
    """Keep the filtered agent reachable at a fixed guest socket path.

    Opens its own SSH connection to the guest, requests agent forwarding,
    and runs a long-lived command that links sshd's per-session agent socket
    to *guest_socket*. Reconnects with backoff until stopped or ``alive``
    returns False.

    Args:
        agent_filter: Filter that answers the guest's agent requests.
        connect: Returns a connected ``celesto.ssh.SSHClient`` (or anything
            with ``_ensure_connected()`` and ``close()``).
        guest_socket: Fixed guest path for the agent socket.
        alive: Returns False once the VM is gone.
    """

    def __init__(
        self,
        agent_filter: AgentFilter,
        connect: Callable[[], Any],
        *,
        guest_socket: str = GUEST_AGENT_SOCKET,
        alive: Callable[[], bool] = lambda: True,
    ) -> None:
        self.agent_filter = agent_filter
        self._connect = connect
        self.guest_socket = guest_socket
        self._alive = alive
        self._stopped = threading.Event()
        self.ready = threading.Event()
        self._thread: threading.Thread | None = None
        self._client: Any = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True, name="celesto-ssh-agent")
        self._thread.start()

    def stop(self) -> None:
        self._stopped.set()
        client = self._client
        if client is not None:
            with contextlib.suppress(Exception):
                client.close()

    def _on_agent_channel(self, channel: Any) -> None:
        def serve() -> None:
            try:
                self.agent_filter.handle(channel)
            finally:
                with contextlib.suppress(Exception):
                    channel.close()

        threading.Thread(target=serve, daemon=True).start()

    def _run(self) -> None:
        delay = 0.5
        while not self._stopped.is_set() and self._alive():
            try:
                self._run_once()
                delay = 0.5
            except Exception:  # noqa: BLE001 - guest not up yet, or the link dropped
                logger.debug("SSH agent forward to the guest failed", exc_info=True)
            finally:
                self.ready.clear()
                client, self._client = self._client, None
                if client is not None:
                    with contextlib.suppress(Exception):
                        client.close()
            if self._stopped.wait(delay):
                return
            delay = min(delay * 2, 10.0)

    def _run_once(self) -> None:
        client = self._connect()
        self._client = client
        paramiko_client = client._ensure_connected()
        transport = paramiko_client.get_transport()
        transport.set_keepalive(15)
        channel = transport.open_session()
        channel.request_forward_agent(self._on_agent_channel)
        channel.exec_command(_link_command(self.guest_socket))
        buffer = b""
        while not self._stopped.is_set() and self._alive():
            if channel.recv_ready():
                buffer += channel.recv(1024)
                if b"celesto-agent-ready" in buffer:
                    self.ready.set()
                    buffer = b""
            if channel.exit_status_ready() or not transport.is_active():
                return
            time.sleep(0.2)


@dataclass
class SshAgentService:
    """Handle for a running filtered agent; :meth:`stop` tears it down."""

    agent_filter: AgentFilter
    forward: GuestAgentForward

    def stop(self) -> None:
        self.forward.stop()


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _state_allowed(sandbox_id: str, data_dir: str | None) -> Callable[[], set[str]]:
    from pathlib import Path

    from celesto.cli.service import CLIService

    service = CLIService(Path(data_dir) if data_dir else None)
    state = service.state_manager()

    def allowed() -> set[str]:
        return {fp for fp, _line in state.list_ssh_keys(sandbox_id)}

    return allowed


def _guest_from_state(sandbox_id: str, data_dir: str | None) -> dict[str, Any]:
    from pathlib import Path

    from celesto.cli.service import CLIService
    from celesto.utils import ensure_ssh_key

    state = CLIService(Path(data_dir) if data_dir else None).state_manager()
    info = state.get_vm(sandbox_id)
    network = info.network
    if network is not None and network.ssh_host_port:
        host, port = "127.0.0.1", int(network.ssh_host_port)
    elif network is not None and network.guest_ip:
        host, port = network.guest_ip, 22
    else:
        raise ValueError(f"{sandbox_id} has no SSH address")
    key_path, _pub = ensure_ssh_key()
    return {"host": host, "port": port, "user": "root", "key_path": str(key_path)}


def serve(spec: dict[str, Any]) -> SshAgentService:
    """Start the filtered SSH agent for one sandbox (called by the per-VM launcher).

    Reads from *spec* (the launcher's LaunchSpec):

    - ``sandbox_id`` (required) and ``vm_pid`` (stop when it exits).
    - ``ssh`` (optional dict):
      - ``host_agent_socket``: host ``SSH_AUTH_SOCK``; defaults to this
        process's ``SSH_AUTH_SOCK``. ``None``/missing agent means the guest
        sees an empty agent.
      - ``allowed_fingerprints``: fixed allow list; by default it is re-read
        from the CLI state on every request, so ``ssh-key add/remove``
        apply to a running sandbox.
      - ``guest``: ``{"host", "port", "user", "key_path"}``; defaults to the
        sandbox's SSH address in the CLI state and Celesto's default key.
      - ``data_dir``: CLI data dir override.

    Returns immediately; the forward runs on a daemon thread and reconnects
    until the VM exits or :meth:`SshAgentService.stop` is called.
    """
    from celesto.ssh import SSHClient

    sandbox_id = str(spec["sandbox_id"])
    options: dict[str, Any] = dict(spec.get("ssh") or {})
    data_dir = options.get("data_dir")
    upstream = options.get("host_agent_socket", os.environ.get("SSH_AUTH_SOCK")) or None

    allowed: Callable[[], Collection[str]]
    if options.get("allowed_fingerprints") is not None:
        fixed = frozenset(str(fp) for fp in options["allowed_fingerprints"])
        allowed = lambda: fixed  # noqa: E731
    else:
        allowed = _state_allowed(sandbox_id, data_dir)

    guest = options.get("guest") or _guest_from_state(sandbox_id, data_dir)

    def connect() -> SSHClient:
        return SSHClient(
            host=str(guest["host"]),
            port=int(guest["port"]),
            user=str(guest.get("user", "root")),
            key_path=guest.get("key_path"),
        )

    vm_pid = spec.get("vm_pid")
    alive: Callable[[], bool] = (lambda: _pid_alive(int(vm_pid))) if vm_pid else (lambda: True)

    agent_filter = AgentFilter(upstream, allowed)
    forward = GuestAgentForward(agent_filter, connect, alive=alive)
    forward.start()
    return SshAgentService(agent_filter, forward)


__all__ = [
    "GITHUB_HTTPS_BASE",
    "GITHUB_SSH_PREFIXES",
    "GUEST_AGENT_SOCKET",
    "AgentFilter",
    "GuestAgentForward",
    "PublicKey",
    "SshAgentService",
    "UnixAgentServer",
    "fingerprint",
    "guest_env",
    "guest_files",
    "guest_git_config",
    "guest_setup_script",
    "host_agent_fingerprints",
    "looks_like_private_key",
    "parse_public_key",
    "serve",
]

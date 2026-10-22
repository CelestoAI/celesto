# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""A throwaway ssh-agent with throwaway keys; never touches the user's agent."""

from __future__ import annotations

import contextlib
import os
import shutil
import socket
import struct
import subprocess
import tempfile
import threading
from collections.abc import Iterator
from pathlib import Path

import pytest

from celesto.credentials import ssh as cssh

SSH_AGENT_FAILURE = 5
SSH_AGENTC_REQUEST_IDENTITIES = 11
SSH_AGENT_IDENTITIES_ANSWER = 12
SSH_AGENTC_SIGN_REQUEST = 13
SSH_AGENT_SIGN_RESPONSE = 14


def _clean_env(**extra: str) -> dict[str, str]:
    """Env for OpenSSH tools that can never reach the user's agent or keys."""
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": extra.pop("HOME"),
    }
    env.update(extra)
    return env


class Lab:
    """A throwaway ssh-agent with two keys and a filter in front of it."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.home = root / "home"
        self.home.mkdir()
        self.agent_sock = root / "agent.sock"
        self.filter_sock = root / "filter.sock"
        self.allowed_key = root / "allowed"
        self.other_key = root / "other"
        for key, comment in ((self.allowed_key, "w6-allowed"), (self.other_key, "w6-other")):
            subprocess.run(
                ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", comment, "-f", str(key)],
                check=True,
                env=_clean_env(HOME=str(self.home)),
            )
        self.agent = subprocess.Popen(
            ["ssh-agent", "-D", "-a", str(self.agent_sock)],
            env=_clean_env(HOME=str(self.home)),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(200):
            if self.agent_sock.exists():
                break
            threading.Event().wait(0.02)
        for key in (self.allowed_key, self.other_key):
            self.agent_cmd(["ssh-add", str(key)], sock=self.agent_sock, check=True)
        self.allowed_fp = cssh.parse_public_key(self.pub(self.allowed_key)).fingerprint
        self.other_fp = cssh.parse_public_key(self.pub(self.other_key)).fingerprint
        self.allowed: set[str] = {self.allowed_fp}
        self.server: cssh.UnixAgentServer | None = None

    def pub(self, key: Path) -> str:
        return Path(f"{key}.pub").read_text()

    def start_filter(self, upstream: Path | None = None, *, use_upstream: bool = True) -> None:
        agent_filter = cssh.AgentFilter(
            upstream=str(upstream or self.agent_sock) if use_upstream else None,
            allowed=lambda: set(self.allowed),
        )
        self.server = cssh.UnixAgentServer(agent_filter, str(self.filter_sock))
        self.server.start()

    def agent_cmd(
        self, argv: list[str], *, sock: Path | None = None, check: bool = False, input: str = ""
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            argv,
            env=_clean_env(HOME=str(self.home), SSH_AUTH_SOCK=str(sock or self.filter_sock)),
            capture_output=True,
            text=True,
            input=input,
            check=check,
            timeout=20,
        )

    def fingerprints(self, sock: Path) -> str:
        return self.agent_cmd(["ssh-add", "-l"], sock=sock).stdout

    def sign(self, key: Path, sock: Path) -> subprocess.CompletedProcess[str]:
        data = self.root / "data.txt"
        data.write_text("hello from w6\n")
        sig = Path(f"{data}.sig")
        sig.unlink(missing_ok=True)
        # Only the public key is given, so ssh-keygen must sign via the agent.
        pub_only = self.root / f"{key.name}-only.pub"
        pub_only.write_text(self.pub(key))
        return self.agent_cmd(
            ["ssh-keygen", "-Y", "sign", "-n", "file", "-f", str(pub_only), str(data)], sock=sock
        )

    def raw(self, payload: bytes) -> bytes:
        """Send one framed message to the filter and return the framed reply body."""
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
            conn.settimeout(5)
            conn.connect(str(self.filter_sock))
            conn.sendall(struct.pack(">I", len(payload)) + payload)
            return _read_reply(conn)

    def close(self) -> None:
        if self.server is not None:
            self.server.stop()
        self.agent.terminate()
        self.agent.wait(timeout=5)


def _read_exact(conn: socket.socket, n: int) -> bytes:
    data = b""
    while len(data) < n:
        chunk = conn.recv(n - len(data))
        if not chunk:
            raise EOFError
        data += chunk
    return data


def _read_reply(conn: socket.socket) -> bytes:
    (length,) = struct.unpack(">I", _read_exact(conn, 4))
    return _read_exact(conn, length)


def _string(data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + data


@contextlib.contextmanager
def make_lab() -> Iterator[Lab]:
    """Start a throwaway agent; Unix socket paths stay short (~104 bytes on macOS)."""
    root = Path(tempfile.mkdtemp(prefix="w6a-", dir="/tmp"))
    lab = Lab(root)
    try:
        yield lab
    finally:
        lab.close()
        shutil.rmtree(root, ignore_errors=True)


@pytest.fixture
def lab() -> Iterator[Lab]:
    with make_lab() as started:
        yield started

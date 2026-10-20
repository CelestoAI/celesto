# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""Isolated tests for the filtered SSH agent (D-13).

The filter is security-critical and sits between a sandbox and the user's
real SSH agent. The VM E2E test shows the happy path; these tests run the
filter against a real ``ssh-agent`` (started in a temp dir with throwaway
keys, never the user's agent) and real OpenSSH clients.

Failure modes, written before the implementation:

1. Lists a key the user did not allow (identities answer not filtered).
2. Signs with a key the user did not allow (sign request forwarded blindly).
3. Accepts add / add-constrained / remove / remove-all / lock / unlock /
   smartcard / extension requests, letting a guest change or lock the host
   agent, or probe it via vendor extensions.
4. Leaks private key material or unrelated host data (raw upstream bytes
   relayed instead of a re-built answer; extension replies passed through).
5. Breaks when the host agent is absent, unreachable, or dies mid-session
   (crash, hang, or exception that kills the listener).
6. Message framing bugs: oversized length prefix buffered without limit,
   truncated messages, zero-length messages, several requests in one
   write, one request split across many writes, trailing bytes smuggled
   inside a sign request.
7. Allowed-key changes need a restart (allow list cached forever).
8. A key that is allowed but not loaded in the host agent is listed anyway.
"""

from __future__ import annotations

import shutil
import socket
import struct
import subprocess

import pytest

from celesto.credentials import ssh as cssh
from tests.credentials._agent_lab import (
    SSH_AGENT_FAILURE,
    SSH_AGENT_IDENTITIES_ANSWER,
    SSH_AGENT_SIGN_RESPONSE,
    SSH_AGENTC_REQUEST_IDENTITIES,
    SSH_AGENTC_SIGN_REQUEST,
    Lab,
    _clean_env,
    _read_reply,
    _string,
)

pytestmark = pytest.mark.skipif(
    shutil.which("ssh-agent") is None or shutil.which("ssh-keygen") is None,
    reason="OpenSSH client tools are required",
)


def test_lists_only_allowed_keys(lab: Lab) -> None:
    lab.start_filter()
    listed = lab.fingerprints(lab.filter_sock)
    assert lab.allowed_fp in listed
    assert "w6-allowed" in listed
    assert lab.other_fp not in listed
    # Sanity: the real agent holds both.
    assert lab.other_fp in lab.fingerprints(lab.agent_sock)

    public = lab.agent_cmd(["ssh-add", "-L"]).stdout
    assert lab.pub(lab.allowed_key).split()[1] in public
    assert lab.pub(lab.other_key).split()[1] not in public


def test_signs_with_allowed_key_only(lab: Lab) -> None:
    lab.start_filter()
    ok = lab.sign(lab.allowed_key, lab.filter_sock)
    assert ok.returncode == 0, ok.stderr
    refused = lab.sign(lab.other_key, lab.filter_sock)
    assert refused.returncode != 0
    # Sanity: the real agent can sign with the other key.
    assert lab.sign(lab.other_key, lab.agent_sock).returncode == 0


def test_raw_sign_with_unlisted_key_fails(lab: Lab) -> None:
    lab.start_filter()
    blob = cssh.parse_public_key(lab.pub(lab.other_key)).blob
    reply = lab.raw(bytes([SSH_AGENTC_SIGN_REQUEST]) + _string(blob) + _string(b"x") + b"\0\0\0\0")
    assert reply == bytes([SSH_AGENT_FAILURE])


def test_sign_request_with_trailing_bytes_fails(lab: Lab) -> None:
    lab.start_filter()
    blob = cssh.parse_public_key(lab.pub(lab.allowed_key)).blob
    good = bytes([SSH_AGENTC_SIGN_REQUEST]) + _string(blob) + _string(b"x") + b"\0\0\0\0"
    assert lab.raw(good)[0] == SSH_AGENT_SIGN_RESPONSE
    assert lab.raw(good + b"junk") == bytes([SSH_AGENT_FAILURE])


def test_refuses_agent_changes(lab: Lab) -> None:
    lab.start_filter()
    extra = lab.root / "extra"
    subprocess.run(
        ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "w6-extra", "-f", str(extra)],
        check=True,
        env=_clean_env(HOME=str(lab.home)),
    )
    assert lab.agent_cmd(["ssh-add", str(extra)]).returncode != 0
    assert lab.agent_cmd(["ssh-add", "-d", f"{lab.allowed_key}.pub"]).returncode != 0
    assert lab.agent_cmd(["ssh-add", "-D"]).returncode != 0

    real = lab.fingerprints(lab.agent_sock)
    assert lab.allowed_fp in real
    assert lab.other_fp in real
    assert "w6-extra" not in real


@pytest.mark.parametrize(
    "message_type",
    [
        17,  # ADD_IDENTITY
        18,  # REMOVE_IDENTITY
        19,  # REMOVE_ALL_IDENTITIES
        20,  # ADD_SMARTCARD_KEY
        21,  # REMOVE_SMARTCARD_KEY
        22,  # LOCK
        23,  # UNLOCK
        25,  # ADD_ID_CONSTRAINED
        26,  # ADD_SMARTCARD_KEY_CONSTRAINED
        27,  # EXTENSION
        1,  # SSH1 request identities (obsolete)
        9,  # SSH1 remove all (obsolete)
        200,  # unknown
    ],
)
def test_refuses_every_other_request(lab: Lab, message_type: int) -> None:
    lab.start_filter()
    body = _string(b"query") if message_type == 27 else _string(b"password")
    assert lab.raw(bytes([message_type]) + body) == bytes([SSH_AGENT_FAILURE])
    # The real agent is not locked and still lists both keys.
    real = lab.fingerprints(lab.agent_sock)
    assert lab.allowed_fp in real and lab.other_fp in real


def test_lock_through_ssh_add_is_refused(lab: Lab) -> None:
    lab.start_filter()
    # ssh-add -x reads the lock password from the terminal or askpass.
    askpass = lab.root / "askpass.sh"
    askpass.write_text("#!/bin/sh\necho w6-lock\n")
    askpass.chmod(0o700)
    result = subprocess.run(
        ["ssh-add", "-x"],
        env=_clean_env(
            HOME=str(lab.home),
            SSH_AUTH_SOCK=str(lab.filter_sock),
            SSH_ASKPASS=str(askpass),
            SSH_ASKPASS_REQUIRE="force",
            DISPLAY=":0",
        ),
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        timeout=20,
        start_new_session=True,
    )
    assert result.returncode != 0
    assert lab.sign(lab.allowed_key, lab.agent_sock).returncode == 0


def test_identities_answer_is_rebuilt_not_relayed(lab: Lab) -> None:
    lab.start_filter()
    reply = lab.raw(bytes([SSH_AGENTC_REQUEST_IDENTITIES]))
    allowed = cssh.parse_public_key(lab.pub(lab.allowed_key))
    assert reply == (
        bytes([SSH_AGENT_IDENTITIES_ANSWER])
        + struct.pack(">I", 1)
        + _string(allowed.blob)
        + _string(b"w6-allowed")
    )


def test_no_host_agent(lab: Lab) -> None:
    lab.start_filter(use_upstream=False)
    listed = lab.agent_cmd(["ssh-add", "-l"])
    assert "no identities" in listed.stdout.lower()
    assert lab.sign(lab.allowed_key, lab.filter_sock).returncode != 0


def test_host_agent_socket_missing_or_dead(lab: Lab) -> None:
    lab.start_filter(upstream=lab.root / "missing.sock")
    assert "no identities" in lab.agent_cmd(["ssh-add", "-l"]).stdout.lower()

    lab.server.stop()  # type: ignore[union-attr]
    lab.start_filter()
    assert lab.allowed_fp in lab.fingerprints(lab.filter_sock)
    lab.agent.terminate()
    lab.agent.wait(timeout=5)
    assert "no identities" in lab.agent_cmd(["ssh-add", "-l"]).stdout.lower()
    assert lab.sign(lab.allowed_key, lab.filter_sock).returncode != 0


def test_oversized_and_truncated_messages_do_not_break_the_listener(lab: Lab) -> None:
    lab.start_filter()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
        conn.settimeout(5)
        conn.connect(str(lab.filter_sock))
        conn.sendall(struct.pack(">I", 64 * 1024 * 1024) + b"\x0b")
        assert conn.recv(16) == b""  # closed, not buffered
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
        conn.connect(str(lab.filter_sock))
        conn.sendall(struct.pack(">I", 50) + b"\x0d\x00")  # truncated, then hang up
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
        conn.settimeout(5)
        conn.connect(str(lab.filter_sock))
        conn.sendall(struct.pack(">I", 0))
        assert _read_reply(conn) == bytes([SSH_AGENT_FAILURE])
    assert lab.allowed_fp in lab.fingerprints(lab.filter_sock)


def test_pipelined_and_split_requests(lab: Lab) -> None:
    lab.start_filter()
    request = struct.pack(">I", 1) + bytes([SSH_AGENTC_REQUEST_IDENTITIES])
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as conn:
        conn.settimeout(5)
        conn.connect(str(lab.filter_sock))
        conn.sendall(request * 3)
        replies = [_read_reply(conn) for _ in range(3)]
        assert all(r[0] == SSH_AGENT_IDENTITIES_ANSWER for r in replies)
        for byte in request:
            conn.sendall(bytes([byte]))
        assert _read_reply(conn)[0] == SSH_AGENT_IDENTITIES_ANSWER


def test_allow_list_changes_apply_without_restart(lab: Lab) -> None:
    lab.allowed = set()
    lab.start_filter()
    assert "no identities" in lab.agent_cmd(["ssh-add", "-l"]).stdout.lower()
    lab.allowed = {lab.other_fp}
    listed = lab.fingerprints(lab.filter_sock)
    assert lab.other_fp in listed and lab.allowed_fp not in listed


def test_allowed_key_not_in_host_agent_is_not_listed(lab: Lab) -> None:
    lab.agent_cmd(["ssh-add", "-d", f"{lab.allowed_key}.pub"], sock=lab.agent_sock, check=True)
    lab.start_filter()
    assert "no identities" in lab.agent_cmd(["ssh-add", "-l"]).stdout.lower()
    assert lab.sign(lab.allowed_key, lab.filter_sock).returncode != 0


def test_filter_socket_is_private(lab: Lab) -> None:
    lab.start_filter()
    assert (lab.filter_sock.stat().st_mode & 0o777) == 0o600

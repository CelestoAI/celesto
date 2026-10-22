# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""End-to-end tests for ``celesto computer ssh-key add|remove|list`` (D-13).

Runs the real CLI in a subprocess against a temp data dir and a throwaway
ssh-agent. The sandbox is a stopped inventory record: allowing a key only
changes host state, so no VM is needed.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from celesto.cli._sqlite import SQLiteStateManager
from celesto.credentials import ssh as cssh
from celesto.types import VMConfig
from tests.credentials._agent_lab import Lab

pytestmark = pytest.mark.skipif(
    shutil.which("ssh-agent") is None or shutil.which("ssh-keygen") is None,
    reason="OpenSSH client tools are required",
)

SBX = "w6-cli"


@pytest.fixture
def data_dir(lab: Lab) -> Path:
    data = lab.root / "data"
    data.mkdir()
    kernel = lab.root / "vmlinux"
    rootfs = lab.root / "rootfs.ext4"
    kernel.touch()
    rootfs.touch()
    SQLiteStateManager(data / "celesto.db").create_vm(
        VMConfig(vm_id=SBX, kernel_path=kernel, rootfs_path=rootfs)
    )
    return data


def run_cli(lab: Lab, data_dir: Path, *argv: str, agent: Path | None | str = "default") -> dict:
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(lab.home),
        "CELESTO_DATA_DIR": str(data_dir),
        "CELESTO_DISABLE_VERSION_CHECK": "1",
        "CELESTO_NO_TELEMETRY": "1",
    }
    if agent == "default":
        env["SSH_AUTH_SOCK"] = str(lab.agent_sock)
    elif agent is not None:
        env["SSH_AUTH_SOCK"] = str(agent)
    result = subprocess.run(
        [sys.executable, "-c", "from celesto.cli.main import main; raise SystemExit(main())"]
        + list(argv)
        + ["--json"],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    payload = json.loads(result.stdout)
    payload["_exit"] = result.returncode
    return payload


def test_add_list_remove(lab: Lab, data_dir: Path) -> None:
    pub = f"{lab.allowed_key}.pub"
    empty = run_cli(lab, data_dir, "computer", "ssh-key", "list", SBX)
    assert empty["ok"] and empty["data"]["keys"] == []

    added = run_cli(lab, data_dir, "computer", "ssh-key", "add", SBX, pub)
    assert added["ok"], added
    assert added["data"]["fingerprint"] == lab.allowed_fp
    assert added["data"]["added"] is True

    again = run_cli(lab, data_dir, "sandbox", "ssh-key", "add", SBX, pub)
    assert again["ok"] and again["data"]["added"] is False

    listed = run_cli(lab, data_dir, "computer", "ssh-key", "list", SBX)
    assert [k["fingerprint"] for k in listed["data"]["keys"]] == [lab.allowed_fp]
    assert listed["data"]["keys"][0]["comment"] == "w6-allowed"

    # The state the CLI wrote is what a running sandbox's filter reads.
    allowed = cssh._state_allowed(SBX, str(data_dir))
    agent_filter = cssh.AgentFilter(str(lab.agent_sock), allowed)
    reply = agent_filter.respond(bytes([cssh.SSH_AGENTC_REQUEST_IDENTITIES]))
    assert b"w6-allowed" in reply
    assert b"w6-other" not in reply

    removed = run_cli(lab, data_dir, "computer", "ssh-key", "remove", SBX, pub)
    assert removed["ok"] and removed["data"]["removed"] is True
    assert run_cli(lab, data_dir, "computer", "ssh-key", "list", SBX)["data"]["keys"] == []
    reply = agent_filter.respond(bytes([cssh.SSH_AGENTC_REQUEST_IDENTITIES]))
    assert b"w6-allowed" not in reply


def test_remove_by_fingerprint(lab: Lab, data_dir: Path) -> None:
    run_cli(lab, data_dir, "computer", "ssh-key", "add", SBX, f"{lab.allowed_key}.pub")
    removed = run_cli(lab, data_dir, "computer", "ssh-key", "remove", SBX, lab.allowed_fp)
    assert removed["ok"] and removed["data"]["removed"] is True
    missing = run_cli(lab, data_dir, "computer", "ssh-key", "remove", SBX, lab.allowed_fp)
    assert missing["ok"] and missing["data"]["removed"] is False


def test_key_not_loaded_in_agent(lab: Lab, data_dir: Path) -> None:
    lab.agent_cmd(["ssh-add", "-d", f"{lab.allowed_key}.pub"], sock=lab.agent_sock, check=True)
    pub = f"{lab.allowed_key}.pub"
    result = run_cli(lab, data_dir, "computer", "ssh-key", "add", SBX, pub)
    assert not result["ok"] and result["_exit"] == 1
    assert f"ssh-add {lab.allowed_key}" in result["error"]["message"]
    assert f"celesto computer ssh-key add {SBX} {pub}" in result["error"]["message"]
    assert run_cli(lab, data_dir, "computer", "ssh-key", "list", SBX)["data"]["keys"] == []


def test_no_agent_running(lab: Lab, data_dir: Path) -> None:
    pub = f"{lab.allowed_key}.pub"
    result = run_cli(lab, data_dir, "computer", "ssh-key", "add", SBX, pub, agent=None)
    assert not result["ok"]
    message = result["error"]["message"]
    assert "ssh-agent" in message and f"ssh-add {lab.allowed_key}" in message
    dead = run_cli(
        lab, data_dir, "computer", "ssh-key", "add", SBX, pub, agent=lab.root / "nope.sock"
    )
    assert not dead["ok"]


def test_private_key_is_refused_and_not_stored(lab: Lab, data_dir: Path) -> None:
    result = run_cli(lab, data_dir, "computer", "ssh-key", "add", SBX, str(lab.allowed_key))
    assert not result["ok"]
    assert f"celesto computer ssh-key add {SBX} {lab.allowed_key}.pub" in result["error"]["message"]
    db = (data_dir / "celesto.db").read_bytes()
    private_body = "".join(lab.allowed_key.read_text().splitlines()[1:-1])
    assert private_body[:40].encode() not in db


def test_bad_inputs(lab: Lab, data_dir: Path) -> None:
    missing = run_cli(lab, data_dir, "computer", "ssh-key", "add", SBX, str(lab.root / "x.pub"))
    assert not missing["ok"] and str(lab.root / "x.pub") in missing["error"]["message"]

    junk = lab.root / "junk.pub"
    junk.write_text("hello\n")
    bad = run_cli(lab, data_dir, "computer", "ssh-key", "add", SBX, str(junk))
    assert not bad["ok"] and "isn't an SSH public key" in bad["error"]["message"]

    nobody = run_cli(
        lab, data_dir, "computer", "ssh-key", "add", "w6-nobody", f"{lab.allowed_key}.pub"
    )
    assert not nobody["ok"] and "celesto computer list --all" in nobody["error"]["message"]
    assert not run_cli(lab, data_dir, "computer", "ssh-key", "list", "w6-nobody")["ok"]

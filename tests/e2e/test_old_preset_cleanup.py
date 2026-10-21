# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""One-time cleanup of keys the old presets copied into a computer (D-21).

Boots a real QEMU computer through the CLI, plants what an old preset left
behind (sentinel values only), then makes its stored record look like a
computer from the previous release: ``preset`` set and credential-protection
version 0. The next ``celesto computer start`` must delete exactly the fixed
list of copied keys, keep everything else, and print the one-time message
once; a second restart must print nothing.

Opt in: ``CELESTO_E2E_CREDENTIALS=1 uv run --extra dev pytest -m e2e
tests/e2e/test_old_preset_cleanup.py``. Writes
``credential-cleanup/e2e-summary.json`` under ``$CELESTO_TEST_ARTIFACTS``
(default ``artifacts/``); no sentinel value is written to it.
"""

from __future__ import annotations

import json
import os
import shlex
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import pytest

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        os.environ.get("CELESTO_E2E_CREDENTIALS") != "1",
        reason="Set CELESTO_E2E_CREDENTIALS=1 to boot a real computer.",
    ),
]

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT = (
    Path(os.environ.get("CELESTO_TEST_ARTIFACTS") or ROOT / "artifacts")
    / "credential-cleanup"
    / "e2e-summary.json"
)
CELESTO = str(Path(sys.executable).with_name("celesto"))
SENTINEL = "sk-SENTINEL-d21cleanup-" + uuid.uuid4().hex

# What an old preset wrote: removed on the first start after upgrade.
COPIED_ENV = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "HF_TOKEN", "AWS_SECRET_ACCESS_KEY")
COPIED_FILES = (
    "/root/.codex/auth.json",
    "/root/.claude/.credentials.json",
    "/root/.local/share/opencode/auth.json",
    "/root/.pi/agent/auth.json",
    "/root/.hermes/.env",
    "/root/.git-credentials",
    "/root/.config/gh/hosts.yml",
    "/root/.ssh/id_ed25519",
    "/root/.ssh/work_key",
)
# Not on the list: must survive.
KEPT_ENV = {"MY_APP_MODE": "fast"}
KEPT_FILES = (
    "/root/.ssh/id_ed25519.pub",
    "/root/.ssh/known_hosts",
    "/root/.ssh/config",
    "/root/.codex/config.toml",
    "/root/notes/auth.json",
)
PRIVATE_KEY = (
    "-----BEGIN OPENSSH PRIVATE KEY-----\\n" + SENTINEL + "\\n-----END OPENSSH PRIVATE KEY-----\\n"
)


def _message(name: str) -> str:
    return (
        f"Celesto removed copied keys from {name}. If an agent may have copied them"
        " elsewhere in the computer, rotate them or recreate the computer."
    )


def _cli(env: dict[str, str], *args: str, json_out: bool = True) -> tuple[int, Any, str]:
    argv = [CELESTO, *args, *(["--json"] if json_out else [])]
    proc = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=600)
    assert SENTINEL not in proc.stdout and SENTINEL not in proc.stderr
    payload: Any = proc.stdout
    if json_out and proc.stdout.strip().startswith("{"):
        payload = json.loads(proc.stdout)
    return proc.returncode, payload, proc.stdout + proc.stderr


def _make_old_preset_record(data_dir: Path, name: str) -> None:
    """Rewrite the stored record the way the previous release left it."""
    (db,) = [p for p in data_dir.glob("*.db") if p.is_file()]
    with sqlite3.connect(db) as conn:
        row = conn.execute("SELECT config FROM vms WHERE id = ?", (name,)).fetchone()
        config = json.loads(row[0])
        config["preset"] = "codex"
        conn.execute(
            "UPDATE vms SET config = ?, credential_protection = 0 WHERE id = ?",
            (json.dumps(config), name),
        )


def _plant(vm: Any) -> None:
    lines = ["set -e"]
    for path in (*COPIED_FILES, *KEPT_FILES):
        lines.append(f"mkdir -p {os.path.dirname(path)}")
    for path in COPIED_FILES:
        body = PRIVATE_KEY if "/.ssh/" in path else SENTINEL + "\\n"
        lines.append(f"printf '%b' '{body}' > {path}")
    for path in KEPT_FILES:
        lines.append(f"printf '%b' 'keep-me\\n' > {path}")
    result = vm.run("bash -c " + shlex.quote("; ".join(lines)), timeout=60, shell="raw")
    assert result.ok, result.stderr
    # The old presets wrote real keys into the managed env file directly.
    vm._set_env_vars_unchecked({**dict.fromkeys(COPIED_ENV, SENTINEL), **KEPT_ENV})
    # A stop may not flush the guest page cache; the old files were on disk.
    assert vm.run("sync", timeout=60, shell="raw").ok


def _guest_state(vm: Any) -> dict[str, Any]:
    paths = " ".join((*COPIED_FILES, *KEPT_FILES))
    listing = vm.run(
        f"for f in {paths}; do [ -e $f ] && echo $f; done; true", timeout=60, shell="raw"
    ).stdout.split()
    hits = vm.run(
        f"grep -rlF {SENTINEL} /root /etc/profile.d 2>/dev/null; true", timeout=60, shell="raw"
    ).stdout.split()
    return {
        "present": sorted(listing),
        "env_names": sorted(vm.list_env_vars()),
        "sentinel_hits": sorted(hits),
    }


def test_old_preset_computer_loses_copied_keys_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from celesto.cli.service import CLIService

    data_dir = tmp_path / "data"
    home = tmp_path / "home"
    home.mkdir()
    image_dir = os.environ.get("CELESTO_IMAGE_DIR") or str(Path.home() / ".celesto" / "images")
    env = {
        **os.environ,
        "HOME": str(home),
        "CELESTO_DATA_DIR": str(data_dir),
        "CELESTO_IMAGE_DIR": image_dir,
        "CELESTO_TELEMETRY": "0",
    }
    for name in COPIED_ENV:
        env.pop(name, None)
    # The in-process SDK must find the same keys the CLI made under HOME.
    for key in ("HOME", "CELESTO_DATA_DIR", "CELESTO_IMAGE_DIR", "CELESTO_TELEMETRY"):
        monkeypatch.setenv(key, env[key])
    name = f"d21-clean-{uuid.uuid4().hex[:6]}"
    summary: dict[str, Any] = {"computer": name, "checks": {}}
    checks = summary["checks"]
    vm = None
    try:
        code, payload, raw = _cli(env, "computer", "create", "--name", name)
        assert code == 0, raw
        vm = CLIService(data_dir).vm_from_id(name, data_dir=data_dir)
        _plant(vm)
        before = _guest_state(vm)
        assert set(before["present"]) == {*COPIED_FILES, *KEPT_FILES}
        assert set(COPIED_ENV) <= set(before["env_names"])
        checks["planted"] = before
        vm.close()
        vm = None

        assert _cli(env, "computer", "stop", name)[0] == 0
        _make_old_preset_record(data_dir, name)
        code, payload, raw = _cli(env, "computer", "start", name)
        assert code == 0, raw
        message = _message(name)
        assert payload["data"].get("warnings", []).count(message) == 1, raw
        checks["message_on_first_start"] = message

        vm = CLIService(data_dir).vm_from_id(name, data_dir=data_dir)
        after = _guest_state(vm)
        checks["after_first_start"] = after
        assert after["present"] == sorted(KEPT_FILES)
        assert not set(COPIED_ENV) & set(after["env_names"])
        assert set(KEPT_ENV) <= set(after["env_names"])
        assert vm.list_env_vars()["MY_APP_MODE"] == "fast"
        assert after["sentinel_hits"] == []
        kept = vm.run("cat /root/.ssh/id_ed25519.pub", shell="raw").stdout
        assert kept.strip() == "keep-me"
        vm.close()
        vm = None

        # Once only: the next restart (human output) says nothing about it.
        assert _cli(env, "computer", "stop", name)[0] == 0
        code, human, raw = _cli(env, "computer", "start", name, json_out=False)
        assert code == 0, raw
        assert "removed copied keys" not in " ".join(raw.split())
        checks["no_message_on_second_start"] = True
    finally:
        if vm is not None:
            vm.close()
        _cli(env, "computer", "delete", name, "--force")
        ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
        assert SENTINEL not in text
        ARTIFACT.write_text(text)

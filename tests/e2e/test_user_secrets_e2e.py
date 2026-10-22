# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""User secrets and env refusal on a real, booted computer (D-11, D-12, D-15, D-18).

Runs the installed ``celesto`` CLI as a user would, plus the Python SDK
against the same CLI inventory. Opt in with ``pytest -m e2e
tests/e2e/test_user_secrets_e2e.py``; it boots one small Ubuntu computer
named ``w4-e2e-<random>`` and deletes it at the end.

Live proxy checks (guest sees a placeholder, upstream gets the real value,
``secret remove`` cuts it off) need the per-sandbox proxy runtime. When
``celesto.credentials.runtime`` is missing they are skipped, and the test
instead proves the fail-closed path: nothing reaches the guest.

Artifact: ``user_secrets_e2e.json`` in ``$CELESTO_TEST_ARTIFACTS`` (default
pytest's tmp dir) with every command, exit code, and JSON payload.
"""

from __future__ import annotations

import importlib.util
import json
import os
import secrets
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.e2e

# Sentinel values only.
SENTINEL_OPENAI = "sk-w4sentinel-e2e-openai-0000000000"
SENTINEL_GITHUB = "ghp_w4sentinelE2Egithub000000000000000"
SENTINEL_STRIPE = "w4-sentinel-e2e-stripe-value"
ALL_SENTINELS = (SENTINEL_OPENAI, SENTINEL_GITHUB, SENTINEL_STRIPE)

_CELESTO = Path(sys.executable).with_name("celesto")
_HAS_RUNTIME = importlib.util.find_spec("celesto.credentials.runtime") is not None


def _redact(text: str) -> str:
    for value in ALL_SENTINELS:
        text = text.replace(value, "<sentinel>")
    return text


class Transcript:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.steps: list[dict[str, Any]] = []

    def run(self, *argv: str, env: dict[str, str] | None = None) -> tuple[int, Any]:
        child_env = {k: v for k, v in os.environ.items() if k not in {"STRIPE_KEY"}}
        child_env.update(env or {})
        proc = subprocess.run(
            [str(_CELESTO), *argv],
            capture_output=True,
            text=True,
            env=child_env,
            stdin=subprocess.DEVNULL,
            timeout=300,
            check=False,
        )
        try:
            payload: Any = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = proc.stdout
        # Record which env names were passed, never their values.
        self.steps.append(
            {
                "argv": [_redact(arg) for arg in argv],
                "env_names": sorted(env or {}),
                "exit_code": proc.returncode,
                "output": payload,
                "stderr": proc.stderr[-2000:],
            }
        )
        self.save()
        for value in ALL_SENTINELS:
            assert value not in proc.stdout and value not in proc.stderr
        return proc.returncode, payload

    def note(self, **data: Any) -> None:
        self.steps.append(data)
        self.save()

    def save(self) -> None:
        self.path.write_text(json.dumps(self.steps, indent=2, default=str))


@pytest.fixture(scope="module")
def transcript(tmp_path_factory: pytest.TempPathFactory) -> Transcript:
    root = os.environ.get("CELESTO_TEST_ARTIFACTS")
    out = Path(root) if root else tmp_path_factory.mktemp("artifacts")
    out.mkdir(parents=True, exist_ok=True)
    return Transcript(out / "user_secrets_e2e.json")


@pytest.fixture(scope="module")
def computer(transcript: Transcript) -> Iterator[str]:
    if not _CELESTO.exists():
        pytest.skip(f"The celesto CLI is not installed next to {sys.executable}.")
    name = f"w4-e2e-{secrets.token_hex(3)}"
    code, payload = transcript.run(
        "computer", "create", "-n", name, "--os", "ubuntu", "--boot-timeout", "180", "--json"
    )
    if code != 0:
        pytest.fail(f"Could not create {name}: {payload}")
    try:
        yield name
    finally:
        transcript.run("computer", "delete", name, "--force", "--json")


def _guest_env_text(transcript: Transcript, name: str) -> str:
    code, payload = transcript.run(
        "computer",
        "exec",
        name,
        "--json",
        "--",
        "sh",
        "-c",
        "cat /etc/profile.d/celesto_env.sh 2>/dev/null; . /etc/profile >/dev/null 2>&1; env",
    )
    assert code == 0, payload
    return str(payload["data"]["stdout"])


def test_env_set_refuses_secret_and_nothing_reaches_the_guest(
    computer: str, transcript: Transcript
) -> None:
    code, payload = transcript.run(
        "computer", "env", "set", computer, f"OPENAI_API_KEY={SENTINEL_OPENAI}", "--json"
    )

    assert code == 1
    assert payload["error"]["code"] == "secret_refused"
    assert payload["error"]["message"] == (
        "OPENAI_API_KEY looks like a secret, so Celesto won't place it inside the computer. "
        f"Run 'celesto computer secret set {computer} OPENAI_API_KEY --host api.openai.com' "
        "instead."
    )
    guest = _guest_env_text(transcript, computer)
    assert SENTINEL_OPENAI not in guest
    assert "OPENAI_API_KEY" not in guest


def test_env_set_not_secret_passes(computer: str, transcript: Transcript) -> None:
    code, payload = transcript.run(
        "computer",
        "env",
        "set",
        computer,
        "--not-secret",
        "PUBLIC_KEY",
        "PUBLIC_KEY=ssh-ed25519-w4-not-secret",
        "--json",
    )

    assert code == 0, payload
    assert "PUBLIC_KEY=" in _guest_env_text(transcript, computer)


def test_sdk_set_env_vars_refuses_secret(computer: str, transcript: Transcript) -> None:
    from celesto import Celesto, SecretRefusedError
    from celesto.cli.service import CLIService

    vm = CLIService().vm_from_id(computer)
    try:
        with pytest.raises(SecretRefusedError) as caught:
            vm.set_env_vars({"GITHUB_TOKEN": SENTINEL_GITHUB})
        transcript.note(sdk_refusal=str(caught.value))
        assert str(caught.value) == (
            "GITHUB_TOKEN looks like a secret, so Celesto won't place it inside the computer. "
            'Pass secrets={"GITHUB_TOKEN": Secret(host="api.github.com")} instead.'
        )
    finally:
        vm.close()
    assert isinstance(vm, Celesto)
    assert SENTINEL_GITHUB not in _guest_env_text(transcript, computer)


def test_secret_set_on_running_computer(computer: str, transcript: Transcript) -> None:
    host = os.environ.get("CELESTO_TEST_SECRET_HOST", "api.stripe.com")
    code, payload = transcript.run(
        "computer",
        "secret",
        "set",
        computer,
        "STRIPE_KEY",
        "--host",
        host,
        "--json",
        env={"STRIPE_KEY": SENTINEL_STRIPE},
    )
    assert code == 0, payload
    guest = _guest_env_text(transcript, computer)
    assert SENTINEL_STRIPE not in guest

    code, listed = transcript.run("computer", "secret", "list", computer, "--json")
    assert code == 0
    (row,) = listed["data"]["secrets"]
    assert set(row) == {"name", "hosts", "source", "status", "last_used"}
    assert row["name"] == "STRIPE_KEY" and row["hosts"] == [host]

    if not _HAS_RUNTIME:
        # Fail closed: without the proxy, the guest gets neither value nor placeholder.
        assert payload["data"]["applied"] == "not_applied"
        assert "STRIPE_KEY" not in guest
        assert row["status"] == "proxy stopped"
        return

    assert payload["data"]["applied"] == "live"
    assert "STRIPE_KEY=celesto-placeholder-" in guest
    assert row["status"] == "active"


@pytest.mark.skipif(not _HAS_RUNTIME, reason="needs the credential proxy runtime (W1 + W3)")
def test_secret_remove_live_cuts_off_the_real_value(computer: str, transcript: Transcript) -> None:
    code, payload = transcript.run("computer", "secret", "remove", computer, "STRIPE_KEY", "--json")

    assert code == 0, payload
    assert payload["data"]["applied"] == "live"
    assert "STRIPE_KEY" not in _guest_env_text(transcript, computer)

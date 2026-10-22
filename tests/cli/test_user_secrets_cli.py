# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""User path for host-bound secrets and env refusal, without booting a VM.

These run the real ``celesto`` CLI entry point against a real SQLite
inventory in a temp ``CELESTO_DATA_DIR``. Nothing is mocked. Commands that
need a running sandbox live in ``tests/e2e/test_user_secrets_e2e.py``.

Each test writes a JSON transcript to ``$CELESTO_TEST_ARTIFACTS`` (default:
pytest's tmp dir) so the result can be inspected and diffed later.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from celesto.cli._sqlite import SQLiteStateManager
from celesto.cli.main import main
from celesto.credentials import user_secrets
from celesto.types import VMConfig, VMState

# Sentinel values only. Each test asserts these never show up in output or state.
SENTINEL_KEY = "sk-w4sentinel-cli-0000000000000000"
SENTINEL_STRIPE = "w4-sentinel-stripe-value-0001"


@pytest.fixture
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "celesto-data"
    path.mkdir()
    monkeypatch.setenv("CELESTO_DATA_DIR", str(path))
    monkeypatch.delenv("STRIPE_KEY", raising=False)
    return path


@pytest.fixture
def artifact_dir(tmp_path: Path) -> Path:
    root = os.environ.get("CELESTO_TEST_ARTIFACTS")
    path = Path(root) if root else tmp_path / "artifacts"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def stopped_vm(data_dir: Path, tmp_path: Path) -> str:
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.ext4"
    kernel.write_bytes(b"k")
    rootfs.write_bytes(b"r")
    state = SQLiteStateManager(data_dir / "celesto.db")
    state.create_vm(VMConfig(vm_id="w4-stopped", kernel_path=kernel, rootfs_path=rootfs))
    state.update_vm("w4-stopped", status=VMState.STOPPED)
    return "w4-stopped"


def _run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str]:
    code = main(list(argv))
    captured = capsys.readouterr()
    return code, captured.out + captured.err


def _json(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, dict]:
    code, out = _run(capsys, *argv, "--json")
    return code, json.loads(out)


def _flat(text: str) -> str:
    """Drop Rich panel borders and wrapping so a message can be matched exactly."""
    for char in "│╭╮╰╯─":
        text = text.replace(char, " ")
    return " ".join(text.split()).replace(" Error ", " ").removeprefix("Error ")


def _save(artifact_dir: Path, name: str, transcript: list[dict]) -> None:
    (artifact_dir / f"{name}.json").write_text(json.dumps(transcript, indent=2))


def _assert_no_values(data_dir: Path, *texts: str) -> None:
    db_path = data_dir / "celesto.db"
    db = db_path.read_bytes() if db_path.exists() else b""
    for text in texts:
        for value in (SENTINEL_KEY, SENTINEL_STRIPE):
            assert value not in text
            assert value.encode() not in db


# ----------------------------------------------------------------------
# D-12: env set refuses secrets before touching the sandbox
# ----------------------------------------------------------------------


def test_env_set_refuses_secret_name_with_exact_message(
    data_dir: Path, artifact_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, payload = _json(
        capsys, "sandbox", "env", "set", "my-sbx", f"OPENAI_API_KEY={SENTINEL_KEY}"
    )
    code_h, human = _run(
        capsys, "sandbox", "env", "set", "my-sbx", f"OPENAI_API_KEY={SENTINEL_KEY}"
    )
    _save(artifact_dir, "env_set_refusal", [payload, {"human": human}])

    expected = (
        "OPENAI_API_KEY looks like a secret, so Celesto won't place it inside the computer. "
        "Run 'celesto computer secret set my-sbx OPENAI_API_KEY --host api.openai.com' instead."
    )
    assert code == 1 and code_h == 1
    assert payload["ok"] is False
    assert payload["error"]["code"] == "secret_refused"
    assert payload["error"]["message"] == expected
    assert _flat(human).count(expected) == 1
    _assert_no_values(data_dir, json.dumps(payload), human)


def test_env_set_refuses_secret_shaped_value_under_plain_name(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, payload = _json(capsys, "sandbox", "env", "set", "my-sbx", f"MODEL_CFG={SENTINEL_KEY}")

    assert code == 1
    assert payload["error"]["message"] == (
        "MODEL_CFG looks like a secret, so Celesto won't place it inside the computer. "
        "Run 'celesto computer secret set my-sbx MODEL_CFG --host <the API's host name>' instead."
    )


def test_env_set_not_secret_skips_the_refusal(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # The refusal is skipped, so the command goes on to look up the sandbox.
    code, payload = _json(
        capsys,
        "sandbox",
        "env",
        "set",
        "w4-missing",
        "--not-secret",
        "PUBLIC_KEY",
        "PUBLIC_KEY=ssh-ed25519-not-secret",
    )

    assert code == 1
    assert payload["error"]["code"] != "secret_refused"
    assert "w4-missing" in payload["error"]["message"]


# ----------------------------------------------------------------------
# D-11 / D-18: secret set, list, remove on a stopped sandbox
# ----------------------------------------------------------------------


def test_secret_set_list_remove_on_stopped_sandbox(
    data_dir: Path,
    stopped_vm: str,
    artifact_dir: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("STRIPE_KEY", SENTINEL_STRIPE)
    transcript: list[dict] = []

    code, set_payload = _json(
        capsys, "sandbox", "secret", "set", stopped_vm, "STRIPE_KEY", "--host", "api.stripe.com"
    )
    transcript.append(set_payload)
    assert code == 0, set_payload
    assert set_payload["data"]["name"] == "STRIPE_KEY"
    assert set_payload["data"]["hosts"] == ["api.stripe.com"]
    assert set_payload["data"]["applied"] == "next_start"

    code, list_payload = _json(capsys, "sandbox", "secret", "list", stopped_vm)
    transcript.append(list_payload)
    assert code == 0
    assert list_payload["data"] == {
        "vm_id": stopped_vm,
        "secrets": [
            {
                "name": "STRIPE_KEY",
                "hosts": ["api.stripe.com"],
                "source": "env:STRIPE_KEY",
                "status": "proxy stopped",
                "last_used": None,
            }
        ],
    }

    code_h, human_list = _run(capsys, "sandbox", "secret", "list", stopped_vm)
    transcript.append({"human": human_list})
    assert code_h == 0
    assert "STRIPE_KEY" in human_list and "api.stripe.com" in human_list

    # The stored placeholder is stable and never shown.
    state = SQLiteStateManager(data_dir / "celesto.db")
    placeholder = state.list_user_secrets(stopped_vm)[0]["placeholder"]
    assert placeholder not in json.dumps(transcript)
    bindings, guest_env, missing = user_secrets.plan_for(stopped_vm, state)
    assert guest_env == {"STRIPE_KEY": placeholder}
    assert bindings[0].hosts == ("api.stripe.com",)
    assert bindings[0].source == "env:STRIPE_KEY"
    assert missing == []

    code, remove_payload = _json(capsys, "sandbox", "secret", "remove", stopped_vm, "STRIPE_KEY")
    transcript.append(remove_payload)
    assert code == 0
    code, empty = _json(capsys, "sandbox", "secret", "list", stopped_vm)
    transcript.append(empty)
    assert empty["data"]["secrets"] == []

    _save(artifact_dir, "secret_set_list_remove", transcript)
    _assert_no_values(data_dir, json.dumps(transcript))


def test_secret_set_without_value_on_stopped_sandbox_warns(
    data_dir: Path, stopped_vm: str, capsys: pytest.CaptureFixture[str]
) -> None:
    code, payload = _json(
        capsys, "sandbox", "secret", "set", stopped_vm, "STRIPE_KEY", "--host", "api.stripe.com"
    )

    assert code == 0
    assert payload["data"]["warnings"] == [
        "STRIPE_KEY isn't set in this terminal, so w4-stopped can't use it. "
        "Set it before you run 'celesto computer start w4-stopped'."
    ]
    state = SQLiteStateManager(data_dir / "celesto.db")
    _, _, missing = user_secrets.plan_for(stopped_vm, state, environ={})
    assert missing == [user_secrets.missing_warning("STRIPE_KEY", stopped_vm)]


@pytest.mark.parametrize(
    ("host", "message"),
    [
        (
            "https://api.stripe.com/v1",
            "'https://api.stripe.com/v1' isn't a host name. Use just the host: 'api.stripe.com'.",
        ),
        (
            "*.stripe.com",
            "'*.stripe.com' has a wildcard, but Celesto can only protect exact host names. "
            "Pass each host on its own, such as 'api.example.com'.",
        ),
    ],
)
def test_secret_set_rejects_non_host(
    data_dir: Path,
    stopped_vm: str,
    capsys: pytest.CaptureFixture[str],
    host: str,
    message: str,
) -> None:
    code, payload = _json(
        capsys, "sandbox", "secret", "set", stopped_vm, "STRIPE_KEY", "--host", host
    )

    assert code == 1
    assert payload["error"]["message"] == message
    assert SQLiteStateManager(data_dir / "celesto.db").list_user_secrets(stopped_vm) == []


def test_secret_remove_unknown_name(
    data_dir: Path, stopped_vm: str, capsys: pytest.CaptureFixture[str]
) -> None:
    code, payload = _json(capsys, "sandbox", "secret", "remove", stopped_vm, "STRIPE_KEY")

    assert code == 1
    assert payload["error"]["message"] == (
        "STRIPE_KEY isn't a secret in w4-stopped. "
        "Run 'celesto computer secret list w4-stopped' to see its secrets."
    )


def test_sdk_config_secrets_are_listed_by_the_cli(
    data_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    kernel = tmp_path / "vmlinux2"
    rootfs = tmp_path / "rootfs2.ext4"
    kernel.write_bytes(b"k")
    rootfs.write_bytes(b"r")
    state = SQLiteStateManager(data_dir / "celesto.db")
    state.create_vm(
        VMConfig(
            vm_id="w4-sdk",
            kernel_path=kernel,
            rootfs_path=rootfs,
            secrets={"STRIPE_KEY": user_secrets.Secret(host="api.stripe.com")},
        )
    )

    code, payload = _json(capsys, "sandbox", "secret", "list", "w4-sdk")

    assert code == 0
    assert [row["name"] for row in payload["data"]["secrets"]] == ["STRIPE_KEY"]

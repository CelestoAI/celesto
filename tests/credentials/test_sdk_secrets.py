# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""Python SDK user path for D-11/D-12 that fails before any VM boots.

The SDK refuses secrets in plain ``env_vars`` while building the config, so
these need no hypervisor. Booted checks live in tests/e2e.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from celesto import Celesto, Secret, SecretRefusedError
from celesto.storage._base import vm_config_from_json
from celesto.types import VMConfig

SENTINEL = "sk-w4sentinel-sdk-00000000000000000"


@pytest.fixture
def boot_files(tmp_path: Path) -> dict[str, Path]:
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.ext4"
    kernel.write_bytes(b"k")
    rootfs.write_bytes(b"r")
    return {"kernel_path": kernel, "rootfs_path": rootfs}


def test_vmconfig_refuses_secret_env_var(boot_files: dict[str, Path]) -> None:
    with pytest.raises(SecretRefusedError) as caught:
        VMConfig(vm_id="w4-sdk", env_vars={"OPENAI_API_KEY": SENTINEL}, **boot_files)

    assert str(caught.value) == (
        "OPENAI_API_KEY looks like a secret, so Celesto won't place it inside the sandbox. "
        'Pass secrets={"OPENAI_API_KEY": Secret(host="api.openai.com")} instead.'
    )
    assert SENTINEL not in repr(caught.value.details)


def test_vmconfig_not_secret_allows_the_name(boot_files: dict[str, Path]) -> None:
    config = VMConfig(
        vm_id="w4-sdk",
        env_vars={"PUBLIC_KEY": "ssh-ed25519 AAAA"},
        not_secret=["PUBLIC_KEY"],
        **boot_files,
    )

    assert config.env_vars == {"PUBLIC_KEY": "ssh-ed25519 AAAA"}


def test_vmconfig_secrets_round_trip_without_values(boot_files: dict[str, Path]) -> None:
    config = VMConfig(
        vm_id="w4-sdk",
        secrets={"STRIPE_KEY": Secret(host=["API.Stripe.com", "files.stripe.com"])},
        **boot_files,
    )

    loaded = vm_config_from_json(config.model_dump_json())
    assert loaded.secrets["STRIPE_KEY"].hosts == ("api.stripe.com", "files.stripe.com")


def test_vmconfig_rejects_name_in_both_env_vars_and_secrets(boot_files: dict[str, Path]) -> None:
    with pytest.raises(ValueError, match="STRIPE_KEY is both a secret and a plain env var"):
        VMConfig(
            vm_id="w4-sdk",
            env_vars={"STRIPE_KEY": "x"},
            not_secret=["STRIPE_KEY"],
            secrets={"STRIPE_KEY": Secret(host="api.stripe.com")},
            **boot_files,
        )


def test_stored_config_with_old_secret_still_loads(boot_files: dict[str, Path]) -> None:
    """Sandboxes created before this release must stay listable (D-17 cleans them)."""
    raw = VMConfig(vm_id="w4-old", **boot_files).model_dump(mode="json")
    raw["env_vars"] = {"OPENAI_API_KEY": SENTINEL}

    import json

    loaded = vm_config_from_json(json.dumps(raw))
    assert loaded.vm_id == "w4-old"


def test_browser_refuses_secret_env_before_boot() -> None:
    with pytest.raises(SecretRefusedError) as caught:
        Celesto.browser(session_id="w4-browser", env_vars={"GITHUB_TOKEN": SENTINEL})

    assert str(caught.value).startswith(
        "GITHUB_TOKEN looks like a secret, so Celesto won't place it inside the sandbox."
    )


def test_secret_rejects_url_and_wildcard() -> None:
    from celesto.exceptions import ValidationError

    with pytest.raises(ValidationError, match="Use just the host: 'api.stripe.com'"):
        Secret(host="https://api.stripe.com")
    with pytest.raises(ValidationError, match="wildcard"):
        Secret(host="*.stripe.com")

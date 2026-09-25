"""Tests for the sanitized HTTP API wire models."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from pydantic import ValidationError

from celesto.server.models import (
    CreateBrowserSessionRequest,
    CreateSandboxRequest,
)


def test_create_request_accepts_supported_options() -> None:
    request = CreateSandboxRequest(os="ubuntu", memory=1024, disk_size=4096, backend="qemu")

    assert request.model_dump(exclude_none=True) == {
        "os": "ubuntu",
        "memory": 1024,
        "disk_size": 4096,
        "backend": "qemu",
        "network": {"mode": "open"},
    }


@pytest.mark.parametrize("field,value", [("memory", 127), ("disk_size", 0)])
def test_create_request_rejects_invalid_resource_sizes(field: str, value: int) -> None:
    with pytest.raises(ValidationError):
        CreateSandboxRequest(**{field: value})


def test_restricted_network_requires_an_ipv4_range() -> None:
    with pytest.raises(ValidationError):
        CreateSandboxRequest(network={"mode": "restricted", "allowed_cidrs": []})


def test_browser_request_validates_profile_and_live_video() -> None:
    with pytest.raises(ValidationError, match="profile_id is required"):
        CreateBrowserSessionRequest(profile_mode="persistent")
    with pytest.raises(ValidationError, match="record_video requires"):
        CreateBrowserSessionRequest(record_video=True)
    with pytest.raises(ValidationError):
        CreateBrowserSessionRequest(session_id="Browser-Demo")
    with pytest.raises(ValidationError):
        CreateBrowserSessionRequest(profile_id="browser-")

    request = CreateBrowserSessionRequest(
        session_id="browser-demo",
        mode="live",
        backend="qemu",
        viewport={"width": 1440, "height": 900},
        allow_downloads=False,
        network={"mode": "off"},
    )
    assert request.viewport.width == 1440
    assert request.network.mode == "off"

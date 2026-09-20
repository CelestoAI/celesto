"""Typed constructor options for the fixed-provider public entry points."""

from collections.abc import Callable
from pathlib import Path
from typing import Any, TypedDict

from celesto.callbacks import Callback
from celesto.comm.base import CommChannelKind
from celesto.types import GuestOS, InternetSettings, QemuMachine, VMConfig


class LocalOptions(TypedDict, total=False):
    template_id: str | None
    config: VMConfig | None
    image: str | None
    data_dir: Path | None
    socket_dir: Path | None
    backend: str | None
    os: GuestOS | str | None
    qemu_machine: QemuMachine
    memory: int | None
    disk_size: int | None
    ssh_user: str
    ssh_key_path: str | None
    ssh_password: str | None
    comm_channel: CommChannelKind | None
    internet_settings: InternetSettings | dict[str, Any] | None
    mounts: list[str] | None
    writable_mounts: bool
    callbacks: list[Callback] | None
    on_download: Callable[[str, int, int | None], None] | None


class CloudOptions(TypedDict, total=False):
    api_key: str | None
    base_url: str
    organization_id: str | None
    startup_timeout: float
    cleanup_timeout: float
    vcpus: int | None
    ram_mb: int | None
    disk_size_mb: int | None
    image: str
    template_id: str | None
    template_version: str | None
    external_volume_enabled: bool

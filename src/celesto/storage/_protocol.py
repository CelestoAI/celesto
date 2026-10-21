# Copyright 2026 Celesto AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""State manager protocol for Celesto storage backends."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Protocol, TypedDict

from celesto.types import (
    BrowserSessionConfig,
    BrowserSessionInfo,
    BrowserSessionState,
    DesktopEndpoint,
    NetworkConfig,
    SnapshotInfo,
    VMConfig,
    VMInfo,
    VMState,
)


class UserSecretRecord(TypedDict):
    """A user-defined, host-bound secret stored with its sandbox (D-11).

    Holds the definition and the guest placeholder only, never the real value.
    """

    name: str
    hosts: list[str]
    source: str
    header: str | None
    placeholder: str


class StateManagerProtocol(Protocol):
    """Interface for Celesto state persistence.

    Implementations must provide atomic operations for VM lifecycle,
    IP/port allocation, snapshots, and browser sessions.
    """

    def close(self) -> None:
        """Release backend resources (e.g. connection pool).

        No-op for SQLite. Must be called for PostgreSQL to avoid
        leaking pooled connections.
        """
        ...

    # ------------------------------------------------------------------
    # VM operations
    # ------------------------------------------------------------------

    def create_vm(self, config: VMConfig) -> VMInfo:
        pass

    def get_vm(self, vm_id: str) -> VMInfo:
        pass

    def update_vm(
        self,
        vm_id: str,
        *,
        status: VMState | None = None,
        config: VMConfig | None = None,
        network: NetworkConfig | None = None,
        pid: int | None = None,
        control_socket_path: Path | None = None,
        display: DesktopEndpoint | None = None,
        clear_pid: bool = False,
        clear_socket_path: bool = False,
        clear_display: bool = False,
    ) -> VMInfo:
        pass

    def delete_vm(self, vm_id: str) -> None:
        pass

    def list_vms(self, status: VMState | None = None) -> list[VMInfo]:
        pass

    # ------------------------------------------------------------------
    # Credential-protection version (see credentials/store.py)
    # ------------------------------------------------------------------

    def get_credential_protection(self, vm_id: str) -> int:
        pass

    def set_credential_protection(self, vm_id: str, version: int) -> None:
        pass

    # ------------------------------------------------------------------
    # IP allocation
    # ------------------------------------------------------------------

    def allocate_ip(
        self,
        vm_id: str,
        tap_device: str,
        requested_ip: str | None = None,
    ) -> str:
        pass

    def release_ip(self, vm_id: str) -> None:
        pass

    def get_ip_lease(self, vm_id: str) -> tuple[str, str] | None:
        pass

    def update_ip_lease_tap(self, vm_id: str, tap_device: str) -> None:
        pass

    # ------------------------------------------------------------------
    # SSH port allocation
    # ------------------------------------------------------------------

    def reserve_ssh_port(
        self,
        vm_id: str,
        guest_port: int = 22,
        host_port: int | None = None,
        excluded_host_ports: set[int] | None = None,
    ) -> int:
        pass

    def get_ssh_port(self, vm_id: str) -> int | None:
        pass

    def release_ssh_port(self, vm_id: str) -> None:
        pass

    # ------------------------------------------------------------------
    # vsock CID allocation
    # ------------------------------------------------------------------

    def reserve_vsock_cid(self, vm_id: str, guest_cid: int | None = None) -> int:
        pass

    def get_vsock_cid(self, vm_id: str) -> int | None:
        pass

    def release_vsock_cid(self, vm_id: str) -> None:
        pass

    # ------------------------------------------------------------------
    # TAP allocation (bridge mode)
    # ------------------------------------------------------------------

    def reserve_tap_name(
        self,
        vm_id: str,
        mode: str,
        bridge_name: str | None = None,
        requested_tap: str | None = None,
    ) -> str:
        pass

    def get_tap_allocation(self, vm_id: str) -> tuple[str, str, str | None] | None:
        pass

    def release_tap_name(self, vm_id: str) -> None:
        pass

    # ------------------------------------------------------------------
    # Snapshots
    # ------------------------------------------------------------------

    def create_snapshot(self, info: SnapshotInfo) -> SnapshotInfo:
        pass

    def get_snapshot(self, snapshot_id: str) -> SnapshotInfo:
        pass

    def list_snapshots(self, vm_id: str | None = None) -> list[SnapshotInfo]:
        pass

    def mark_snapshot_restored(self, snapshot_id: str, restored_vm_id: str) -> SnapshotInfo:
        pass

    def delete_snapshot(self, snapshot_id: str) -> None:
        pass

    # ------------------------------------------------------------------
    # Browser sessions
    # ------------------------------------------------------------------

    def create_browser_session(
        self,
        info: BrowserSessionInfo,
        config: BrowserSessionConfig,
    ) -> BrowserSessionInfo:
        pass

    def get_browser_session(self, session_id: str) -> BrowserSessionInfo:
        pass

    def get_browser_session_config(self, session_id: str) -> BrowserSessionConfig:
        pass

    def update_browser_session(
        self,
        session_id: str,
        *,
        status: BrowserSessionState | None = None,
        cdp_url: str | None = None,
        live_url: str | None = None,
        vnc_url: str | None = None,
        debug_port: int | None = None,
        vnc_port: int | None = None,
        profile_id: str | None = None,
        expires_at: datetime | None = None,
        artifacts_dir: Path | None = None,
        config: BrowserSessionConfig | None = None,
    ) -> BrowserSessionInfo:
        pass

    def delete_browser_session(self, session_id: str) -> None:
        pass

    def list_browser_sessions(
        self, status: BrowserSessionState | None = None
    ) -> list[BrowserSessionInfo]:
        pass

    # ------------------------------------------------------------------
    # User secrets (definitions and placeholders only, never values)
    # ------------------------------------------------------------------

    def put_user_secret(self, vm_id: str, record: UserSecretRecord) -> None:
        """Insert or replace the secret named ``record["name"]`` for *vm_id*."""
        ...

    def delete_user_secret(self, vm_id: str, name: str) -> bool:
        """Remove a secret; return whether it existed."""
        ...

    def list_user_secrets(self, vm_id: str) -> list[UserSecretRecord]:
        """Return the secrets defined for *vm_id*, sorted by name."""
        ...

    def claim_user_secret_seed(self, vm_id: str) -> bool:
        """Return True exactly once per VM, so config secrets are copied in once."""
        ...

    # ------------------------------------------------------------------
    # Allowed SSH keys (public keys only; D-13)
    # ------------------------------------------------------------------

    def add_ssh_key(self, vm_id: str, fingerprint: str, public_key: str) -> bool:
        """Allow a key for *vm_id*; False if it was already allowed."""
        ...

    def remove_ssh_key(self, vm_id: str, fingerprint: str) -> bool:
        """Disallow a key; False if it was not allowed."""
        ...

    def list_ssh_keys(self, vm_id: str) -> list[tuple[str, str]]:
        """Return ``(fingerprint, public_key_line)`` for each allowed key."""
        ...

    # ------------------------------------------------------------------
    # Reconciliation
    # ------------------------------------------------------------------

    def reconcile(self) -> list[str]:
        pass

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

"""Privileged end-to-end coverage for guest-managed bridged networking."""

from __future__ import annotations

import asyncio
import json
import os
import platform
import secrets
import subprocess
import tempfile
import threading
import time
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from shutil import which
from typing import Any

import pytest
from _util import (
    BOOT_TIMEOUT,
    E2E_BACKENDS,
    E2EBackend,
    require_backend_available,
    selected_backend,
)

from celesto import Celesto
from celesto.cli._sqlite import SQLiteStateManager
from celesto.comm import host_supports_vsock
from celesto.exceptions import CelestoError, VMNotFoundError
from celesto.facade import _build_auto_config
from celesto.host.network import NetworkManager
from celesto.runtime.backends import BACKEND_FIRECRACKER, BACKEND_QEMU
from celesto.types import NetworkAttachmentConfig, SnapshotType, VMState
from celesto.vm import CelestoManager

pytestmark = pytest.mark.e2e


@dataclass(frozen=True, slots=True)
class _BridgeLab:
    bridge: str
    uplink: str
    peer: str
    namespace: str
    guest_ip: str
    peer_ip: str


def _privileged_prefix() -> list[str]:
    if os.geteuid() == 0:
        return []
    if which("sudo") is None:
        pytest.skip("Bridge e2e needs root or passwordless sudo to create temporary interfaces.")
    check = subprocess.run(
        ["sudo", "-n", "true"],
        check=False,
        capture_output=True,
        text=True,
    )
    if check.returncode != 0:
        pytest.skip("Bridge e2e needs root or passwordless sudo to create temporary interfaces.")
    return ["sudo", "-n"]


def _run_privileged(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*_privileged_prefix(), *args],
        check=check,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def bridge_lab() -> _BridgeLab:
    """Create an address-free bridge with a network-namespace peer."""
    if platform.system() != "Linux" or which("ip") is None:
        pytest.skip("Bridge e2e requires Linux and the ip command.")

    token = f"{os.getpid():x}{secrets.token_hex(2)}"[-7:]
    octet = int(token[-2:], 16) % 200 + 20
    lab = _BridgeLab(
        bridge=f"svbr{token}",
        uplink=f"svup{token}",
        peer=f"svpr{token}",
        namespace=f"celesto-e2e-{token}",
        guest_ip=f"198.18.{octet}.2",
        peer_ip=f"198.18.{octet}.1",
    )

    _run_privileged("ip", "netns", "add", lab.namespace)
    try:
        _run_privileged("ip", "link", "add", lab.bridge, "type", "bridge")
        _run_privileged("ip", "link", "add", lab.uplink, "type", "veth", "peer", "name", lab.peer)
        _run_privileged("ip", "link", "set", lab.uplink, "master", lab.bridge)
        # Keep both address-free host interfaces free of automatic IPv6 addresses.
        _run_privileged("sysctl", "-q", "-w", f"net.ipv6.conf.{lab.bridge}.disable_ipv6=1")
        _run_privileged("sysctl", "-q", "-w", f"net.ipv6.conf.{lab.uplink}.disable_ipv6=1")
        _run_privileged("ip", "link", "set", lab.peer, "netns", lab.namespace)
        _run_privileged("ip", "link", "set", lab.bridge, "up")
        _run_privileged("ip", "link", "set", lab.uplink, "up")
        _run_privileged(
            "ip",
            "netns",
            "exec",
            lab.namespace,
            "ip",
            "addr",
            "add",
            f"{lab.peer_ip}/24",
            "dev",
            lab.peer,
        )
        _run_privileged("ip", "netns", "exec", lab.namespace, "ip", "link", "set", "lo", "up")
        _run_privileged("ip", "netns", "exec", lab.namespace, "ip", "link", "set", lab.peer, "up")
        yield lab
    finally:
        _run_privileged("ip", "netns", "del", lab.namespace, check=False)
        _run_privileged("ip", "link", "del", lab.bridge, check=False)
        _run_privileged("ip", "link", "del", lab.uplink, check=False)


def _wait_for_guest_network_init(sandbox: Celesto, *, timeout: float = 30.0) -> None:
    """Wait until PID 1 finishes its initial DHCP/static-network attempt."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = sandbox.run("grep -q 'stage=net-config-done' /var/log/celesto-boot.log")
        if result.exit_code == 0:
            return
        time.sleep(0.25)
    pytest.fail("Guest init did not finish its network setup before the timeout.")


def _assert_namespace_can_ping(lab: _BridgeLab, *, timeout: float = 15.0) -> None:
    """Wait for guest init and bridge forwarding to make the guest reachable."""
    deadline = time.monotonic() + timeout
    result: subprocess.CompletedProcess[str] | None = None
    while time.monotonic() < deadline:
        result = _run_privileged(
            "ip",
            "netns",
            "exec",
            lab.namespace,
            "ping",
            "-c",
            "1",
            "-W",
            "1",
            lab.guest_ip,
            check=False,
        )
        if result.returncode == 0:
            return
        time.sleep(0.5)
    assert result is not None
    pytest.fail(result.stderr or result.stdout)


@pytest.mark.parametrize("backend", E2E_BACKENDS, ids=str)
def test_bridge_connectivity_restart_restore_and_delete(
    backend: E2EBackend,
    bridge_lab: _BridgeLab,
    request: pytest.FixtureRequest,
) -> None:
    """Exercise bridge connectivity, vsock management, repair, restore, and cleanup."""
    selected = selected_backend(request.config)
    if selected != "all" and backend != selected:
        pytest.skip(
            f"End-to-end tests for '{backend}' are skipped because this run selected "
            f"'{selected}'; rerun all backends with: pytest tests/e2e."
        )
    require_backend_available(backend, request.config, sandbox_name=f"bridge-{backend}")
    if backend == "qemu" and not host_supports_vsock():
        pytest.skip("Bridge e2e requires /dev/vhost-vsock for QEMU.")

    vm_name = f"e2e-bridge-{backend}-{secrets.token_hex(2)}"
    config, ssh_key_path = _build_auto_config(
        vm_name=vm_name,
        os="alpine",
        backend=backend,
        qemu_machine="auto",
        memory=None,
        disk_size_mib=None,
        ssh_key_path=None,
    )
    config = config.model_copy(
        update={
            "comm_channel": "vsock",
            "network_attachment": NetworkAttachmentConfig(mode="bridge", bridge=bridge_lab.bridge),
        }
    )

    sandbox = Celesto(config, ssh_key_path=ssh_key_path, comm_channel="vsock")
    restored: Celesto | None = None
    tap_name: str | None = None
    try:
        sandbox.start(boot_timeout=BOOT_TIMEOUT)
        assert sandbox.status == VMState.RUNNING
        assert sandbox.run("echo managed-over-vsock").stdout.strip() == "managed-over-vsock"
        # The guest agent intentionally starts before networking. Wait for the
        # no-DHCP-server attempt to finish before replacing it with static setup.
        _wait_for_guest_network_init(sandbox)

        configure = sandbox.run(
            "mkdir -p /etc/celesto\n"
            "cat > /etc/celesto/network.sh <<'EOF'\n"
            "#!/bin/sh\n"
            "set -e\n"
            'ip addr flush dev "$1"\n'
            f'ip addr add {bridge_lab.guest_ip}/24 dev "$1"\n'
            'ip link set "$1" up\n'
            "EOF\n"
            "chmod +x /etc/celesto/network.sh\n"
            "/etc/celesto/network.sh eth0 && sync"
        )
        assert configure.exit_code == 0, configure.stderr
        assert sandbox.run(f"ping -c 1 -W 3 {bridge_lab.peer_ip}").exit_code == 0
        _assert_namespace_can_ping(bridge_lab)

        assert sandbox.info.network is not None
        tap_name = sandbox.info.network.tap_device
        assert tap_name

        # A missing owned TAP is safely recreated on the next start.
        sandbox.stop()
        _run_privileged("ip", "link", "del", tap_name)
        sandbox.start(boot_timeout=BOOT_TIMEOUT)
        assert sandbox.run("echo restarted").stdout.strip() == "restarted"
        _assert_namespace_can_ping(bridge_lab)

        snapshot_type = SnapshotType.DISK if backend == BACKEND_FIRECRACKER else SnapshotType.FULL
        snapshot = sandbox.snapshot(snapshot_type=snapshot_type)
        sandbox.stop()
        sandbox.delete()
        assert _run_privileged("ip", "link", "show", tap_name, check=False).returncode != 0

        restored = Celesto.from_snapshot(snapshot.snapshot_id, backend=backend, resume_vm=True)
        assert restored.run("echo restored-over-vsock").stdout.strip() == "restored-over-vsock"
        _assert_namespace_can_ping(bridge_lab)
    finally:
        # QEMU full-snapshot shutdown has separate lifecycle coverage and can
        # outlive its stop timeout; do not make this bridge test own that path.
        target = restored or sandbox
        with suppress(Exception):
            target.stop()
        with suppress(Exception):
            target.delete()
        if tap_name is not None:
            _run_privileged("ip", "link", "del", tap_name, check=False)


def test_cancelled_async_create_removes_the_interface_it_was_setting_up(
    bridge_lab: _BridgeLab,
    request: pytest.FixtureRequest,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cancelling creation waits for interface setup, then removes the interface.

    Ways this can fail: the cancelled call returns and releases the computer's
    lock while setup still runs on a worker thread; rollback runs before the
    interface exists, so the interface appears afterwards with no computer
    that owns it; or the computer's row is left behind.
    """
    selected = selected_backend(request.config)
    if selected not in ("all", BACKEND_QEMU):
        pytest.skip(
            f"End-to-end tests for 'qemu' are skipped because this run selected "
            f"'{selected}'; rerun with: pytest tests/e2e --e2e-backend qemu."
        )
    require_backend_available(BACKEND_QEMU, request.config, sandbox_name="bridge-cancel")
    if not host_supports_vsock():
        pytest.skip("Bridge e2e requires /dev/vhost-vsock for QEMU.")

    vm_name = f"e2e-bridge-cancel-{secrets.token_hex(2)}"
    config, _ = _build_auto_config(vm_name=vm_name, os="alpine", backend=BACKEND_QEMU)
    config = config.model_copy(
        update={
            "comm_channel": "vsock",
            "network_attachment": NetworkAttachmentConfig(mode="bridge", bridge=bridge_lab.bridge),
        }
    )
    data = Path(tempfile.mkdtemp(prefix="bc-data-"))
    sockets = Path(tempfile.mkdtemp(prefix="bc-", dir="/tmp"))
    state = SQLiteStateManager(data / "celesto.db")
    manager = CelestoManager(data_dir=data, socket_dir=sockets, state_manager=state)

    events: list[dict[str, Any]] = []
    entered = threading.Event()
    released = threading.Event()
    tap: dict[str, str] = {}
    original_prepare = NetworkManager.prepare_bridged_tap

    def gated_prepare(self: NetworkManager, tap_name: str, *args: Any, **kw: Any) -> None:
        # Hold before the interface exists: the moment a cancel used to
        # let rollback run too early.
        tap["name"] = tap_name
        events.append({"event": "setup_waiting_to_create_interface", "tap": tap_name})
        entered.set()
        released.wait(120)
        original_prepare(self, tap_name, *args, **kw)
        events.append({"event": "interface_created", "tap": tap_name})

    monkeypatch.setattr(NetworkManager, "prepare_bridged_tap", gated_prepare)

    def lock_free() -> bool:
        try:
            lock = manager._acquire_operation_lock(
                manager._lifecycle_lock_name(vm_name), timeout=0, vm_id=vm_name
            )
        except CelestoError:
            return False
        manager._release_vm_create_lock(lock)
        return True

    def row_exists() -> bool:
        try:
            state.get_vm(vm_name)
        except VMNotFoundError:
            return False
        return True

    async def cancel_during_setup() -> tuple[dict[str, Any], str]:
        task = asyncio.ensure_future(manager.async_create(config))
        assert await asyncio.to_thread(entered.wait, 120), "create never reached setup"
        task.cancel()
        done, _ = await asyncio.wait({task}, timeout=3.0)
        held = {"returned_before_setup_finished": bool(done), "lock_free": lock_free()}
        events.append({"event": "while_setup_held", **held})
        released.set()
        try:
            await task
        except asyncio.CancelledError:
            return held, "cancelled"
        except Exception as exc:  # noqa: BLE001 - reported by the test
            return held, repr(exc)
        return held, "returned"

    facts: dict[str, Any] = {}
    try:
        held, ended = asyncio.run(cancel_during_setup())
        interface_left = (
            _run_privileged("ip", "link", "show", tap["name"], check=False).returncode == 0
        )
        facts.update(held=held, ended=ended, row_after=row_exists(), interface_left=interface_left)
    finally:
        released.set()
        artifact_dir = Path(os.environ.get("CELESTO_E2E_ARTIFACT_DIR") or tmp_path)
        artifact_dir.mkdir(parents=True, exist_ok=True)
        artifact = artifact_dir / f"{request.node.name}-{vm_name}.json"
        artifact.write_text(json.dumps({"events": events, "facts": facts}, indent=2) + "\n")
        print(f"bridge cancel report: {artifact}")
        if "name" in tap:
            _run_privileged("ip", "link", "del", tap["name"], check=False)
        with suppress(Exception):
            manager.delete(vm_name)
        manager.close()
        state.close()

    assert not held["returned_before_setup_finished"], "create returned while setup ran"
    assert not held["lock_free"], "create released the lock while setup ran"
    assert ended == "cancelled", f"the cancelled create ended with {ended}"
    assert not facts["row_after"], "cancelled create left the computer's row behind"
    assert not interface_left, f"cancelled create left interface {tap['name']} behind"

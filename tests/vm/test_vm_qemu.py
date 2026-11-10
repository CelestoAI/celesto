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

"""QEMU-specific Celesto manager tests."""

import asyncio
import signal
import subprocess
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from celesto.exceptions import CelestoError, NetworkError, VMNotFoundError
from celesto.types import (
    NetworkConfig,
    PortForwardConfig,
    VMConfig,
    VMInfo,
    VMState,
    VsockConfig,
    WorkspaceMount,
)
from celesto.vm import CelestoManager


def _qemu_vm_info(tmp_path: Path) -> VMInfo:
    """Return a minimal QEMU VMInfo for launch-command tests."""
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.ext4"
    kernel.touch()
    rootfs.touch()
    return VMInfo(
        vm_id="vm-qemu",
        status=VMState.CREATED,
        config=VMConfig(
            vm_id="vm-qemu",
            kernel_path=kernel,
            rootfs_path=rootfs,
            backend="qemu",
            boot_args="console=ttyS0 reboot=k panic=1 init=/init",
        ),
        network=NetworkConfig(
            guest_ip="10.0.2.15",
            tap_device="qemu-user",
            guest_mac="52:54:00:12:34:56",
            ssh_host_port=2200,
        ),
    )


def test_live_qemu_vsock_cids_reads_proc_cmdline_without_subprocess(tmp_path: Path) -> None:
    """The live-CID guard should not spawn ``ps`` during VM create."""
    proc = tmp_path / "proc"
    proc.mkdir()
    (proc / "1").mkdir()
    (proc / "1" / "cmdline").write_bytes(
        b"qemu-system-x86_64\0-device\0vhost-vsock-pci,guest-cid=7,id=vsock0\0"
    )
    (proc / "2").mkdir()
    (proc / "2" / "cmdline").write_bytes(
        b"qemu-system-aarch64\0-device\0vhost-vsock-device,guest-cid=8,id=vsock0\0"
    )
    (proc / "not-a-pid").mkdir()

    with (
        patch("celesto.vm.platform.system", return_value="Linux"),
        patch("celesto.vm.subprocess.run", side_effect=AssertionError("must not spawn ps")),
    ):
        assert CelestoManager._live_qemu_vsock_cids(proc) == {7, 8}


def test_start_qemu_missing_binary_uses_linux_install_hint(tmp_path: Path) -> None:
    """Linux users should get a Linux package-manager hint, not Homebrew."""
    sdk = CelestoManager(
        data_dir=tmp_path / "data", socket_dir=tmp_path / "sockets", backend="qemu"
    )

    with (
        patch.object(CelestoManager, "_find_qemu_binary", return_value=None),
        patch("celesto.vm.platform.system", return_value="Linux"),
        patch("celesto.vm.platform.machine", return_value="x86_64"),
        patch("celesto.vm._linux_os_release_ids", return_value={"ubuntu", "debian"}),
        pytest.raises(CelestoError) as exc_info,
    ):
        sdk._start_qemu(_qemu_vm_info(tmp_path), tmp_path / "vm-qemu.log")

    message = str(exc_info.value)
    assert "sudo apt-get update && sudo apt-get install -y qemu-system-x86 qemu-utils" in message
    assert "brew install qemu" not in message


def test_create_qemu_summarizes_busy_ssh_ports(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """QEMU slirp VMs skip busy ports with one informational summary."""
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.ext4"
    kernel.touch()
    rootfs.touch()
    config = VMConfig(
        vm_id="vm-qemu-busy-port",
        kernel_path=kernel,
        rootfs_path=rootfs,
        backend="qemu",
        comm_channel="ssh",
    )
    sdk = CelestoManager(
        data_dir=tmp_path / "data", socket_dir=tmp_path / "sockets", backend="qemu"
    )

    with (
        caplog.at_level("INFO", logger="celesto.vm"),
        patch.object(CelestoManager, "_create_qemu_overlay_disk") as mock_overlay,
        patch.object(
            CelestoManager,
            "_local_ssh_port_is_available",
            side_effect=lambda port: port >= 2203,
        ),
    ):
        mock_overlay.side_effect = lambda _source, target, **_kwargs: target.touch()
        vm_info = sdk.create(config)

    assert vm_info.network is not None
    assert vm_info.network.ssh_host_port == 2203
    assert [
        (record.levelname, record.message)
        for record in caplog.records
        if "busy SSH ports" in record.message
    ] == [
        (
            "INFO",
            "Skipped 3 busy SSH ports while creating sandbox 'vm-qemu-busy-port'; using port 2203",
        )
    ]


def test_local_tcp_port_probe_handles_invalid_ports() -> None:
    """Invalid TCP ports should be treated as unavailable, not crash the probe."""
    assert CelestoManager._local_tcp_port_is_available("127.0.0.1", 65536) is False


def test_start_qemu_slirp_reports_busy_ssh_port_before_launch(tmp_path: Path) -> None:
    """A stopped QEMU slirp VM should fail clearly before QEMU exits early."""
    vm_info = _qemu_vm_info(tmp_path)
    sdk = CelestoManager(
        data_dir=tmp_path / "data", socket_dir=tmp_path / "sockets", backend="qemu"
    )
    sdk.state.create_vm(vm_info.config)
    sdk.state.update_vm(vm_info.vm_id, network=vm_info.network)

    with (
        patch.object(CelestoManager, "_local_ssh_port_is_available", return_value=False),
        patch.object(sdk, "_runtime_adapter_for_backend") as mock_adapter_factory,
        pytest.raises(CelestoError, match="Local SSH port 2200 is already in use"),
    ):
        sdk.start(vm_info.vm_id)

    mock_adapter_factory.assert_not_called()
    assert sdk.state.get_vm(vm_info.vm_id).status == VMState.CREATED


def test_start_qemu_slirp_reports_busy_custom_forward_before_launch(tmp_path: Path) -> None:
    """Configured QEMU host forwards should get the same clear preflight error."""
    vm_info = _qemu_vm_info(tmp_path)
    config = vm_info.config.model_copy(
        update={"port_forwards": [PortForwardConfig(host_port=39011, guest_port=9222)]}
    )
    vm_info = vm_info.model_copy(update={"config": config})
    sdk = CelestoManager(
        data_dir=tmp_path / "data", socket_dir=tmp_path / "sockets", backend="qemu"
    )
    sdk.state.create_vm(vm_info.config)
    sdk.state.update_vm(vm_info.vm_id, network=vm_info.network)

    with (
        patch.object(
            CelestoManager,
            "_local_tcp_port_is_available",
            side_effect=lambda _host, port: port != 39011,
        ),
        patch.object(sdk, "_runtime_adapter_for_backend") as mock_adapter_factory,
        pytest.raises(CelestoError, match="Local port 127.0.0.1:39011 is already in use"),
    ):
        sdk.start(vm_info.vm_id)

    mock_adapter_factory.assert_not_called()
    assert sdk.state.get_vm(vm_info.vm_id).status == VMState.CREATED


@patch("celesto.vm.subprocess.Popen")
@patch.object(
    CelestoManager,
    "_find_qemu_binary",
    return_value=Path("/opt/homebrew/bin/qemu-system-aarch64"),
)
def test_start_qemu_includes_configured_hostfwd_rules(
    _mock_find_qemu_binary: MagicMock,
    mock_popen: MagicMock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """QEMU launch should include configured user-network host forwards."""
    monkeypatch.setattr(CelestoManager, "_local_ssh_port_is_available", lambda *args: True)
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.ext4"
    kernel.touch()
    rootfs.touch()

    config = VMConfig(
        vm_id="vm-qemu1",
        kernel_path=kernel,
        rootfs_path=rootfs,
        backend="qemu",
        comm_channel="ssh",
        boot_args="console=ttyAMA0 reboot=k panic=1 init=/init",
        port_forwards=[
            PortForwardConfig(host_port=39011, guest_port=9222),
            PortForwardConfig(host_port=39012, guest_port=6080),
        ],
    )

    sdk = CelestoManager(
        data_dir=tmp_path / "data", socket_dir=tmp_path / "sockets", backend="qemu"
    )
    with patch.object(CelestoManager, "_create_qemu_overlay_disk") as mock_convert:
        mock_convert.side_effect = lambda source, target, **_kwargs: target.touch()
        vm_info = sdk.create(config)

    proc = MagicMock()
    proc.pid = 12345
    mock_popen.return_value = proc

    with patch("celesto.vm.platform.system", return_value="Darwin"):
        sdk._start_qemu(vm_info, tmp_path / "vm-qemu1.log")

    cmd = mock_popen.call_args.args[0]
    netdev_arg = cmd[cmd.index("-netdev") + 1]
    assert "hostfwd=tcp:127.0.0.1:2200-:22" in netdev_arg
    assert "hostfwd=tcp:127.0.0.1:39011-:9222" in netdev_arg
    assert "hostfwd=tcp:127.0.0.1:39012-:6080" in netdev_arg


@patch("celesto.vm.subprocess.Popen")
@patch.object(
    CelestoManager,
    "_find_qemu_binary",
    return_value=Path("/opt/homebrew/bin/qemu-system-aarch64"),
)
def test_start_qemu_uses_distinct_block_backend_and_node_names(
    _mock_find_qemu_binary: MagicMock,
    mock_popen: MagicMock,
    tmp_path: Path,
) -> None:
    """QEMU launch should not reuse the same name for backend id and block node."""
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.ext4"
    kernel.touch()
    rootfs.touch()

    config = VMConfig(
        vm_id="vm-qemu-nodes",
        kernel_path=kernel,
        rootfs_path=rootfs,
        backend="qemu",
        boot_args="console=ttyAMA0 reboot=k panic=1 init=/init",
    )

    sdk = CelestoManager(
        data_dir=tmp_path / "data", socket_dir=tmp_path / "sockets", backend="qemu"
    )
    with patch.object(CelestoManager, "_create_qemu_overlay_disk") as mock_convert:
        mock_convert.side_effect = lambda source, target, **_kwargs: target.touch()
        vm_info = sdk.create(config)

    proc = MagicMock()
    proc.pid = 12345
    mock_popen.return_value = proc

    with patch("celesto.vm.platform.system", return_value="Darwin"):
        sdk._start_qemu(vm_info, tmp_path / "vm-qemu-nodes.log")

    cmd = mock_popen.call_args.args[0]
    drive_arg = cmd[cmd.index("-drive") + 1]
    assert "id=rootdisk0-drive" in drive_arg
    assert "node-name=rootdisk0" in drive_arg
    # Rootdisk must be the LAST virtio-blk-device on aarch64 (MMIO transport
    # enumerates devices in reverse declaration order; the kernel-side /dev/vda
    # ends up being whichever virtio-blk-device was added last).
    blk_devs = [a for a in cmd if isinstance(a, str) and a.startswith("virtio-blk-device,")]
    assert blk_devs[-1] == "virtio-blk-device,drive=rootdisk0-drive"


def test_create_qemu_preserves_requested_vsock_cid(tmp_path: Path) -> None:
    """Explicit QEMU vsock config should reserve and persist the requested CID."""
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.ext4"
    kernel.touch()
    rootfs.touch()

    config = VMConfig(
        vm_id="vm-qemu-vsock",
        kernel_path=kernel,
        rootfs_path=rootfs,
        backend="qemu",
        comm_channel="vsock",
        vsock=VsockConfig(guest_cid=42, uds_path="/tmp/vm-qemu-vsock.sock"),
    )
    sdk = CelestoManager(
        data_dir=tmp_path / "data", socket_dir=tmp_path / "sockets", backend="qemu"
    )

    with (
        patch("celesto.comm.select.host_supports_vsock", return_value=True),
        patch.object(CelestoManager, "_create_qemu_overlay_disk") as mock_overlay,
    ):
        mock_overlay.side_effect = lambda source, target, **_kwargs: target.write_text("overlay")
        vm_info = sdk.create(config)

    assert vm_info.config.vsock == VsockConfig(
        guest_cid=42,
        uds_path="/tmp/vm-qemu-vsock.sock",
    )
    assert sdk.state.get_vsock_cid("vm-qemu-vsock") == 42


def test_create_qemu_auto_vsock_skips_live_qemu_cids(tmp_path: Path) -> None:
    """Automatic QEMU vsock allocation should avoid CIDs already bound by QEMU."""
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.ext4"
    kernel.touch()
    rootfs.touch()

    config = VMConfig(
        vm_id="vm-qemu-auto-vsock",
        kernel_path=kernel,
        rootfs_path=rootfs,
        backend="qemu",
        comm_channel="vsock",
    )
    sdk = CelestoManager(
        data_dir=tmp_path / "data", socket_dir=tmp_path / "sockets", backend="qemu"
    )

    with (
        patch("celesto.comm.select.host_supports_vsock", return_value=True),
        patch.object(CelestoManager, "_live_qemu_vsock_cids", return_value={3, 4, 5}),
        patch.object(CelestoManager, "_create_qemu_overlay_disk") as mock_overlay,
    ):
        mock_overlay.side_effect = lambda source, target, **_kwargs: target.write_text("overlay")
        vm_info = sdk.create(config)

    assert vm_info.config.vsock == VsockConfig(guest_cid=6)
    assert sdk.state.get_vsock_cid("vm-qemu-auto-vsock") == 6


def test_create_qemu_explicit_vsock_cid_rejects_live_qemu_conflict(tmp_path: Path) -> None:
    """Explicit QEMU CID conflicts should fail before QEMU exits at start time."""
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.ext4"
    kernel.touch()
    rootfs.touch()

    config = VMConfig(
        vm_id="vm-qemu-vsock-conflict",
        kernel_path=kernel,
        rootfs_path=rootfs,
        backend="qemu",
        comm_channel="vsock",
        vsock=VsockConfig(guest_cid=42),
    )
    sdk = CelestoManager(
        data_dir=tmp_path / "data", socket_dir=tmp_path / "sockets", backend="qemu"
    )

    with (
        patch("celesto.comm.select.host_supports_vsock", return_value=True),
        patch.object(CelestoManager, "_live_qemu_vsock_cids", return_value={42}),
        patch.object(CelestoManager, "_create_qemu_overlay_disk") as mock_overlay,
        pytest.raises(NetworkError, match="Vsock CID 42 is already in use") as exc_info,
    ):
        mock_overlay.side_effect = lambda source, target, **_kwargs: target.write_text("overlay")
        sdk.create(config)

    assert "celesto computer delete vm-qemu-vsock-conflict" in str(exc_info.value)
    assert sdk.state.get_vsock_cid("vm-qemu-vsock-conflict") is None
    with pytest.raises(VMNotFoundError):
        sdk.state.get_vm("vm-qemu-vsock-conflict")


def test_create_qemu_reserves_vsock_even_when_control_channel_is_ssh(tmp_path: Path) -> None:
    """A QEMU vsock device still needs collision-safe CID reservation with SSH control."""
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.ext4"
    kernel.touch()
    rootfs.touch()

    config = VMConfig(
        vm_id="vm-qemu-vsock-ssh",
        kernel_path=kernel,
        rootfs_path=rootfs,
        backend="qemu",
        comm_channel="ssh",
        vsock=VsockConfig(guest_cid=43),
    )
    sdk = CelestoManager(
        data_dir=tmp_path / "data", socket_dir=tmp_path / "sockets", backend="qemu"
    )

    with patch.object(CelestoManager, "_create_qemu_overlay_disk") as mock_overlay:
        mock_overlay.side_effect = lambda source, target, **_kwargs: target.write_text("overlay")
        vm_info = sdk.create(config)

    assert vm_info.config.vsock == VsockConfig(guest_cid=43)
    assert sdk.state.get_vsock_cid("vm-qemu-vsock-ssh") == 43


def test_create_qemu_uses_declared_backing_format_with_misleading_suffix(
    tmp_path: Path,
) -> None:
    """QEMU overlay creation should trust rootfs_format over the filename."""
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "raw-rootfs.qcow2"
    kernel.touch()
    rootfs.write_text("raw-ext4-data")

    config = VMConfig(
        vm_id="vm-qemu-raw-suffix",
        kernel_path=kernel,
        rootfs_path=rootfs,
        rootfs_format="raw-ext4",
        backend="qemu",
    )
    sdk = CelestoManager(
        data_dir=tmp_path / "data", socket_dir=tmp_path / "sockets", backend="qemu"
    )

    with patch.object(CelestoManager, "_create_qemu_overlay_disk") as mock_overlay:
        mock_overlay.side_effect = lambda source, target, **_kwargs: target.write_text("overlay")
        vm_info = sdk.create(config)

    assert vm_info.config.rootfs_path == sdk.data_dir / "disks" / "vm-qemu-raw-suffix.qcow2"
    assert vm_info.config.rootfs_format == "qcow2"
    assert mock_overlay.call_args.kwargs["backing_format"] == "raw"


def test_create_qemu_raw_grow_uses_managed_raw_disk(tmp_path: Path) -> None:
    """QEMU raw-ext4 grow creates a growable raw disk instead of a qcow2 overlay."""
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.img"
    kernel.touch()
    rootfs.write_bytes(b"\0" * (1024 * 1024))

    config = VMConfig(
        vm_id="vm-qemu-grow",
        kernel_path=kernel,
        rootfs_path=rootfs,
        rootfs_format="raw-ext4",
        backend="qemu",
        disk_size_mib=2,
        grow_filesystem=True,
    )
    sdk = CelestoManager(
        data_dir=tmp_path / "data", socket_dir=tmp_path / "sockets", backend="qemu"
    )

    def _copy(source: Path, target: Path) -> None:
        target.write_bytes(source.read_bytes())

    with (
        patch.object(CelestoManager, "_create_qemu_overlay_disk") as mock_overlay,
        patch.object(CelestoManager, "_copy_with_reflink", side_effect=_copy),
        patch.object(sdk, "_grow_raw_ext4_filesystem") as mock_grow,
    ):
        vm_info = sdk.create(config)

    expected_disk = sdk.data_dir / "disks" / "vm-qemu-grow.ext4"
    assert vm_info.config.rootfs_path == expected_disk
    assert vm_info.config.rootfs_format == "raw-ext4"
    assert expected_disk.stat().st_size == 2 * 1024 * 1024
    mock_overlay.assert_not_called()
    mock_grow.assert_called_once_with(expected_disk, "vm-qemu-grow")


def test_create_qemu_uses_managed_qcow2_disk(tmp_path: Path) -> None:
    """QEMU isolated disks should be materialized as managed qcow2 files."""
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.ext4"
    kernel.touch()
    rootfs.write_text("rootfs-data")

    config = VMConfig(
        vm_id="vm-qemu2",
        kernel_path=kernel,
        rootfs_path=rootfs,
        backend="qemu",
        boot_args="console=ttyAMA0 reboot=k panic=1 init=/init",
    )

    sdk = CelestoManager(
        data_dir=tmp_path / "data", socket_dir=tmp_path / "sockets", backend="qemu"
    )
    with patch.object(CelestoManager, "_create_qemu_overlay_disk") as mock_convert:
        mock_convert.side_effect = lambda source, target, **_kwargs: target.write_text(
            "managed-qcow2"
        )
        vm_info = sdk.create(config)

    expected_disk = sdk.data_dir / "disks" / "vm-qemu2.qcow2"
    assert vm_info.config.rootfs_path == expected_disk
    assert expected_disk.read_text() == "managed-qcow2"


def test_materialize_firmware_noop_for_linux_guests(tmp_path: Path) -> None:
    """Linux guests don't need per-VM OVMF NVRAM — _materialize_firmware is a no-op."""
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.ext4"
    kernel.touch()
    rootfs.touch()
    config = VMConfig(
        vm_id="vm-linux",
        kernel_path=kernel,
        rootfs_path=rootfs,
        backend="qemu",
    )

    sdk = CelestoManager(
        data_dir=tmp_path / "data",
        socket_dir=tmp_path / "sockets",
        backend="qemu",
    )
    sdk._materialize_firmware(config)
    # No firmware dir should be created for Linux VMs.
    assert not (sdk.data_dir / "firmware" / "vm-linux").exists()


def test_materialize_firmware_copies_ovmf_template_for_windows(tmp_path: Path) -> None:
    """Windows guests get a per-VM OVMF_VARS.fd copied from the system template."""
    from celesto.runtime.guest_platforms import FirmwareSpec
    from celesto.types import GuestOS

    rootfs = tmp_path / "win11.qcow2"
    rootfs.touch()

    # Fake the system OVMF template — both files have to exist for our copy.
    template = tmp_path / "OVMF_VARS_4M.ms.fd"
    template.write_bytes(b"fake-ovmf-vars-template")
    code = tmp_path / "OVMF_CODE_4M.secboot.fd"
    code.touch()
    fake_spec_firmware = FirmwareSpec(code_path=code, vars_template_path=template)

    config = VMConfig(
        vm_id="vm-win",
        kernel_path=None,
        rootfs_path=rootfs,
        backend="qemu",
        guest_os=GuestOS.WINDOWS,
        boot_mode="firmware",
        disk_mode="shared",  # don't try to overlay a Windows qcow2
    )

    sdk = CelestoManager(
        data_dir=tmp_path / "data",
        socket_dir=tmp_path / "sockets",
        backend="qemu",
    )
    with (
        patch(
            "celesto.runtime.guest_platforms._find_x86_64_ovmf",
            return_value=fake_spec_firmware,
        ),
        patch("celesto.vm.platform.system", return_value="Linux"),
        patch("celesto.vm.platform.machine", return_value="x86_64"),
    ):
        sdk._materialize_firmware(config)

    target = sdk.data_dir / "firmware" / "vm-win" / "OVMF_VARS.fd"
    assert target.exists()
    assert target.read_bytes() == b"fake-ovmf-vars-template"
    # NVRAM is locked down (owner-only) by-default.
    assert (target.stat().st_mode & 0o777) == 0o600


def test_materialize_firmware_raises_with_install_hint_when_no_ovmf(tmp_path: Path) -> None:
    """Missing OVMF gives a plain-English install hint at create time."""
    from celesto.types import GuestOS

    rootfs = tmp_path / "win11.qcow2"
    rootfs.touch()
    config = VMConfig(
        vm_id="vm-win-no-ovmf",
        kernel_path=None,
        rootfs_path=rootfs,
        backend="qemu",
        guest_os=GuestOS.WINDOWS,
        boot_mode="firmware",
        disk_mode="shared",
    )

    sdk = CelestoManager(
        data_dir=tmp_path / "data",
        socket_dir=tmp_path / "sockets",
        backend="qemu",
    )
    with (
        patch(
            "celesto.runtime.guest_platforms._find_x86_64_ovmf",
            return_value=None,
        ),
        patch("celesto.vm.platform.system", return_value="Linux"),
        patch("celesto.vm.platform.machine", return_value="x86_64"),
        pytest.raises(CelestoError, match="OVMF"),
    ):
        sdk._materialize_firmware(config)


def test_windows_local_image_uses_per_vm_overlay_disk(tmp_path: Path) -> None:
    """Windows VMs get a per-VM overlay, baseline qcow2 stays untouched."""
    from celesto.runtime.guest_platforms import FirmwareSpec
    from celesto.types import GuestOS

    baseline = tmp_path / "win11-baseline.qcow2"
    baseline.write_bytes(b"baseline-bytes")
    baseline_mtime = baseline.stat().st_mtime_ns

    code = tmp_path / "OVMF_CODE.fd"
    code.touch()
    template = tmp_path / "OVMF_VARS.fd"
    template.write_bytes(b"vars-template")
    fake_firmware = FirmwareSpec(code_path=code, vars_template_path=template)

    config = VMConfig(
        vm_id="vm-win-iso",
        kernel_path=None,
        rootfs_path=baseline,
        backend="qemu",
        guest_os=GuestOS.WINDOWS,
        boot_mode="firmware",
        disk_mode="isolated",  # Phase 3a: new default for Windows local-image
    )

    sdk = CelestoManager(
        data_dir=tmp_path / "data",
        socket_dir=tmp_path / "sockets",
        backend="qemu",
    )
    with (
        patch(
            "celesto.runtime.guest_platforms._find_x86_64_ovmf",
            return_value=fake_firmware,
        ),
        patch("celesto.vm.platform.system", return_value="Linux"),
        patch("celesto.vm.platform.machine", return_value="x86_64"),
        patch.object(CelestoManager, "_create_qemu_overlay_disk") as mock_overlay,
    ):
        mock_overlay.side_effect = lambda source, target, **_kwargs: target.write_text(
            "overlay-bytes"
        )
        vm_info = sdk.create(config)

    expected_overlay = sdk.data_dir / "disks" / "vm-win-iso.qcow2"
    # The VM now points at its own overlay, NOT the user's baseline.
    assert vm_info.config.rootfs_path == expected_overlay
    assert expected_overlay.read_text() == "overlay-bytes"
    # The user's baseline file is byte-identical AND mtime-identical —
    # nothing wrote to it, so two Celestos in parallel can share it safely.
    assert baseline.read_bytes() == b"baseline-bytes"
    assert baseline.stat().st_mtime_ns == baseline_mtime
    # The overlay was created with the baseline as the backing file.
    source_arg, target_arg = mock_overlay.call_args.args
    assert source_arg == baseline
    assert target_arg == expected_overlay


def test_two_windows_vms_from_same_baseline_get_distinct_overlays(
    tmp_path: Path,
) -> None:
    """Concurrent Windows sandboxes from the same image use separate overlays."""
    from celesto.runtime.guest_platforms import FirmwareSpec
    from celesto.types import GuestOS

    baseline = tmp_path / "win11-baseline.qcow2"
    baseline.write_bytes(b"baseline-bytes")

    code = tmp_path / "OVMF_CODE.fd"
    code.touch()
    template = tmp_path / "OVMF_VARS.fd"
    template.write_bytes(b"vars-template")
    fake_firmware = FirmwareSpec(code_path=code, vars_template_path=template)

    def _windows_config(vm_id: str) -> VMConfig:
        return VMConfig(
            vm_id=vm_id,
            kernel_path=None,
            rootfs_path=baseline,
            backend="qemu",
            guest_os=GuestOS.WINDOWS,
            boot_mode="firmware",
            disk_mode="isolated",
        )

    sdk = CelestoManager(
        data_dir=tmp_path / "data",
        socket_dir=tmp_path / "sockets",
        backend="qemu",
    )
    with (
        patch(
            "celesto.runtime.guest_platforms._find_x86_64_ovmf",
            return_value=fake_firmware,
        ),
        patch("celesto.vm.platform.system", return_value="Linux"),
        patch("celesto.vm.platform.machine", return_value="x86_64"),
        patch.object(CelestoManager, "_create_qemu_overlay_disk") as mock_overlay,
    ):
        mock_overlay.side_effect = lambda source, target, **_kwargs: target.write_text(target.name)
        vm_alpha = sdk.create(_windows_config("vm-win-alpha"))
        vm_beta = sdk.create(_windows_config("vm-win-beta"))

    # Distinct per-VM overlays.
    assert vm_alpha.config.rootfs_path != vm_beta.config.rootfs_path
    assert vm_alpha.config.rootfs_path.name == "vm-win-alpha.qcow2"
    assert vm_beta.config.rootfs_path.name == "vm-win-beta.qcow2"
    # Both overlays share the same backing file (the user's baseline).
    backing_paths = [call.args[0] for call in mock_overlay.call_args_list]
    assert backing_paths == [baseline, baseline]


def test_delete_qemu_retains_isolated_disk_when_enabled(tmp_path: Path) -> None:
    """retain_disk_on_delete should preserve managed qcow2 disks for QEMU VMs."""
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.ext4"
    kernel.touch()
    rootfs.write_text("rootfs-data")

    config = VMConfig(
        vm_id="vm-qemu3",
        kernel_path=kernel,
        rootfs_path=rootfs,
        backend="qemu",
        boot_args="console=ttyAMA0 reboot=k panic=1 init=/init",
        retain_disk_on_delete=True,
    )

    sdk = CelestoManager(
        data_dir=tmp_path / "data", socket_dir=tmp_path / "sockets", backend="qemu"
    )
    with patch.object(CelestoManager, "_create_qemu_overlay_disk") as mock_convert:
        mock_convert.side_effect = lambda source, target, **_kwargs: target.write_text(
            "managed-qcow2"
        )
        sdk.create(config)

    disk_path = sdk.data_dir / "disks" / "vm-qemu3.qcow2"
    sdk.delete("vm-qemu3")

    assert disk_path.exists()


# ---------------------------------------------------------------------------
# How stop and delete end the QEMU process.
#
# On SIGTERM, QEMU writes every disk's cached data to the host before it
# exits. On a busy host that takes longer than the 10 s stop timeout. Delete
# removes the disk right after, so it kills QEMU at once instead, but only
# when no file QEMU writes outlives the delete.
#
# Ways this can break, and the test that catches each:
# - delete (sync or async) still sends SIGTERM and waits for the flush
#   -> test_delete_kills_qemu_at_once_when_its_disk_is_deleted
# - delete returns before QEMU has exited, so its resources (such as the
#   vsock address) are reused while QEMU still holds them -> same test
#   (the process must already be reaped when delete returns)
# - a kill that QEMU survives no longer raises -> tests/runtime/test_runtime_qemu.py
# - a plain stop loses its SIGTERM -> test_stop_still_lets_qemu_flush_before_it_exits
# - a delete that keeps data kills QEMU at once
#   -> test_delete_stops_qemu_gracefully_when_its_data_outlives_the_delete
#
# A real child process stands in for QEMU so the real signal, wait and reap
# code runs. Only the QEMU launch itself is skipped.
# ---------------------------------------------------------------------------

# Stand-in for QEMU. On SIGTERM it records the signal in argv[1], then takes
# argv[2] seconds to exit, like QEMU writing its disk caches to the host.
_FAKE_QEMU_SCRIPT = """
import pathlib, signal, sys, time

def on_sigterm(_signum, _frame):
    pathlib.Path(sys.argv[1]).write_text("SIGTERM")
    time.sleep(float(sys.argv[2]))
    sys.exit(0)

signal.signal(signal.SIGTERM, on_sigterm)
print("ready", flush=True)
while True:
    time.sleep(60)
"""

FakeQemu = Callable[..., tuple[subprocess.Popen[bytes], Path]]


@pytest.fixture
def fake_qemu(tmp_path: Path) -> Iterator[FakeQemu]:
    """Return a helper that marks a VM as running on a QEMU stand-in process.

    The helper returns the process and the file it writes when it receives
    SIGTERM. Any process a failed test leaves behind is killed at teardown.
    """
    processes: list[subprocess.Popen[bytes]] = []

    def run(
        sdk: CelestoManager, vm_id: str, *, flush_seconds: float
    ) -> tuple[subprocess.Popen[bytes], Path]:
        sigterm_marker = tmp_path / f"{vm_id}.sigterm"
        process = subprocess.Popen(
            [
                sys.executable,
                "-I",
                "-c",
                _FAKE_QEMU_SCRIPT,
                str(sigterm_marker),
                str(flush_seconds),
            ],
            stdout=subprocess.PIPE,
        )
        processes.append(process)
        # Wait until the SIGTERM handler is installed; a SIGTERM before that
        # would end the process without writing the marker.
        assert process.stdout is not None
        assert process.stdout.readline() == b"ready\n"
        process.stdout.close()
        # The manager reaps the processes it launched through these handles.
        sdk._process_handles[process.pid] = process
        sdk.state.update_vm(vm_id, status=VMState.RUNNING, pid=process.pid)
        return process, sigterm_marker

    yield run

    for process in processes:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)


def _create_qemu_vm(sdk: CelestoManager, tmp_path: Path, vm_id: str, **config: Any) -> None:
    """Create a QEMU VM record without building a real disk image."""
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.ext4"
    kernel.touch()
    rootfs.write_text("rootfs-data")
    with patch.object(CelestoManager, "_create_qemu_overlay_disk") as mock_overlay:
        mock_overlay.side_effect = lambda _source, target, **_kwargs: target.write_text(
            "managed-qcow2"
        )
        sdk.create(
            VMConfig(
                vm_id=vm_id,
                kernel_path=kernel,
                rootfs_path=rootfs,
                backend="qemu",
                boot_args="console=ttyAMA0 reboot=k panic=1 init=/init",
                **config,
            )
        )


def _qemu_manager(tmp_path: Path) -> CelestoManager:
    return CelestoManager(
        data_dir=tmp_path / "data", socket_dir=tmp_path / "sockets", backend="qemu"
    )


@pytest.mark.parametrize("call", ["delete", "async_delete"])
def test_delete_kills_qemu_at_once_when_its_disk_is_deleted(
    tmp_path: Path, fake_qemu: FakeQemu, call: str
) -> None:
    """Delete skips QEMU's exit flush when the disk it would flush is removed."""
    sdk = _qemu_manager(tmp_path)
    _create_qemu_vm(sdk, tmp_path, "vm-del-fast")
    disk = sdk.data_dir / "disks" / "vm-del-fast.qcow2"
    assert disk.exists()
    # A 30 s flush makes a graceful stop obvious: delete would wait 10 s first.
    process, sigterm_marker = fake_qemu(sdk, "vm-del-fast", flush_seconds=30)

    if call == "async_delete":
        asyncio.run(sdk.async_delete("vm-del-fast"))
    else:
        sdk.delete("vm-del-fast")

    assert not sigterm_marker.exists(), "QEMU was asked to exit gracefully"
    # returncode is set only once the manager has reaped the process, so this
    # also proves delete waited for QEMU to exit before it returned.
    assert process.returncode == -signal.SIGKILL
    assert not disk.exists()
    with pytest.raises(VMNotFoundError):
        sdk.get("vm-del-fast")


def _retain_the_disk(tmp_path: Path) -> dict[str, Any]:
    return {"retain_disk_on_delete": True}


def _share_the_rootfs(tmp_path: Path) -> dict[str, Any]:
    return {"disk_mode": "shared"}


def _keep_an_extra_drive(tmp_path: Path) -> dict[str, Any]:
    drive = tmp_path / "data-drive.raw"
    drive.write_text("user-data")
    return {"extra_drives": [drive]}


def _keep_a_writable_shared_folder(tmp_path: Path) -> dict[str, Any]:
    folder = tmp_path / "workspace"
    folder.mkdir()
    return {"workspace_mounts": [WorkspaceMount(host_path=folder, writable=True)]}


@pytest.mark.parametrize("call", ["delete", "async_delete"])
@pytest.mark.parametrize(
    "kept_data",
    [
        pytest.param(_retain_the_disk, id="retain_disk_on_delete"),
        pytest.param(_share_the_rootfs, id="shared_disk"),
        pytest.param(_keep_an_extra_drive, id="extra_drive"),
        pytest.param(_keep_a_writable_shared_folder, id="writable_shared_folder"),
        pytest.param(None, id="disk_marked_as_kept"),
    ],
)
def test_delete_stops_qemu_gracefully_when_its_data_outlives_the_delete(
    tmp_path: Path,
    fake_qemu: FakeQemu,
    kept_data: Callable[[Path], dict[str, Any]] | None,
    call: str,
) -> None:
    """Delete keeps the graceful stop whenever a file QEMU writes survives it.

    QEMU's exit flush is what puts its cached writes into those files.
    """
    sdk = _qemu_manager(tmp_path)
    _create_qemu_vm(sdk, tmp_path, "vm-del-keep", **(kept_data(tmp_path) if kept_data else {}))
    if kept_data is None:
        # A disk marked as kept survives delete even without retain_disk_on_delete.
        disk = sdk.data_dir / "disks" / "vm-del-keep.qcow2"
        sdk._mark_disk_retained(disk)
    process, sigterm_marker = fake_qemu(sdk, "vm-del-keep", flush_seconds=0.2)

    if call == "async_delete":
        asyncio.run(sdk.async_delete("vm-del-keep"))
    else:
        sdk.delete("vm-del-keep")

    assert sigterm_marker.read_text() == "SIGTERM"
    # The stand-in finished its flush and exited on its own.
    assert process.returncode == 0


@pytest.mark.parametrize("call", ["stop", "async_stop"])
def test_stop_still_lets_qemu_flush_before_it_exits(
    tmp_path: Path, fake_qemu: FakeQemu, call: str
) -> None:
    """A plain stop keeps the disk, so QEMU must still flush it on SIGTERM."""
    sdk = _qemu_manager(tmp_path)
    # The same VM shape that delete kills at once.
    _create_qemu_vm(sdk, tmp_path, "vm-stop")
    process, sigterm_marker = fake_qemu(sdk, "vm-stop", flush_seconds=0.2)

    if call == "async_stop":
        asyncio.run(sdk.async_stop("vm-stop"))
    else:
        sdk.stop("vm-stop")

    assert sigterm_marker.read_text() == "SIGTERM"
    assert process.returncode == 0
    assert sdk.get("vm-stop").status == VMState.STOPPED
    assert (sdk.data_dir / "disks" / "vm-stop.qcow2").exists()

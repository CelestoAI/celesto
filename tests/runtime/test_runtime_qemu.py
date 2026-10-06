"""Unit tests for the QEMU runtime adapter."""

import subprocess
from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from celesto.exceptions import CelestoError
from celesto.runtime.base import RuntimeContext
from celesto.runtime.guest_platforms import GuestPlatformSpec
from celesto.runtime.qemu import QemuRuntimeAdapter, _SwtpmSidecar
from celesto.types import GuestOS, NetworkConfig, VMConfig, VMInfo, VMState


def _make_context() -> RuntimeContext:
    """Build a minimal runtime context with mockable process hooks."""
    return RuntimeContext(
        data_dir=Path("/tmp/data"),
        socket_dir=Path("/tmp"),
        firmware_dir=Path("/tmp/data/firmware"),
        log_files={},
        process_handles={},
        resolve_boot_args=lambda vm_info: vm_info.config.boot_args,
        start_firecracker=MagicMock(),
        start_qemu=MagicMock(),
        unlink_socket=MagicMock(),
        kill_process=MagicMock(),
        wait_for_process=MagicMock(),
        is_process_running=MagicMock(),
        find_qemu_binary=MagicMock(),
    )


def _make_vm_info(tmp_path: Path, *, pid: int = 12345) -> VMInfo:
    """Create a minimal QEMU-backed VMInfo for adapter tests."""
    kernel = tmp_path / "vmlinux"
    rootfs = tmp_path / "rootfs.ext4"
    socket_path = tmp_path / "qmp.sock"
    kernel.touch()
    rootfs.touch()
    socket_path.touch()

    return VMInfo(
        vm_id="vm-qemu-stop",
        status=VMState.RUNNING,
        config=VMConfig(
            vm_id="vm-qemu-stop",
            kernel_path=kernel,
            rootfs_path=rootfs,
            backend="qemu",
            boot_args="console=ttyAMA0 reboot=k panic=1 init=/init",
        ),
        network=NetworkConfig(
            guest_ip="10.0.2.15",
            gateway_ip="10.0.2.2",
            netmask="255.255.255.0",
            tap_device="usernet",
            guest_mac="aa:fc:00:00:00:01",
            ssh_host_port=2200,
        ),
        pid=pid,
        control_socket_path=socket_path,
    )


def test_stop_waits_for_hard_kill_before_releasing_socket(tmp_path: Path) -> None:
    """Forced QEMU termination should wait for exit before cleanup proceeds."""
    context = _make_context()
    context.is_process_running.side_effect = [True, True, False]
    adapter = QemuRuntimeAdapter(context)
    vm_info = _make_vm_info(tmp_path)

    with patch("os.kill") as mock_os_kill:
        adapter.stop(vm_info, timeout=10.0)

    mock_os_kill.assert_called_once()
    context.kill_process.assert_called_once_with(vm_info.pid)
    assert context.wait_for_process.call_args_list == [
        call(vm_info.pid, 10.0),
        call(vm_info.pid, 5.0),
    ]
    context.unlink_socket.assert_called_once_with(vm_info.control_socket_path)


def test_stop_raises_when_qemu_survives_hard_kill(tmp_path: Path) -> None:
    """Cleanup should fail loudly if the QEMU process still has not exited."""
    context = _make_context()
    context.is_process_running.side_effect = [True, True, True]
    adapter = QemuRuntimeAdapter(context)
    vm_info = _make_vm_info(tmp_path)

    with patch("os.kill") as mock_os_kill, pytest.raises(CelestoError, match="did not exit"):
        adapter.stop(vm_info, timeout=10.0)

    mock_os_kill.assert_called_once()
    context.kill_process.assert_called_once_with(vm_info.pid)
    assert context.wait_for_process.call_args_list == [
        call(vm_info.pid, 10.0),
        call(vm_info.pid, 5.0),
    ]
    context.unlink_socket.assert_not_called()


def test_qcow2_backing_inspection_force_shares_running_qemu_disk(tmp_path: Path) -> None:
    """Inspecting a paused-but-open QEMU disk must bypass qemu-img's image lock."""
    disk = tmp_path / "vm.qcow2"
    disk.touch()
    result = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout='{"full-backing-filename": "/tmp/base.qcow2"}',
        stderr="",
    )

    with (
        patch("celesto.runtime.qemu.which", return_value=Path("/usr/bin/qemu-img")),
        patch("celesto.runtime.qemu.subprocess.run", return_value=result) as mock_run,
    ):
        backing = QemuRuntimeAdapter._qcow2_backing_file_required(disk)

    assert backing == Path("/tmp/base.qcow2")
    mock_run.assert_called_once_with(
        ["/usr/bin/qemu-img", "info", "-U", "--output=json", str(disk)],
        capture_output=True,
        text=True,
        check=False,
    )


# --- swtpm sidecar lifecycle, as driven by QemuRuntimeAdapter.start() ---------
#
# Windows guests need a per-VM swtpm (software TPM) sidecar. The adapter owns
# it: start() spawns it before QEMU, and every failure after that point has to
# reap it, otherwise the daemon (and its socket + pidfile) outlives the failed
# launch. The tests below drive the real adapter method with a fake swtpm.


_WINDOWS_SW_SPEC = GuestPlatformSpec(
    guest_os=GuestOS.WINDOWS,
    name="windows",
    requires_swtpm=True,
)
"""A Windows spec that only asserts ``requires_swtpm``.

Firmware is left unset so ``_firmware_vars_path`` returns None and the adapter
never touches OVMF files. Patching the spec factory (rather than the adapter)
keeps ``_resolve_platform_spec`` itself under test and makes these tests
host-independent: the real Windows spec is unavailable off a Linux x86_64 host.
"""


def _make_swtpm_context(tmp_path: Path) -> RuntimeContext:
    """Runtime context whose swtpm state dirs live under *tmp_path*."""
    return RuntimeContext(
        data_dir=tmp_path / "data",
        socket_dir=tmp_path / "sockets",
        firmware_dir=tmp_path / "firmware",
        log_files={},
        process_handles={},
        resolve_boot_args=lambda vm_info: vm_info.config.boot_args,
        start_firecracker=MagicMock(),
        start_qemu=MagicMock(),
        unlink_socket=MagicMock(),
        kill_process=MagicMock(),
        wait_for_process=MagicMock(),
        is_process_running=MagicMock(),
        find_qemu_binary=MagicMock(),
    )


def _make_windows_vm_info(tmp_path: Path) -> VMInfo:
    """Create a Windows-guest VMInfo, which is what pulls in the swtpm sidecar."""
    rootfs = tmp_path / "windows.qcow2"
    rootfs.touch()

    return VMInfo(
        vm_id="vm-qemu-win",
        status=VMState.STOPPED,
        config=VMConfig(
            vm_id="vm-qemu-win",
            rootfs_path=rootfs,
            backend="qemu",
            boot_mode="firmware",
            guest_os=GuestOS.WINDOWS,
        ),
        network=NetworkConfig(
            guest_ip="10.0.2.15",
            gateway_ip="10.0.2.2",
            netmask="255.255.255.0",
            tap_device="usernet",
            guest_mac="aa:fc:00:00:00:02",
            ssh_host_port=2201,
        ),
        pid=None,
        control_socket_path=tmp_path / "qmp.sock",
    )


def _fake_swtpm(
    context: RuntimeContext,
    vm_id: str,
    *,
    pid: int,
    create_socket: bool,
) -> Callable[..., subprocess.CompletedProcess[str]]:
    """Build a ``swtpm socket --daemon`` stand-in.

    swtpm daemonises, so the subprocess returns immediately and the sidecar
    discovers its child by watching for the socket and pidfile. *create_socket*
    False models the daemon that forks and writes its pidfile but never opens
    its control socket.
    """
    sidecar = _SwtpmSidecar(vm_id=vm_id, firmware_dir=context.firmware_dir, context=context)

    def run(cmd: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        sidecar.pidfile_path.write_text(f"{pid}\n")
        if create_socket:
            sidecar.socket_path.touch()
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

    return run


def _stepping_monotonic() -> Callable[[], float]:
    """A ``time.monotonic`` replacement that jumps ~1s per call.

    The sidecar waits up to 5s for its socket; advancing the clock per read
    keeps every deadline loop making progress without spending real seconds.
    """
    state = {"now": 0.0}

    def monotonic() -> float:
        state["now"] += 1.0
        return state["now"]

    return monotonic


def test_start_stops_swtpm_when_its_control_socket_never_appears(tmp_path: Path) -> None:
    """A swtpm that forks but never opens its socket must still be reaped.

    Regression guard: the sidecar start used to sit outside the adapter's
    try/except, so this failure escaped the cleanup handler and left the
    swtpm daemon running with its socket and pidfile on disk.
    """
    context = _make_swtpm_context(tmp_path)
    adapter = QemuRuntimeAdapter(context)
    vm_info = _make_windows_vm_info(tmp_path)
    swtpm_pid = 51501

    # Alive for the SIGTERM, then gone for the post-signal wait and the
    # SIGKILL re-check (a SIGKILL here would fail assert_called_once).
    context.is_process_running.side_effect = [True, False, False]

    with (
        patch("celesto.runtime.qemu.get_guest_platform", return_value=_WINDOWS_SW_SPEC),
        patch("celesto.runtime.qemu.which", return_value=Path("/usr/bin/swtpm")),
        patch(
            "celesto.runtime.qemu.subprocess.run",
            side_effect=_fake_swtpm(context, vm_info.vm_id, pid=swtpm_pid, create_socket=False),
        ),
        patch("celesto.runtime.qemu.time.monotonic", side_effect=_stepping_monotonic()),
        patch("celesto.runtime.qemu.os.kill") as mock_kill,
        pytest.raises(CelestoError, match="socket never appeared"),
    ):
        adapter.start(vm_info, log_path=tmp_path / "qemu.log", boot_timeout=1.0)

    # QEMU was never reached, so only the sidecar needed tearing down.
    context.start_qemu.assert_not_called()
    mock_kill.assert_called_once()
    assert mock_kill.call_args.args[0] == swtpm_pid

    sidecar = _SwtpmSidecar(vm_id=vm_info.vm_id, firmware_dir=context.firmware_dir, context=context)
    assert not sidecar.pidfile_path.exists()
    assert not sidecar.socket_path.exists()


def test_start_stops_swtpm_when_qemu_fails_to_boot(tmp_path: Path) -> None:
    """A QEMU boot failure still reaps the sidecar it was started alongside."""
    context = _make_swtpm_context(tmp_path)
    adapter = QemuRuntimeAdapter(context)
    vm_info = _make_windows_vm_info(tmp_path)
    swtpm_pid = 51502
    context.start_qemu.return_value = MagicMock(pid=4242)
    context.is_process_running.side_effect = [True, False, False]

    with (
        patch("celesto.runtime.qemu.get_guest_platform", return_value=_WINDOWS_SW_SPEC),
        patch("celesto.runtime.qemu.which", return_value=Path("/usr/bin/swtpm")),
        patch(
            "celesto.runtime.qemu.subprocess.run",
            side_effect=_fake_swtpm(context, vm_info.vm_id, pid=swtpm_pid, create_socket=True),
        ),
        patch.object(
            QemuRuntimeAdapter,
            "_wait_for_runtime",
            side_effect=CelestoError("Timed out waiting for QEMU control socket"),
        ),
        patch("celesto.runtime.qemu.os.kill") as mock_kill,
        pytest.raises(CelestoError, match="Timed out waiting"),
    ):
        adapter.start(vm_info, log_path=tmp_path / "qemu.log", boot_timeout=1.0)

    context.kill_process.assert_called_once_with(4242)
    mock_kill.assert_called_once()
    assert mock_kill.call_args.args[0] == swtpm_pid

    sidecar = _SwtpmSidecar(vm_id=vm_info.vm_id, firmware_dir=context.firmware_dir, context=context)
    assert not sidecar.pidfile_path.exists()
    assert not sidecar.socket_path.exists()


def test_start_leaves_swtpm_running_when_the_launch_succeeds(tmp_path: Path) -> None:
    """A successful launch must hand the live sidecar over to the running VM."""
    context = _make_swtpm_context(tmp_path)
    adapter = QemuRuntimeAdapter(context)
    vm_info = _make_windows_vm_info(tmp_path)
    swtpm_pid = 51503
    context.start_qemu.return_value = MagicMock(pid=4242)

    with (
        patch("celesto.runtime.qemu.get_guest_platform", return_value=_WINDOWS_SW_SPEC),
        patch("celesto.runtime.qemu.which", return_value=Path("/usr/bin/swtpm")),
        patch(
            "celesto.runtime.qemu.subprocess.run",
            side_effect=_fake_swtpm(context, vm_info.vm_id, pid=swtpm_pid, create_socket=True),
        ),
        patch.object(QemuRuntimeAdapter, "_wait_for_runtime"),
        patch("celesto.runtime.qemu.os.kill") as mock_kill,
    ):
        launch = adapter.start(vm_info, log_path=tmp_path / "qemu.log", boot_timeout=1.0)

    assert launch.pid == 4242
    # QEMU was handed the sidecar's socket, so it must survive the launch.
    assert context.start_qemu.call_args.kwargs["swtpm_socket"].name == "swtpm-sock"
    mock_kill.assert_not_called()
    context.kill_process.assert_not_called()

    sidecar = _SwtpmSidecar(vm_id=vm_info.vm_id, firmware_dir=context.firmware_dir, context=context)
    assert sidecar.pidfile_path.read_text().strip() == str(swtpm_pid)
    assert sidecar.socket_path.exists()

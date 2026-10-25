"""Public browser egress is installed before a VM starts and remains owned."""

from __future__ import annotations

import asyncio
import socket
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from celesto._network_policy import validate_network_policy_options
from celesto.exceptions import ValidationError
from celesto.runtime.guest_platforms import _LINUX_SPEC
from celesto.runtime.qemu_args import build_qemu_argv
from celesto.types import InternetSettings, NetworkConfig, VMConfig, VMInfo, VMState
from celesto.vm import CelestoManager


@pytest.mark.parametrize("async_lifecycle", [False, True])
@pytest.mark.parametrize(
    "fail_launch,cleanup",
    [(False, "close"), ("runtime", "close"), ("persistence", "close")]
    + [("persistence_cleanup", action) for action in ("close", "stop", "delete")],
)
def test_public_proxy_owns_vm_launch_and_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    async_lifecycle: bool,
    fail_launch: bool | str,
    cleanup: str,
) -> None:
    kernel, disk = tmp_path / "kernel", tmp_path / "disk"
    kernel.touch()
    disk.touch()
    manager = CelestoManager(data_dir=tmp_path / "state", backend="qemu")
    config = VMConfig(
        vm_id="public-test",
        backend="qemu",
        kernel_path=kernel,
        rootfs_path=disk,
        internet_settings=InternetSettings(mode="public"),
    )
    manager.state.create_vm(config)
    manager.state.update_vm(
        config.vm_id,
        network=NetworkConfig(
            guest_ip="10.0.2.15",
            gateway_ip="10.0.2.2",
            tap_device="usernet",
            guest_mac="52:54:00:12:34:56",
        ),
    )
    ports: list[int] = []

    def start(info: VMInfo, **_kwargs: object) -> SimpleNamespace:
        assert info.network is not None
        port = info.network.egress_proxy_host_port
        assert port is not None
        ports.append(port)
        argv = build_qemu_argv(
            info,
            qemu_bin=Path("/usr/bin/qemu-system-x86_64"),
            boot_args=config.boot_args,
            platform_spec=_LINUX_SPEC,
            host_system="Linux",
        )
        net = argv[argv.index("-netdev") + 1]
        assert "restrict=on" in net and "ipv6=off" in net
        assert "guestfwd=tcp:10.0.2.100:3128-cmd:" in net
        assert f"_public_egress_relay.py {port}" in net
        with socket.create_connection(("127.0.0.1", port), timeout=2) as connection:
            connection.sendall(
                b"GET http://127.0.0.1:9223/json HTTP/1.1\r\nHost: 127.0.0.1:9223\r\n\r\n"
            )
            assert connection.recv(4096).startswith(b"HTTP/1.1 403")
        if fail_launch == "runtime":
            raise RuntimeError("simulated launch failure")
        return SimpleNamespace(
            status=VMState.RUNNING, pid=12345, control_socket_path=None, display=None
        )

    async def async_start(info: VMInfo, **kwargs: object) -> SimpleNamespace:
        return start(info, **kwargs)

    stopped: list[str] = []

    def stop(info: VMInfo, **_kwargs: object) -> None:
        # Runtime teardown must precede release of the private proxy listener,
        # including when saving the launched runtime fails.
        assert info.pid == 12345
        assert info.network is not None and info.network.egress_proxy_host_port is not None
        with socket.create_connection(
            ("127.0.0.1", info.network.egress_proxy_host_port), timeout=1
        ):
            stopped.append(info.vm_id)
        if fail_launch == "persistence_cleanup" and len(stopped) <= (
            1 if cleanup == "close" else 2
        ):
            raise RuntimeError("simulated launch cleanup failure")

    async def async_stop(info: VMInfo, **kwargs: object) -> None:
        stop(info, **kwargs)

    adapter = SimpleNamespace(
        start=start, async_start=async_start, stop=stop, async_stop=async_stop
    )
    monkeypatch.setattr(manager, "_runtime_adapter_for_backend", lambda _backend: adapter)
    monkeypatch.setattr(manager, "_check_qemu_slirp_host_forward_ports", lambda _info: None)
    if fail_launch in {"persistence", "persistence_cleanup"}:
        update_vm = manager.state.update_vm

        def fail_running_save(vm_id: str, **kwargs: Any) -> VMInfo:
            if kwargs.get("status") == VMState.RUNNING:
                raise RuntimeError("simulated launch persistence failure")
            return update_vm(vm_id, **kwargs)

        monkeypatch.setattr(manager.state, "update_vm", fail_running_save)
    try:

        def launch() -> VMInfo:
            return (
                asyncio.run(manager.async_start(config.vm_id))
                if async_lifecycle
                else manager.start(config.vm_id)
            )

        if fail_launch:
            with pytest.raises(RuntimeError, match="simulated launch"):
                launch()
            if fail_launch in {"persistence", "persistence_cleanup"}:
                assert stopped == [config.vm_id]
            if fail_launch == "persistence_cleanup":
                with socket.create_connection(("127.0.0.1", ports[-1]), timeout=1):
                    pass  # reserve the listener until close retries failed runtime teardown
                if cleanup != "close":

                    def cleanup_pending() -> None:
                        method = getattr(manager, ("async_" if async_lifecycle else "") + cleanup)
                        result = method(config.vm_id)
                        if async_lifecycle:
                            asyncio.run(result)

                    with pytest.raises(RuntimeError, match="simulated launch cleanup failure"):
                        cleanup_pending()
                    assert config.vm_id in manager._unrecorded_public_launches
                    with socket.create_connection(("127.0.0.1", ports[-1]), timeout=1):
                        pass
                    cleanup_pending()
                    assert config.vm_id not in manager._unrecorded_public_launches
                    assert stopped == [config.vm_id] * 3
        else:
            launch()
            if async_lifecycle:
                asyncio.run(manager.async_stop(config.vm_id))
            else:
                manager.stop(config.vm_id)
            launch()  # restarting owns a fresh listener, never trusts persisted port metadata
    finally:
        manager.close()
    assert ports
    for port in ports:
        with pytest.raises(OSError):
            socket.create_connection(("127.0.0.1", port), timeout=0.2)


@pytest.mark.parametrize(
    "backend,network", [("firecracker", "slirp"), ("libkrun", "slirp"), ("qemu", "tap")]
)
def test_public_egress_rejects_unenforced_backends(backend: str, network: str) -> None:
    with pytest.raises(ValidationError, match="public.*QEMU"):
        validate_network_policy_options(
            InternetSettings(mode="public"),
            backend=backend,
            guest_os="ubuntu",
            qemu_network=network,
        )


@pytest.mark.parametrize("option", ["has_mounts", "has_forwards"])
def test_public_egress_rejects_extra_host_capabilities(option: str) -> None:
    with pytest.raises(ValidationError, match="public.*shared folders|public.*exposed ports"):
        validate_network_policy_options(
            InternetSettings(mode="public"),
            backend="qemu",
            guest_os="ubuntu",
            has_mounts=option == "has_mounts",
            has_forwards=option == "has_forwards",
        )


def test_cancelled_public_launch_waits_for_runtime_and_stops_before_releasing_proxy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    kernel, disk = tmp_path / "kernel", tmp_path / "disk"
    kernel.touch()
    disk.touch()
    manager = CelestoManager(data_dir=tmp_path / "state", backend="qemu")
    config = VMConfig(
        vm_id="cancel-public",
        backend="qemu",
        kernel_path=kernel,
        rootfs_path=disk,
        internet_settings=InternetSettings(mode="public"),
    )
    manager.state.create_vm(config)
    manager.state.update_vm(
        config.vm_id,
        network=NetworkConfig(
            guest_ip="10.0.2.15",
            gateway_ip="10.0.2.2",
            tap_device="usernet",
            guest_mac="52:54:00:12:34:56",
        ),
    )
    stopped: list[str] = []

    async def scenario() -> None:
        starting, finish = asyncio.Event(), asyncio.Event()

        async def start(info: VMInfo, **_kwargs: object) -> SimpleNamespace:
            starting.set()
            await finish.wait()
            return SimpleNamespace(
                status=VMState.RUNNING, pid=12345, control_socket_path=None, display=None
            )

        async def stop(info: VMInfo, **_kwargs: object) -> None:
            # The listener must still be reserved until the guest is stopped.
            assert info.network is not None and info.network.egress_proxy_host_port is not None
            with socket.create_connection(
                ("127.0.0.1", info.network.egress_proxy_host_port), timeout=1
            ):
                stopped.append(info.vm_id)

        monkeypatch.setattr(
            manager,
            "_runtime_adapter_for_backend",
            lambda _backend: SimpleNamespace(async_start=start, async_stop=stop),
        )
        monkeypatch.setattr(manager, "_check_qemu_slirp_host_forward_ports", lambda _info: None)
        task = asyncio.create_task(manager.async_start(config.vm_id))
        await starting.wait()
        task.cancel()
        finish.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert stopped == [config.vm_id]
        assert manager.get(config.vm_id).status == VMState.STOPPED

    try:
        asyncio.run(scenario())
    finally:
        manager.close()

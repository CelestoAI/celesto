"""Public browser egress is installed before a VM starts and remains owned."""

from __future__ import annotations

import asyncio
import json
import socket
import subprocess
import sys
import threading
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from celesto._network_policy import validate_network_policy_options
from celesto.exceptions import CelestoError, ValidationError
from celesto.runtime.guest_platforms import _LINUX_SPEC
from celesto.runtime.qemu import QemuRuntimeAdapter
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


@pytest.mark.parametrize("fail_stop", [False, True])
def test_cancelled_public_launch_waits_for_runtime_and_stops_before_releasing_proxy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fail_stop: bool
) -> None:
    """Cancelled startup keeps its listener and PID when termination fails.

    The interrupted adapter test fails before persistence; this case reaches
    cancellation cleanup after the running process has already been saved.
    """
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
        termination_denied = fail_stop

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
                if termination_denied:
                    raise RuntimeError("test termination denied")
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
        if fail_stop:
            with pytest.raises(RuntimeError, match="termination denied"):
                await task
            retained = manager.get(config.vm_id)
            try:
                assert retained.network is not None
                assert retained.network.egress_proxy_host_port is not None
                with socket.create_connection(
                    ("127.0.0.1", retained.network.egress_proxy_host_port), timeout=1
                ):
                    pass
                assert retained.pid == 12345 and retained.status == VMState.RUNNING
                assert not stopped
            finally:
                termination_denied = False
                await manager.async_stop(config.vm_id)
        else:
            with pytest.raises(asyncio.CancelledError):
                await task
        assert stopped == [config.vm_id]
        assert manager.get(config.vm_id).status == VMState.STOPPED
        (tmp_path / "cancelled-start.json").write_text(
            json.dumps({"termination_initially_denied": fail_stop, "stopped": stopped})
        )

    try:
        asyncio.run(scenario())
    finally:
        manager.close()


@pytest.fixture
def public_runtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[tuple[CelestoManager, str, list[subprocess.Popen[bytes]]]]:
    """Run the actual manager/runtime/proxy with a sleeping process in place of QEMU."""
    kernel, disk = tmp_path / "kernel", tmp_path / "disk"
    kernel.touch()
    disk.touch()
    manager = CelestoManager(
        data_dir=tmp_path / "state", socket_dir=tmp_path / "sockets", backend="qemu"
    )
    config = VMConfig(
        vm_id="starting-public",
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
    children: list[subprocess.Popen[bytes]] = []
    real_popen = subprocess.Popen

    def launch(command: list[str], **kwargs: Any) -> subprocess.Popen[bytes]:
        if command[0] != sys.executable:
            return real_popen(command, **kwargs)
        process = real_popen([sys.executable, "-c", "import time; time.sleep(30)"], **kwargs)
        children.append(process)
        return process

    monkeypatch.setattr(manager, "_find_qemu_binary", lambda: Path(sys.executable))
    monkeypatch.setattr("celesto.vm.subprocess.Popen", launch)
    try:
        yield manager, config.vm_id, children
    finally:
        for process in children:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=5)
        manager.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("second_start", ["async", "thread"])
async def test_concurrent_start_preserves_the_first_public_runtime(
    public_runtime: tuple[CelestoManager, str, list[subprocess.Popen[bytes]]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    second_start: str,
) -> None:
    """A second caller cannot replace a booting guest's proxy or lose its PID.

    Existing lifecycle tests start one guest at a time. Real subprocesses and
    proxy sockets expose the ownership race; only QMP readiness is held back.
    """
    manager, vm_id, children = public_runtime
    starting, finish = threading.Event(), threading.Event()

    def wait_for_runtime(_self: object, *_args: object) -> None:
        starting.set()
        if len(children) == 1:
            assert finish.wait(timeout=5), "test did not release the first launch"

    monkeypatch.setattr(QemuRuntimeAdapter, "_wait_for_runtime", wait_for_runtime)
    first = asyncio.create_task(manager.async_start(vm_id))
    try:
        assert await asyncio.to_thread(starting.wait, 5), "first runtime did not launch"
        original = manager.get(vm_id)
        assert original.network is not None
        port = original.network.egress_proxy_host_port
        assert port is not None
        with pytest.raises(CelestoError):
            if second_start == "thread":
                await asyncio.to_thread(manager.start, vm_id)
            else:
                await manager.async_start(vm_id)
        assert len(children) == 1
        current = manager.get(vm_id)
        assert current.network is not None
        assert current.network.egress_proxy_host_port == port
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            pass
    finally:
        finish.set()
        result = await first
        (tmp_path / "concurrent-start.json").write_text(
            json.dumps({"second_start": second_start, "children": [p.pid for p in children]})
        )
    assert result.pid == children[0].pid
    with pytest.raises(CelestoError):
        await manager.async_start(vm_id)
    manager.close()
    assert all(process.poll() is not None for process in children)
    with pytest.raises(OSError):
        socket.create_connection(("127.0.0.1", port), timeout=0.2)


def test_interrupted_public_start_reaps_the_spawned_runtime(
    public_runtime: tuple[CelestoManager, str, list[subprocess.Popen[bytes]]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ctrl-C during QMP readiness cannot leave an untracked live guest.

    The real launcher records a real child, then readiness raises the interrupt.
    This boundary proves process death before the real proxy listener closes.
    """
    manager, vm_id, children = public_runtime
    ports: list[int] = []

    def interrupt(_self: object, *_args: object) -> None:
        info = manager.get(vm_id)
        assert info.network is not None and info.network.egress_proxy_host_port is not None
        ports.append(info.network.egress_proxy_host_port)
        raise KeyboardInterrupt

    monkeypatch.setattr(QemuRuntimeAdapter, "_wait_for_runtime", interrupt)
    with pytest.raises(KeyboardInterrupt):
        manager.start(vm_id)
    manager.close()
    (tmp_path / "interrupted-start.json").write_text(
        json.dumps({"returncodes": [process.poll() for process in children], "ports": ports})
    )
    assert len(children) == 1 and children[0].poll() is not None
    for port in ports:
        with pytest.raises(OSError):
            socket.create_connection(("127.0.0.1", port), timeout=0.2)


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["stop", "async_stop", "delete", "async_delete", "close"])
async def test_cleanup_during_launch_preserves_public_process_ownership(
    public_runtime: tuple[CelestoManager, str, list[subprocess.Popen[bytes]]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    """Cleanup cannot release a live child's proxy before startup records it.

    Sequential cleanup tests cannot expose this pre-persistence interval. Hold
    only readiness and observe the actual child, listener, and final cleanup.
    """
    manager, vm_id, children = public_runtime
    starting, finish = threading.Event(), threading.Event()

    def wait_for_runtime(_self: object, *_args: object) -> None:
        starting.set()
        assert finish.wait(timeout=5), "test did not release startup"

    monkeypatch.setattr(QemuRuntimeAdapter, "_wait_for_runtime", wait_for_runtime)
    first = asyncio.create_task(manager.async_start(vm_id))
    try:
        assert await asyncio.to_thread(starting.wait, 5)
        info = manager.get(vm_id)
        assert info.network is not None and info.network.egress_proxy_host_port is not None
        port = info.network.egress_proxy_host_port
        if operation == "close":
            manager.close()
        else:
            with pytest.raises(CelestoError):
                if operation.startswith("async_"):
                    await getattr(manager, operation)(vm_id)
                else:
                    getattr(manager, operation)(vm_id)
        assert children[0].poll() is None
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            pass
    finally:
        finish.set()
        await first
    if operation != "close":
        manager.close()
    assert children[0].poll() is not None
    with pytest.raises(OSError):
        socket.create_connection(("127.0.0.1", port), timeout=0.2)
    (tmp_path / "cleanup-during-start.json").write_text(
        json.dumps({"operation": operation, "returncode": children[0].returncode, "port": port})
    )


def test_failed_interrupted_start_cleanup_retains_public_process_ownership(
    public_runtime: tuple[CelestoManager, str, list[subprocess.Popen[bytes]]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A denied termination must retain the real proxy until a later close succeeds.

    Existing persistence-failure coverage starts after the adapter returns;
    this exercises interruption inside the adapter before its launch result.
    """
    manager, vm_id, children = public_runtime
    ports: list[int] = []

    def interrupt(_self: object, *_args: object) -> None:
        info = manager.get(vm_id)
        assert info.network is not None and info.network.egress_proxy_host_port is not None
        ports.append(info.network.egress_proxy_host_port)
        raise KeyboardInterrupt

    def deny_kill(*_args: object) -> None:
        raise PermissionError("test termination denied")

    monkeypatch.setattr(QemuRuntimeAdapter, "_wait_for_runtime", interrupt)
    with monkeypatch.context() as blocked:
        blocked.setattr("os.kill", deny_kill)
        blocked.setattr(manager, "_kill_process", deny_kill)
        with pytest.raises(PermissionError):
            manager.start(vm_id)
        assert children[0].poll() is None
        with socket.create_connection(("127.0.0.1", ports[0]), timeout=1):
            pass
        with pytest.raises(PermissionError):
            manager.close()
        with socket.create_connection(("127.0.0.1", ports[0]), timeout=1):
            pass
    manager.close()
    assert children[0].poll() is not None
    with pytest.raises(OSError):
        socket.create_connection(("127.0.0.1", ports[0]), timeout=0.2)
    (tmp_path / "failed-start-cleanup.json").write_text(
        json.dumps({"returncode": children[0].returncode, "port": ports[0]})
    )

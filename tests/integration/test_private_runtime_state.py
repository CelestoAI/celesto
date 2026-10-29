"""Exercise private inventory and boot-console creation on a shared-umask system."""

from __future__ import annotations

import json
import os
import socket
import sqlite3
import stat
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal

import paramiko
import pytest

from celesto.cli.service import CLIService
from celesto.ssh_trust import trusted_host_key
from celesto.types import InternetSettings, NetworkConfig, VMConfig, VMInfo, VMState
from celesto.vm import CelestoManager


@pytest.mark.parametrize("selection", ["explicit", "environment", "default"])
def test_cli_inventory_creates_private_missing_parents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, selection: str
) -> None:
    # A 0002 umask used by shared developer/CI accounts must not make Celesto
    # reject the inventory it just created. Existing tests use a 0022 umask.
    # Missing intermediate directories matter as much as the final directory.
    monkeypatch.delenv("CELESTO_DATA_DIR", raising=False)
    monkeypatch.delenv("SUDO_USER", raising=False)
    state_home = tmp_path / "new-account" / "state"
    data = state_home / "celesto"
    monkeypatch.setenv("XDG_STATE_HOME", str(state_home))
    monkeypatch.setattr("celesto.vm.DEFAULT_SYSTEM_DATA_DIR", data)
    if selection == "environment":
        monkeypatch.setenv("CELESTO_DATA_DIR", str(data))
    previous = os.umask(0o002)
    try:
        service = CLIService(data_dir=data if selection == "explicit" else None)
    finally:
        os.umask(previous)
    try:
        assert service.state_manager().list_vms() == []
        modes = {
            str(path.relative_to(tmp_path)): stat.S_IMODE(path.stat().st_mode)
            for path in (data, state_home, state_home.parent)
        }
        assert set(modes.values()) == {0o700}
        assert stat.S_IMODE((data / "celesto.db").stat().st_mode) == 0o600
        (tmp_path / "private-inventory.json").write_text(json.dumps(modes, indent=2))
    finally:
        service.state_manager().close()


@pytest.mark.parametrize("unsafe_component", ["directory", "ancestor"])
def test_cli_inventory_does_not_repair_existing_shared_directories(
    tmp_path: Path, unsafe_component: Literal["directory", "ancestor"]
) -> None:
    # Choosing a preexisting shared path must still fail closed. Silently
    # chmod'ing it would change another caller's directory and its access.
    shared = tmp_path / "shared"
    shared.mkdir()
    shared.chmod(0o775)
    data = shared if unsafe_component == "directory" else shared / "new" / "celesto"
    with pytest.raises(PermissionError, match="private folder"):
        CLIService(data_dir=data)
    assert stat.S_IMODE(shared.stat().st_mode) == 0o775


@pytest.mark.asyncio
@pytest.mark.parametrize("runtime", ["qemu", "firecracker", "libkrun", "libkrun-async"])
@pytest.mark.parametrize("previous_console", [False, True])
async def test_runtime_console_provisions_identity_with_shared_umask(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    runtime: str,
    previous_console: bool,
) -> None:
    # Only replace the hypervisor executable: the real launcher opens stdout,
    # a real subprocess emits a boot identity, and the real trust reader must
    # accept it. Reopening a legacy log must also make the new boot private.
    backend = "libkrun" if runtime.startswith("libkrun") else runtime
    manager = CelestoManager(data_dir=tmp_path / "data", socket_dir=tmp_path / "sockets")
    (tmp_path / "kernel").touch()
    (tmp_path / "rootfs").touch()
    config = VMConfig(
        vm_id="private-console",
        backend=backend,
        kernel_path=tmp_path / "kernel",
        rootfs_path=tmp_path / "rootfs",
    )
    info = VMInfo(
        vm_id=config.vm_id,
        status=VMState.CREATED,
        config=config,
        network=NetworkConfig(
            guest_ip="10.0.2.15", tap_device="usernet", guest_mac="52:54:00:12:34:56"
        ),
    )
    key = paramiko.RSAKey.generate(1024)
    public_key = f"{key.get_name()} {key.get_base64()}"
    console = manager.data_dir / f"{info.vm_id}.log"
    if previous_console:
        console.write_text("CELESTO_SSH_HOST_KEY old-boot\n")
        console.chmod(0o664)
    real_popen = subprocess.Popen

    def emit_console(_argv: object, **kwargs: Any) -> subprocess.Popen[bytes]:
        return real_popen(
            [sys.executable, "-c", f"print('CELESTO_SSH_HOST_KEY {public_key}')"], **kwargs
        )

    monkeypatch.setattr("celesto.vm.subprocess.Popen", emit_console)
    monkeypatch.setattr(manager, "_find_qemu_binary", lambda: Path(sys.executable))
    monkeypatch.setattr(manager.host, "find_firecracker", lambda: Path(sys.executable))
    monkeypatch.setattr(manager, "_find_libkrun_library", lambda: True)
    previous = os.umask(0o002)
    try:
        if runtime == "libkrun-async":
            child = await manager._async_start_libkrun(info, console)
            assert await child.wait() == 0
        else:
            if runtime == "qemu":
                process = manager._start_qemu(info, console)
            elif runtime == "firecracker":
                process = manager._start_firecracker(tmp_path / "control.sock", console)
            else:
                process = manager._start_libkrun(info, console)
            assert process.wait(timeout=10) == 0
        assert trusted_host_key(manager.data_dir, info.vm_id) == public_key
        assert stat.S_IMODE(console.stat().st_mode) == 0o600
        (tmp_path / "private-console.json").write_text(
            json.dumps({"runtime": runtime, "mode": "0600", "identity_verified": True})
        )
    finally:
        os.umask(previous)
        manager.close()


def test_console_identity_waits_for_the_complete_boot_line(tmp_path: Path) -> None:
    # Runtime stdout can be read between writes. Even a parseable key must not
    # become trusted before the boot script has finished its line.
    key = paramiko.RSAKey.generate(1024)
    public_key = f"{key.get_name()} {key.get_base64()}"
    console = tmp_path / "split-console.log"
    console.write_text(f"CELESTO_SSH_HOST_KEY {public_key}")
    assert trusted_host_key(tmp_path, "split-console") is None
    with console.open("a") as writer:
        writer.write("\n")
    assert trusted_host_key(tmp_path, "split-console") == public_key


def test_cli_inventory_supports_platforms_without_nofollow_chmod(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Some POSIX builds expose chmod but cannot honor follow_symlinks=False.
    # Keep the real filesystem and SQLite; emulate only that syscall capability.
    chmod = os.chmod

    def platform_chmod(path: Any, mode: int, **kwargs: Any) -> None:
        if kwargs.get("follow_symlinks") is False:
            raise NotImplementedError("follow_symlinks unavailable")
        chmod(path, mode, **kwargs)

    monkeypatch.setattr(os, "chmod", platform_chmod)
    service = CLIService(data_dir=tmp_path / "inventory")
    try:
        assert service.state_manager().list_vms() == []
        assert stat.S_IMODE((service.data_dir / "celesto.db").stat().st_mode) == 0o600
    finally:
        service.state_manager().close()


@pytest.mark.skipif(os.name == "nt", reason="POSIX permits unlinking an open SQLite sidecar")
@pytest.mark.parametrize("suffix", ["-journal", "-wal", "-shm"])
def test_inventory_read_survives_sqlite_unlink_during_permission_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, suffix: str
) -> None:
    """A real SQLite commit can unlink a sidecar after pathname lookup resolved it."""
    service = CLIService(data_dir=tmp_path / "inventory")
    manager = service.state_manager()
    database = service.data_dir / "celesto.db"
    with closing(sqlite3.connect(database)) as prepare:
        prepare.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        mode = prepare.execute(
            "PRAGMA journal_mode = " + ("DELETE" if suffix == "-journal" else "WAL")
        ).fetchone()[0]
        prepare.execute("CREATE TABLE commit_probe(value INTEGER)")
        prepare.execute("INSERT INTO commit_probe VALUES(0)")
        prepare.commit()

    ready = threading.Event()
    commit = threading.Event()
    committed = threading.Event()
    sidecar = Path(str(database) + suffix)
    observed: list[dict[str, str | int]] = []
    original_lstat = Path.lstat

    def writer() -> None:
        try:
            with closing(sqlite3.connect(database, isolation_level=None)) as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("UPDATE commit_probe SET value=1")
                ready.set()
                assert commit.wait(10), "Permission check did not reach the sidecar"
                connection.commit()
        finally:
            committed.set()

    def commit_during_stat(path: Path, *args: Any, **kwargs: Any) -> os.stat_result:
        if path != sidecar or observed:
            return original_lstat(path, *args, **kwargs)
        # Hold the resolved inode while SQLite performs its normal unlink.
        # No main-database descriptor is opened/closed, preserving SQLite locks.
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            commit.set()
            assert committed.wait(10), "SQLite did not finish its native commit"
            info = os.fstat(descriptor)
            assert stat.S_ISREG(info.st_mode)
            assert info.st_uid == os.geteuid()
            assert info.st_nlink == 0
            observed.append(
                {"suffix": suffix, "links": info.st_nlink, "mode": oct(stat.S_IMODE(info.st_mode))}
            )
            return info
        finally:
            os.close(descriptor)

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(writer)
        try:
            assert ready.wait(10), "SQLite writer did not create its journal"
            monkeypatch.setattr(Path, "lstat", commit_during_stat)
            assert manager.list_vms() == []
        finally:
            commit.set()
            future.result(timeout=15)
            manager.close()
    assert len(observed) == 1
    with closing(sqlite3.connect(database)) as reader:
        assert reader.execute("SELECT value FROM commit_probe").fetchone()[0] == 1
    (tmp_path / "inventory-unlink-race.json").write_text(
        json.dumps({"journal_mode": mode, "observed": observed, "commit_preserved": True})
    )


def test_manager_close_attempts_other_guests_and_retains_failed_proxy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # One runtime stop failure must not strand other public guests. Real proxy
    # sockets prove the failed runtime keeps its port until a later safe retry.
    manager = CelestoManager(data_dir=tmp_path / "state", backend="qemu")
    kernel, disk = tmp_path / "kernel", tmp_path / "rootfs"
    kernel.touch()
    disk.touch()
    attempted = []
    fail_first = True

    def stop(info: VMInfo, **_kwargs: object) -> None:
        attempted.append(info.vm_id)
        if info.vm_id == "first" and fail_first:
            raise RuntimeError("first runtime remains alive")

    monkeypatch.setattr(
        manager,
        "_runtime_adapter_for_backend",
        lambda _backend: SimpleNamespace(
            start=lambda *_args, **_kwargs: SimpleNamespace(
                status=VMState.RUNNING, pid=12345, control_socket_path=None, display=None
            ),
            stop=stop,
        ),
    )
    monkeypatch.setattr(manager, "_check_qemu_slirp_host_forward_ports", lambda _info: None)
    ports = []
    for vm_id in ("first", "second"):
        manager.state.create_vm(
            VMConfig(
                vm_id=vm_id,
                backend="qemu",
                kernel_path=kernel,
                rootfs_path=disk,
                internet_settings=InternetSettings(mode="public"),
            )
        )
        manager.state.update_vm(
            vm_id,
            network=NetworkConfig(
                guest_ip="10.0.2.15", tap_device="usernet", guest_mac="52:54:00:12:34:56"
            ),
        )
        running = manager.start(vm_id)
        assert running.network is not None and running.network.egress_proxy_host_port is not None
        ports.append(running.network.egress_proxy_host_port)
    try:
        with pytest.raises(RuntimeError, match="first runtime remains alive"):
            manager.close()
        assert attempted == ["first", "second"]
        assert manager.get("second").status == VMState.STOPPED
        with socket.create_connection(("127.0.0.1", ports[0]), timeout=1):
            pass
        with pytest.raises(OSError):
            socket.create_connection(("127.0.0.1", ports[1]), timeout=0.2)
    finally:
        fail_first = False
        manager.close()
    assert attempted == ["first", "second", "first"]
    with pytest.raises(OSError):
        socket.create_connection(("127.0.0.1", ports[0]), timeout=0.2)

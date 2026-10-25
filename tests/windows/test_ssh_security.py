"""Real SSH handshake and streaming regressions; no guest VM is required."""

import os
import socket
import subprocess
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Literal, cast

import paramiko
import pytest
from paramiko.common import AUTH_SUCCESSFUL, OPEN_SUCCEEDED

from celesto import Celesto
from celesto.exceptions import CelestoError, OperationTimeoutError
from celesto.ssh import SSHClient
from celesto.types import (
    CommandExitEvent,
    CommandOutputEvent,
    CommandStartedEvent,
    GuestOS,
    VMConfig,
    VMInfo,
    VMState,
)
from celesto.vm import CelestoManager


@contextmanager
def ssh_peer(
    tmp_path: Path, *, flood: bool | Literal["slow"] = False
) -> Iterator[tuple[int, Path, list[str]]]:
    key = paramiko.RSAKey.generate(1024)
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    listener.settimeout(5)
    port = listener.getsockname()[1]
    authenticated: list[str] = []
    transports: list[paramiko.Transport] = []

    class Peer(paramiko.ServerInterface):
        def __init__(self) -> None:
            self.finished = threading.Event()

        def check_auth_password(self, username: str, password: str) -> int:
            authenticated.append(username)
            return AUTH_SUCCESSFUL

        def get_allowed_auths(self, username: str) -> str:
            return "password"

        def check_channel_request(self, kind: str, chanid: int) -> int:
            return OPEN_SUCCEEDED

        def check_channel_exec_request(self, channel: paramiko.Channel, command: bytes) -> bool:
            def produce() -> None:
                try:
                    if flood == "slow":
                        for _ in range(150):
                            channel.send(b"x")
                            time.sleep(0.01)
                        channel.send_exit_status(0)
                    elif flood:
                        for _ in range(300):
                            channel.sendall(b"x" * 32768)
                        channel.send_exit_status(0)
                    else:
                        channel.send(b"hello")
                        channel.send_stderr(b"error")
                        channel.send_exit_status(0)
                    channel.shutdown_write()
                except (OSError, EOFError):
                    pass
                finally:
                    self.finished.set()

            threading.Thread(target=produce, daemon=True).start()
            return True

    stopped = threading.Event()

    def serve() -> None:
        while not stopped.is_set():
            try:
                sock, _ = listener.accept()
                transport = paramiko.Transport(sock)
                transports.append(transport)
                transport.add_server_key(key)
                peer = Peer()
                transport.start_server(server=peer)
                channel = transport.accept(5)
                if channel:
                    while transport.is_active() and not stopped.is_set():
                        if peer.finished.is_set() and channel.eof_received:
                            channel.close()
                            break
                        stopped.wait(0.01)
            except (OSError, EOFError, paramiko.SSHException):
                if not stopped.is_set():
                    continue

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    known = tmp_path / "known_hosts"
    known.write_text(f"[127.0.0.1]:{port} {key.get_name()} {key.get_base64()}\n")
    try:
        yield port, known, authenticated
    finally:
        stopped.set()
        listener.close()
        for transport in transports:
            transport.close()
        thread.join(6)


@pytest.mark.parametrize("known_hosts_source", ["empty", "missing", "directory"])
def test_unknown_ssh_peer_is_rejected_before_password(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, known_hosts_source: str
) -> None:
    # A missing or unreadable key file must fail before credentials are sent,
    # with the same actionable error boundary as an unknown server key.
    configured = tmp_path / known_hosts_source
    monkeypatch.setenv("CELESTO_SSH_KNOWN_HOSTS", str(configured))
    if known_hosts_source == "empty":
        configured.touch()
    elif known_hosts_source == "directory":
        configured.mkdir()
    with ssh_peer(tmp_path) as (port, _, authenticated):
        client = SSHClient(
            "127.0.0.1",
            port=port,
            password="synthetic-test-password",
            sandbox_name="windows-trust-check",
        )
        try:
            with pytest.raises(CelestoError) as rejected:
                client.run("ignored", shell="raw")
            assert not authenticated
            if known_hosts_source != "empty":
                assert str(configured) in str(rejected.value)
                assert "celesto computer ssh windows-trust-check" in str(rejected.value)
        finally:
            client.close()


def test_trusted_ssh_stream_is_capped_before_collection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with ssh_peer(tmp_path, flood=True) as (port, known, _):
        monkeypatch.setenv("CELESTO_SSH_KNOWN_HOSTS", str(known))
        client = SSHClient("127.0.0.1", port=port, password="synthetic-test-password")
        try:
            with pytest.raises(CelestoError, match="output limit"):
                client.run("ignored", timeout=5, shell="raw")
        finally:
            client.close()


def test_busy_ssh_stream_obeys_absolute_deadline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with ssh_peer(tmp_path, flood="slow") as (port, known, _):
        monkeypatch.setenv("CELESTO_SSH_KNOWN_HOSTS", str(known))
        client = SSHClient("127.0.0.1", port=port, password="synthetic-test-password")
        try:
            with pytest.raises(OperationTimeoutError):
                client.run("ignored", timeout=1, shell="raw")
        finally:
            client.close()


@pytest.mark.parametrize("stream", [False, True])
def test_provisioned_host_key_authenticates_without_global_known_hosts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stream: bool
) -> None:
    # Failure modes: an unknown peer is accepted, a provisioned key is ignored,
    # or a valid guest requires mutable/global known_hosts state.
    monkeypatch.delenv("CELESTO_SSH_KNOWN_HOSTS", raising=False)
    with ssh_peer(tmp_path) as (port, known, authenticated):
        host_key = " ".join(known.read_text().split()[1:])
        client = SSHClient(
            "127.0.0.1", port=port, password="synthetic-test-password", host_key=host_key
        )
        try:
            if stream:
                events = list(client.run_stream("ignored", timeout=1.5, shell="raw"))
                assert isinstance(events[0], CommandStartedEvent)
                assert events[0].timeout_seconds == 1.5
                assert (
                    "".join(
                        event.data
                        for event in events
                        if isinstance(event, CommandOutputEvent) and event.type == "stdout"
                    )
                    == "hello"
                )
                assert isinstance(events[-1], CommandExitEvent)
                assert events[-1].exit_code == 0
            else:
                result = client.run("ignored", timeout=1.5, shell="raw")
                assert result.stdout == "hello"
            assert authenticated == ["root"]
        finally:
            client.close()


def test_provisioned_host_key_rejects_replacement_before_password(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CELESTO_SSH_KNOWN_HOSTS", raising=False)
    with ssh_peer(tmp_path) as (port, _, authenticated):
        wrong_key = paramiko.RSAKey.generate(1024)
        client = SSHClient(
            "127.0.0.1",
            port=port,
            password="synthetic-test-password",
            host_key=f"{wrong_key.get_name()} {wrong_key.get_base64()}",
        )
        try:
            with pytest.raises(CelestoError):
                client.run("ignored", shell="raw")
            assert not authenticated
        finally:
            client.close()


@pytest.mark.parametrize("identity", ["trusted", "missing_alias", "replacement"])
def test_windows_alias_verifies_dynamic_endpoint_before_password(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, identity: str
) -> None:
    # The forward's port is assigned at runtime. A stable, independently
    # provisioned alias must work in both clients, without falling back to an
    # endpoint entry when that alias is missing or names a different key.
    alias = "trusted-windows-image"
    disk = tmp_path / "windows.qcow2"
    disk.touch()
    config = VMConfig(
        vm_id="windows-alias-test",
        rootfs_path=disk,
        backend="qemu",
        guest_os=GuestOS.WINDOWS,
        boot_mode="firmware",
    )
    info = VMInfo(vm_id=config.vm_id, config=config, status=VMState.CREATED)

    def manager(**_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(data_dir=tmp_path, create=lambda _config: info)

    monkeypatch.setattr("celesto.facade.CelestoManager", manager)
    with ssh_peer(tmp_path) as (port, known, authenticated):
        endpoint_entry = known.read_text()
        trusted_key = " ".join(endpoint_entry.split()[1:])
        if identity == "replacement":
            replacement = paramiko.RSAKey.generate(1024)
            alias_key = f"{replacement.get_name()} {replacement.get_base64()}"
        else:
            alias_key = trusted_key
        entry_name = "another-image" if identity == "missing_alias" else alias
        known.write_text(f"{entry_name} {alias_key}\n{endpoint_entry}")
        monkeypatch.setenv("CELESTO_SSH_KNOWN_HOSTS", str(known))
        vm = Celesto(
            config,
            ssh_password="synthetic-test-password",
            ssh_host_key_alias=alias,
        )
        client = vm._new_ssh_client(host="127.0.0.1", port=port)
        try:
            if identity != "trusted":
                with pytest.raises(CelestoError):
                    client.run("ignored", shell="raw")
                assert not authenticated
                return
            assert client.run("ignored", shell="raw").stdout == "hello"
            assert authenticated == ["root"]
            client.close()

            # Exercise OpenSSH's actual alias/port lookup, not just argv shape.
            vm._ssh = client
            vm._ssh_ready = True
            command = vm._ssh_attach_command()
            askpass = tmp_path / "askpass"
            askpass.write_text("#!/bin/sh\nprintf '%s\\n' synthetic-test-password\n")
            askpass.chmod(0o700)
            result = subprocess.run(
                [
                    command[0],
                    "-T",
                    "-o",
                    "PreferredAuthentications=password",
                    "-o",
                    "PubkeyAuthentication=no",
                    "-o",
                    "NumberOfPasswordPrompts=1",
                    *command[1:],
                    "ignored",
                ],
                env={
                    **os.environ,
                    "DISPLAY": ":99",
                    "SSH_ASKPASS": str(askpass),
                    "SSH_ASKPASS_REQUIRE": "force",
                },
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            assert result.returncode == 0, result.stderr
            assert result.stdout == "hello"
            assert authenticated == ["root", "root"]
        finally:
            client.close()


@pytest.mark.parametrize("alias", ["", "-oProxyCommand=bad", "a b", "a\nb", "a" * 254])
def test_ssh_identity_alias_rejects_unsafe_values_before_setup(alias: str) -> None:
    # Both public entry points must reject option-like/control text before
    # any image preparation or network connection can begin.
    with pytest.raises(ValueError, match="SSH identity alias"):
        SSHClient("127.0.0.1", host_key_alias=alias)
    with pytest.raises(ValueError, match="SSH identity alias"):
        Celesto(ssh_host_key_alias=alias)


def _managed_vm(tmp_path: Path) -> Celesto:
    from types import SimpleNamespace

    from celesto.facade import Celesto
    from celesto.types import GuestOS

    vm = Celesto.__new__(Celesto)
    vm._vm_id = "ssh-provisioning-proof"
    vm._sdk = cast(CelestoManager, SimpleNamespace(data_dir=tmp_path))
    vm._info = cast(VMInfo, SimpleNamespace(config=SimpleNamespace(guest_os=GuestOS.ALPINE)))
    vm._ssh_user = "root"
    vm._ssh_password = "synthetic-test-password"
    return vm


def test_managed_vm_provisions_first_console_key_before_ssh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The console is the independent provisioning channel. A later guest log
    # line must not replace the boot key, and no global known_hosts is needed.
    monkeypatch.delenv("CELESTO_SSH_KNOWN_HOSTS", raising=False)
    with ssh_peer(tmp_path) as (port, known, authenticated):
        key = " ".join(known.read_text().split()[1:])
        replacement = paramiko.RSAKey.generate(1024)
        vm = _managed_vm(tmp_path)
        (tmp_path / f"{vm.vm_id}.log").write_text(
            f"booting\nCELESTO_SSH_HOST_KEY {key}\n"
            f"CELESTO_SSH_HOST_KEY {replacement.get_name()} {replacement.get_base64()}\n"
        )
        client = vm._new_ssh_client(host="127.0.0.1", port=port)
        try:
            assert client.run("ignored", shell="raw").stdout == "hello"
            assert authenticated == ["root"]
        finally:
            client.close()


def test_managed_openssh_command_pins_console_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CELESTO_SSH_KNOWN_HOSTS", raising=False)
    vm = _managed_vm(tmp_path)
    key = paramiko.RSAKey.generate(1024)
    (tmp_path / f"{vm.vm_id}.log").write_text(
        f"CELESTO_SSH_HOST_KEY {key.get_name()} {key.get_base64()}\n"
    )
    vm._ssh = SSHClient("127.0.0.1", port=2222)
    vm._ssh_ready = True
    command = vm._ssh_attach_command()
    assert "StrictHostKeyChecking=yes" in command
    known_path = next(
        part.split("=", 1)[1] for part in command if part.startswith("UserKnownHostsFile=")
    )
    assert known_path != "/dev/null"
    keys = paramiko.HostKeys(known_path)
    assert keys.check("[127.0.0.1]:2222", key)
    assert Path(known_path).stat().st_mode & 0o077 == 0


@pytest.mark.parametrize(
    "unsafe_source", ["console_symlink", "writable_directory", "writable_cache"]
)
def test_managed_vm_rejects_untrusted_local_key_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, unsafe_source: str
) -> None:
    # Existing handshake tests trust a well-owned console. These cases protect
    # the independent local provisioning boundary: another account must not be
    # able to substitute a key through a symlink, directory, or writable cache.
    empty = tmp_path / "empty"
    empty.touch()
    monkeypatch.setenv("CELESTO_SSH_KNOWN_HOSTS", str(empty))
    directory = tmp_path / "computers"
    directory.mkdir(mode=0o700)
    vm = _managed_vm(directory)
    with ssh_peer(tmp_path) as (port, known, authenticated):
        key = " ".join(known.read_text().split()[1:])
        console = directory / f"{vm.vm_id}.log"
        if unsafe_source == "console_symlink":
            target = tmp_path / "substituted-console"
            target.write_text(f"CELESTO_SSH_HOST_KEY {key}\n")
            console.symlink_to(target)
        elif unsafe_source == "writable_directory":
            console.write_text(f"CELESTO_SSH_HOST_KEY {key}\n")
            directory.chmod(0o777)
        else:
            cache = directory / "ssh-known-hosts"
            cache.mkdir(mode=0o700)
            cached = cache / f"{vm.vm_id}.known_hosts"
            cached.write_text(known.read_text())
            cached.chmod(0o666)
        client = vm._new_ssh_client(host="127.0.0.1", port=port)
        try:
            with pytest.raises(CelestoError):
                client.run("ignored", shell="raw")
            assert not authenticated
        finally:
            client.close()
            directory.chmod(0o700)


@pytest.mark.parametrize("previous_boot", [False, True])
def test_managed_vm_waits_for_delayed_boot_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, previous_boot: bool
) -> None:
    # Boot readiness starts before init publishes the key. The network can be
    # ready first, but authentication must wait for independent provisioning.
    monkeypatch.delenv("CELESTO_SSH_KNOWN_HOSTS", raising=False)
    with ssh_peer(tmp_path) as (port, known, authenticated):
        vm = _managed_vm(tmp_path)
        vm._ssh = None
        vm._ssh_key_path = None
        key = " ".join(known.read_text().split()[1:])
        (tmp_path / f"{vm.vm_id}.log").touch()
        if previous_boot:
            cache = tmp_path / "ssh-known-hosts"
            cache.mkdir(mode=0o700)
            previous_key = paramiko.RSAKey.generate(1024)
            (cache / f"{vm.vm_id}.known_hosts").write_text(
                f"old {previous_key.get_name()} {previous_key.get_base64()}\n"
            )
        timer = threading.Timer(
            0.2,
            lambda: (tmp_path / f"{vm.vm_id}.log").write_text(f"CELESTO_SSH_HOST_KEY {key}\n"),
        )
        timer.start()
        try:
            errors: list[str] = []
            assert vm._attempt_ssh_candidates(
                [("127.0.0.1", port, None)], deadline=time.monotonic() + 2, errors=errors
            ), errors
            assert vm._ssh is not None
            assert vm._ssh.run("ignored", shell="raw").stdout == "hello"
            assert authenticated == ["root"]
        finally:
            timer.join()
            if vm._ssh is not None:
                vm._ssh.close()

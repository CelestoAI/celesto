"""Verify a computer's SSH identity using its local boot console.

The boot script publishes the public host key before starting SSH. Network
connections never supply this key. Later console output cannot replace it.
"""

from __future__ import annotations

import os
import secrets
import stat
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from pathlib import Path

import paramiko

_MARKER = "CELESTO_SSH_HOST_KEY "
_MAX_BOOT_LOG_BYTES = 4 * 1024 * 1024
_DIRECTORY_FLAGS = os.O_RDONLY | sum(
    getattr(os, flag, 0) for flag in ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC")
)


def _paths(data_dir: Path, vm_id: str) -> tuple[Path, Path] | None:
    # Remote managers need not have a local console. They retain normal,
    # strict known_hosts verification.
    if not isinstance(data_dir, (str, Path)) or not isinstance(vm_id, str):
        return None
    if not vm_id or Path(vm_id).name != vm_id or vm_id in {".", ".."}:
        raise ValueError("Computer name cannot be used as an SSH identity filename")
    directory = Path(data_dir)
    return directory / f"{vm_id}.log", directory / "ssh-known-hosts" / f"{vm_id}.known_hosts"


def _check_owner(fd: int, *, directory: bool, sticky_parent: bool = False) -> None:
    info = os.fstat(fd)
    expected_type = stat.S_ISDIR if directory else stat.S_ISREG
    if not expected_type(info.st_mode) or info.st_uid not in {0, os.geteuid()}:
        raise OSError("SSH identity source is not owned by this account")
    # Root's sticky temporary directories protect individually owned children.
    if info.st_mode & 0o022 and not (
        sticky_parent and info.st_uid == 0 and info.st_mode & stat.S_ISVTX
    ):
        raise OSError("SSH identity source can be changed by another account")


@contextmanager
def _trusted_directory(path: Path) -> Iterator[int]:
    # Resolve system aliases such as macOS /var, then open every component
    # relative to a retained descriptor. No later pathname lookup can redirect
    # a read or publication through a concurrently replaced parent.
    if os.name != "posix":
        raise OSError("Local console identity provisioning requires POSIX file ownership")
    resolved = path.resolve(strict=True)
    descriptor = os.open(resolved.anchor, _DIRECTORY_FLAGS)
    try:
        _check_owner(descriptor, directory=True, sticky_parent=True)
        for index, part in enumerate(resolved.parts[1:]):
            child = os.open(part, _DIRECTORY_FLAGS, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
            _check_owner(descriptor, directory=True, sticky_parent=index < len(resolved.parts) - 2)
        yield descriptor
    finally:
        os.close(descriptor)


def _read_owned_file(directory: int, name: str, limit: int) -> str:
    descriptor = os.open(
        name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=directory
    )
    with os.fdopen(descriptor, "rb") as handle:
        _check_owner(handle.fileno(), directory=False)
        return handle.read(limit).decode("ascii", errors="replace")


def _parse_key(line: str) -> str | None:
    try:
        entry = paramiko.hostkeys.HostKeyEntry.from_line(line)
        if entry is not None and entry.key is not None:
            return f"{entry.key.get_name()} {entry.key.get_base64()}"
    except (ValueError, paramiko.SSHException):
        pass
    return None


def trusted_host_key(data_dir: Path, vm_id: str) -> str | None:
    """Read the first boot key, or an already provisioned per-computer key."""
    paths = _paths(data_dir, vm_id)
    if paths is None:
        return None
    console, known = paths
    try:
        with _trusted_directory(console.parent) as directory:
            current_boot = True
            try:
                lines = _read_owned_file(directory, console.name, _MAX_BOOT_LOG_BYTES).splitlines()
            except FileNotFoundError:
                current_boot = False
                lines = []
            for line in lines:
                if line.startswith(_MARKER):
                    # Never replace a malformed first marker with a later line.
                    return _parse_key("guest " + line[len(_MARKER) :])
            if current_boot:
                # A new boot truncates this file before publishing its new key.
                # Never pin a previous boot while waiting for the current one.
                return None
            cache = os.open(known.parent.name, _DIRECTORY_FLAGS, dir_fd=directory)
            try:
                _check_owner(cache, directory=True)
                return _parse_key(_read_owned_file(cache, known.name, 16384).splitlines()[0])
            finally:
                os.close(cache)
    except (OSError, IndexError, RuntimeError):
        return None


def openssh_host_key_options(data_dir: Path, vm_id: str, host: str, port: int) -> list[str]:
    """Use a private per-computer known_hosts file for interactive SSH and tunnels."""
    options = ["-o", "StrictHostKeyChecking=yes"]
    key = trusted_host_key(data_dir, vm_id)
    paths = _paths(data_dir, vm_id)
    if key is None or paths is None:
        configured = os.environ.get("CELESTO_SSH_KNOWN_HOSTS")
        if configured:
            options.extend(["-o", f"UserKnownHostsFile={Path(configured).expanduser()}"])
        return options
    _, known = paths
    known = known.parent.parent.resolve(strict=True) / known.parent.name / known.name
    endpoint = host if port == 22 else f"[{host}]:{port}"
    with _trusted_directory(known.parent.parent) as directory:
        with suppress(FileExistsError):
            os.mkdir(known.parent.name, mode=0o700, dir_fd=directory)
        cache = os.open(known.parent.name, _DIRECTORY_FLAGS, dir_fd=directory)
        try:
            _check_owner(cache, directory=True)
            staging = f".key-{secrets.token_hex(16)}"
            descriptor = os.open(
                staging,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                0o600,
                dir_fd=cache,
            )
            try:
                with os.fdopen(descriptor, "w") as handle:
                    handle.write(f"{endpoint} {key}\n")
                os.replace(staging, known.name, src_dir_fd=cache, dst_dir_fd=cache)
            finally:
                with suppress(FileNotFoundError):
                    os.unlink(staging, dir_fd=cache)
        finally:
            os.close(cache)
    options.extend(["-o", f"UserKnownHostsFile={known}", "-o", "GlobalKnownHostsFile=/dev/null"])
    return options

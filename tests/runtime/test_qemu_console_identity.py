"""Real console/trust/snapshot contracts designed before the prefix repair.

Credible failures: rollover loses the first boot marker or promotes a later
guest key; malformed/partial/out-of-window markers gain authority; restore
identity is lost or reused by a cold boot; normalization erases the boot prefix;
and unsupported caps allocate a pipe/child before refusal. Existing standalone
retention and SSH tests do not combine these boundaries. Only pipe/process
creation is observed for early-refusal assertions; trust and relay work are real.
"""

from __future__ import annotations

import hashlib
import json
import os
import selectors
import subprocess
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import paramiko
import pytest

from celesto.exceptions import CelestoError
from celesto.ssh_trust import (
    openssh_host_key_options,
    save_snapshot_host_key,
    snapshot_host_key,
    trusted_host_key,
)
from celesto.vm import CelestoManager, _open_runtime_log, _start_bounded_console

WINDOW = 4 * 1024**2
LIMIT = 8 * 1024**2
CHUNK = 64 * 1024
END = b"\nlast useful diagnostic\n"
NOTICE = b"[Celesto: older console output truncated]"
pytestmark = pytest.mark.skipif(os.name != "posix", reason="Private relay requires POSIX")


@pytest.fixture(scope="module")
def identities() -> tuple[str, str]:
    # Synthetic keys remain in memory; receipts contain only public identities.
    keys = [paramiko.RSAKey.generate(1024) for _ in range(2)]
    return (
        f"{keys[0].get_name()} {keys[0].get_base64()}",
        f"{keys[1].get_name()} {keys[1].get_base64()}",
    )


@pytest.fixture
def private_data() -> Iterator[Path]:
    # Workspace ancestors can be group-writable. Keep the real ownership guard
    # and use a fresh owned0700 directory rather than changing that guard.
    with tempfile.TemporaryDirectory(prefix="celesto-console-identity-") as directory:
        yield Path(directory)


def marker(key: str) -> bytes:
    return f"CELESTO_SSH_HOST_KEY {key}\n".encode("ascii")


def wait_for(predicate, reason: str) -> None:
    until = time.monotonic() + 5
    while time.monotonic() < until:
        if predicate():
            return
        time.sleep(0.005)
    raise AssertionError(reason)


@contextmanager
def console(
    directory: Path, *, seed: str | None = None
) -> Iterator[tuple[Path, subprocess.Popen[bytes]]]:
    log = directory / "machine.log"
    with _open_runtime_log(log, ssh_host_key=seed, read_write=True) as handle:
        child = _start_bounded_console(handle, LIMIT)
        try:
            yield log, child
        finally:
            if child.stdin is not None and not child.stdin.closed:
                child.stdin.close()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=2)


def send(child: subprocess.Popen[bytes], log: Path, data: bytes) -> None:
    assert child.stdin is not None
    descriptor = child.stdin.fileno()
    blocking = os.get_blocking(descriptor)
    os.set_blocking(descriptor, False)
    remaining = memoryview(data)
    deadline = time.monotonic() + 5
    try:
        with selectors.DefaultSelector() as writer:
            writer.register(descriptor, selectors.EVENT_WRITE)
            while remaining:
                timeout = deadline - time.monotonic()
                assert timeout > 0, "Console producer exceeded its bounded write deadline"
                assert writer.select(timeout), "Console relay stopped draining its owned pipe"
                try:
                    written = os.write(descriptor, remaining[:CHUNK])
                except BlockingIOError:
                    continue
                assert written > 0
                remaining = remaining[written:]
                assert log.stat().st_size <= LIMIT
    finally:
        os.set_blocking(descriptor, blocking)


def fill(child: subprocess.Popen[bytes], log: Path, count: int, value: bytes = b"x") -> None:
    chunk = value * CHUNK
    for _ in range(count // CHUNK):
        send(child, log, chunk)
    if count % CHUNK:
        send(child, log, chunk[: count % CHUNK])


def suffix(log: Path, size: int) -> bytes:
    with log.open("rb") as source:
        source.seek(-min(size, log.stat().st_size), os.SEEK_END)
        return source.read(size)


def finish_with_late_key(child: subprocess.Popen[bytes], log: Path, key: str) -> None:
    # Force multiple rollovers, then fill the current file exactly to its cap.
    # The next write deterministically puts the later key near the front of
    # the old implementation's rotated tail, exposing promotion rather than
    # depending on pipe chunking or an accidental final file size.
    fill(child, log, 2 * LIMIT)
    checkpoint = b"\nrotation-fill-checkpoint\n"
    send(child, log, checkpoint)
    wait_for(lambda: suffix(log, len(checkpoint)) == checkpoint, "Relay did not drain checkpoint")
    fill(child, log, LIMIT - log.stat().st_size)
    wait_for(lambda: log.stat().st_size == LIMIT, "Relay did not reach exact cap")
    send(child, log, b"\n" + marker(key) + END)
    assert child.stdin is not None
    child.stdin.close()
    assert child.wait(timeout=5) == 0


def receipt(
    tmp_path: Path, log: Path, *, expected_prefix: bytes, selected: str | None, **facts
) -> dict:
    with log.open("rb") as source:
        actual = source.read(WINDOW)
        rest = source.read()
    observed = {
        "limit": LIMIT,
        "retained_bytes": log.stat().st_size,
        "expected_prefix_sha256": hashlib.sha256(expected_prefix).hexdigest(),
        "actual_prefix_sha256": hashlib.sha256(actual).hexdigest(),
        "prefix_unchanged": actual == expected_prefix,
        "rotation_notice_present": NOTICE in actual + rest,
        "latest_diagnostic_retained": suffix(log, len(END)) == END,
        "selected_public_key": selected,
        **facts,
    }
    (tmp_path / "identity-receipt.json").write_text(json.dumps(observed, indent=2) + "\n")
    return observed


def check_rotation(observed: dict) -> None:
    assert observed["retained_bytes"] <= LIMIT
    assert observed["rotation_notice_present"]
    assert observed["latest_diagnostic_retained"]
    assert observed["prefix_unchanged"]


def test_first_boot_key_survives_rotations_and_later_guest_marker(
    private_data: Path, tmp_path: Path, identities: tuple[str, str]
) -> None:
    first, later = identities
    prefix = marker(first) + b"." * (WINDOW - len(marker(first)) - 1) + b"\n"
    with console(private_data) as (log, child):
        send(child, log, prefix)
        wait_for(lambda: log.stat().st_size == WINDOW, "Boot prefix was not written")
        assert trusted_host_key(private_data, "machine") == first
        openssh_host_key_options(private_data, "machine", "127.0.0.1", 2222)
        finish_with_late_key(child, log, later)
        selected = trusted_host_key(private_data, "machine")
        observed = receipt(
            tmp_path,
            log,
            expected_prefix=prefix,
            selected=selected,
            original_public_key=first,
            later_public_key=later,
        )
        assert selected == first
        check_rotation(observed)


def test_malformed_first_marker_cannot_be_replaced_after_rotation(
    private_data: Path, tmp_path: Path, identities: tuple[str, str]
) -> None:
    first = b"CELESTO_SSH_HOST_KEY unsupported-key invalid\n"
    prefix = first + b"." * (WINDOW - len(first) - 1) + b"\n"
    with console(private_data) as (log, child):
        send(child, log, prefix)
        wait_for(lambda: log.stat().st_size == WINDOW, "Malformed boot prefix was not written")
        assert trusted_host_key(private_data, "machine") is None
        finish_with_late_key(child, log, identities[1])
        selected = trusted_host_key(private_data, "machine")
        observed = receipt(tmp_path, log, expected_prefix=prefix, selected=selected)
        assert selected is None
        check_rotation(observed)


@pytest.mark.parametrize("newline_within_window", [True, False])
def test_fragmented_line_obeys_exact_original_boot_window_after_rotation(
    private_data: Path, tmp_path: Path, identities: tuple[str, str], newline_within_window: bool
) -> None:
    line = marker(identities[0])
    offset = WINDOW - len(line) + (0 if newline_within_window else 1)
    padding = b"." * (offset - 1) + b"\n"
    prefix = (padding + line)[:WINDOW]
    with console(private_data) as (log, child):
        send(child, log, padding)
        written = len(padding)
        # Split both the marker and key material; a parseable public key without
        # its completed newline must still never become an authority.
        positions = [0, 8, 17, 24, len(line) // 2, len(line) - 1]
        for start, end in zip(positions, positions[1:] + [len(line) - 1], strict=True):
            if start == end:
                continue
            piece = line[start:end]
            send(child, log, piece)
            written += len(piece)
            wait_for(
                lambda expected_size=written: log.stat().st_size == expected_size,
                "Partial boot line was not drained",
            )
            assert trusted_host_key(private_data, "machine") is None
        send(child, log, b"\n")
        wait_for(lambda: log.stat().st_size == offset + len(line), "Boot newline was not drained")
        expected = identities[0] if newline_within_window else None
        assert trusted_host_key(private_data, "machine") == expected
        finish_with_late_key(child, log, identities[1])
        selected = trusted_host_key(private_data, "machine")
        observed = receipt(
            tmp_path,
            log,
            expected_prefix=prefix,
            selected=selected,
            newline_within_window=newline_within_window,
        )
        assert selected == expected
        check_rotation(observed)


def test_verified_snapshot_seed_survives_rotation_and_subsequent_capture(
    private_data: Path, tmp_path: Path, identities: tuple[str, str]
) -> None:
    original, later = identities
    snapshot = private_data / "snapshot-before"
    snapshot.mkdir(mode=0o700)
    with _open_runtime_log(private_data / "machine.log", ssh_host_key=original):
        save_snapshot_host_key(private_data, "machine", snapshot)
    seed = snapshot_host_key(snapshot)
    assert seed == original
    prefix = marker(original) + b"." * (WINDOW - len(marker(original)) - 1) + b"\n"
    with console(private_data, seed=seed) as (log, child):
        send(child, log, prefix[len(marker(original)) :])
        finish_with_late_key(child, log, later)
        after = private_data / "snapshot-after"
        after.mkdir(mode=0o700)
        save_snapshot_host_key(private_data, "machine", after)
        saved = snapshot_host_key(after)
        selected = trusted_host_key(private_data, "machine")
        observed = receipt(
            tmp_path, log, expected_prefix=prefix, selected=selected, captured_public_key=saved
        )
        assert saved == original
        assert selected == original
        check_rotation(observed)


def test_cold_boot_invalidates_seed_and_cache_before_a_complete_new_key(
    private_data: Path, tmp_path: Path, identities: tuple[str, str]
) -> None:
    old, new = identities
    with _open_runtime_log(private_data / "machine.log", ssh_host_key=old):
        openssh_host_key_options(private_data, "machine", "127.0.0.1", 2222)
    with console(private_data) as (log, child):
        assert trusted_host_key(private_data, "machine") is None
        partial = marker(new)[:-1]
        send(child, log, partial)
        wait_for(lambda: log.stat().st_size == len(partial), "New partial identity was not drained")
        assert trusted_host_key(private_data, "machine") is None
        send(child, log, b"\n")
        wait_for(
            lambda: trusted_host_key(private_data, "machine") == new,
            "New completed identity was not trusted",
        )
        assert child.stdin is not None
        child.stdin.close()
        assert child.wait(timeout=5) == 0
        cached = private_data / "ssh-known-hosts/machine.known_hosts"
        assert old in cached.read_text()
        (tmp_path / "cold-boot-receipt.json").write_text(
            json.dumps(
                {"old_cache_ignored": True, "new_public_key": new, "relay_exit": child.returncode}
            )
        )


def test_oversized_descriptor_normalization_preserves_original_prefix(
    private_data: Path, tmp_path: Path, identities: tuple[str, str]
) -> None:
    log = private_data / "machine.log"
    prefix = marker(identities[0]) + b"." * (WINDOW - len(marker(identities[0])) - 1) + b"\n"
    with _open_runtime_log(log, read_write=True) as handle:
        # This oversized input is intentional: exercise startup normalization,
        # separately from the ordinary producer that never exceeds its cap.
        handle.buffer.write(prefix)
        for _ in range((LIMIT - WINDOW) // CHUNK + 1):
            handle.buffer.write(b"x" * CHUNK)
        handle.buffer.write(END)
        handle.flush()
        assert log.stat().st_size > LIMIT
        child = _start_bounded_console(handle, LIMIT)
        try:
            assert child.stdin is not None
            child.stdin.close()
            assert child.wait(timeout=5) == 0
            selected = trusted_host_key(private_data, "machine")
            observed = receipt(
                tmp_path, log, expected_prefix=prefix, selected=selected, initial_oversize=True
            )
            assert selected == identities[0]
            check_rotation(observed)
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=2)


@pytest.mark.parametrize("entrypoint", ["manager", "direct"])
@pytest.mark.parametrize("limit", [1024, 4096, LIMIT - 1, True, LIMIT + 0.5])
def test_unsupported_limit_refuses_before_pipe_or_child(
    private_data: Path, tmp_path: Path, entrypoint: str, limit: int | float
) -> None:
    manager = None
    pipe = os.pipe
    popen = subprocess.Popen
    with (
        _open_runtime_log(private_data / "machine.log", read_write=True) as handle,
        patch("celesto.vm.os.pipe", wraps=pipe) as pipes,
        patch("celesto.vm.subprocess.Popen", wraps=popen) as children,
    ):
        try:
            with pytest.raises(CelestoError):
                if entrypoint == "manager":
                    manager = CelestoManager(
                        data_dir=private_data / "manager",
                        socket_dir=private_data / "sockets",
                        _qemu_log_limit_bytes=limit,
                    )
                else:
                    child = _start_bounded_console(handle, limit)
                    assert child.stdin is not None
                    child.stdin.close()
                    child.wait(timeout=5)
            assert pipes.call_count == 0
            assert children.call_count == 0
            (tmp_path / "limit-refusal-receipt.json").write_text(
                json.dumps(
                    {
                        "entrypoint": entrypoint,
                        "value": limit,
                        "pipes_created": 0,
                        "children_created": 0,
                    }
                )
            )
        finally:
            if manager is not None:
                manager.close()

"""Actual process/pipe contracts for the Android console retention ceiling.

Failure cases designed before implementation: unbounded console growth, losing
recent diagnostics on rollover, inheriting an agent credential, stopping when
the pool agent exits, and retaining a writer after QEMU EOF. These fixtures use
small supported limits; they do not qualify hostile-load control-plane headroom.

Repair regression contracts: a prepared resource group must be joined before
readiness/guest output, denied join must not start a writer, and a failed QEMU
spawn must not leave its joined console alive. The helper transport below is
simulated; process identity, exec, inherited descriptors and EOF are real.
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from celesto.runtime import _qemu_console

RELAY = Path(_qemu_console.__file__)


@pytest.mark.skipif(sys.platform != "linux", reason="Android host launcher is Linux-only")
def test_old_relay_cannot_overwrite_a_reconnected_managers_new_boot(tmp_path: Path) -> None:
    """Reconnect loses relay handles; delayed old pipe bytes must not corrupt a new boot.

    Designed before repair: stop a real ready relay, queue bytes and EOF as if
    QEMU stopped, reconstruct the actual manager, then start a new console log.
    Resume the old writer and verify the new boot remains intact. No VM, helper
    transport or production test seam is required; existing identity tests own
    symlink/hardlink and foreign-owner refusal.
    """
    import celesto.vm as runtime

    path = tmp_path / "console.log"
    relay = None
    with runtime._open_runtime_log(path, read_write=True) as old:
        try:
            relay = runtime._start_bounded_console(old, 8 * 1024**2)
            os.kill(relay.pid, signal.SIGSTOP)
            os.waitpid(relay.pid, os.WUNTRACED)
            assert relay.stdin is not None
            relay.stdin.write(b"STALE_OUTPUT\n")
            relay.stdin.close()
            manager = runtime.CelestoManager(data_dir=tmp_path / "reconnected")
            assert not manager._qemu_console_relays
            manager._close_runtime_log("vm-reconnected", "qemu")
            with runtime._open_runtime_log(path, read_write=True) as current:
                current.write("NEW_BOOT_CONTENT\n")
                current.flush()
                before = path.read_bytes()
                os.kill(relay.pid, signal.SIGCONT)
                assert relay.wait(timeout=5) == 0
                after = path.read_bytes()
            (tmp_path / "reconnected-console-receipt.json").write_text(
                json.dumps(
                    {
                        "before": before.decode(),
                        "after": after.decode(),
                        "old_relay_exited": True,
                        "real_relay_and_manager": True,
                    }
                )
            )
            assert before == after == b"NEW_BOOT_CONTENT\n"
        finally:
            if relay is not None and relay.poll() is None:
                os.kill(relay.pid, signal.SIGCONT)
                relay.kill()
                relay.wait(timeout=5)


@pytest.mark.skipif(sys.platform != "linux", reason="Android host launcher is Linux-only")
@pytest.mark.parametrize("join_allowed", [True, False])
def test_console_join_precedes_readiness_and_guest_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, join_allowed: bool
) -> None:
    import celesto.vm as runtime

    group = tmp_path / "cmp_012345abcdef"
    group.mkdir()
    members = group / "cgroup.procs"
    members.touch()
    receipt = tmp_path / "joined.txt"
    log_path = tmp_path / "console.log"
    driver = r"""
import os, pathlib, runpy, subprocess, sys
shim, receipt, allowed = sys.argv[1:4]
def join(command, **options):
    if allowed != 'yes':
        raise subprocess.CalledProcessError(1, command)
    group = pathlib.Path(sys.argv[1])
    start = pathlib.Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]
    assert command[4:] == [group.name, str(os.getpid()), start]
    pathlib.Path(group, 'cgroup.procs').write_text(str(os.getpid()))
    pathlib.Path(receipt).write_text(str(os.getpid()))
    return subprocess.CompletedProcess(command, 0)
subprocess.run = join
sys.argv = [shim, *sys.argv[4:]]
runpy.run_path(shim, run_name='__main__')
"""
    popen = subprocess.Popen

    def launch(command, **options):
        assert Path(command[2]).name == "_qemu_launch.py"
        assert command[3] == str(group)
        assert Path(command[8]).name == "_qemu_console.py"
        return popen(
            [
                sys.executable,
                "-I",
                "-c",
                driver,
                command[2],
                str(receipt),
                "yes" if join_allowed else "no",
                *command[3:],
            ],
            **options,
        )

    monkeypatch.setattr(runtime.subprocess, "Popen", launch)
    relay = None
    with log_path.open("w+") as log:
        if not join_allowed:
            with pytest.raises(runtime.CelestoError, match="console could not start"):
                runtime._start_bounded_console(
                    log, 8 * 1024**2, group=group, deadline_epoch=time.time() + 60
                )
            assert not receipt.exists()
            assert log_path.read_bytes() == b""
            return
        try:
            relay = runtime._start_bounded_console(
                log, 8 * 1024**2, group=group, deadline_epoch=time.time() + 60
            )
            assert int(receipt.read_text()) == relay.pid
            assert int(members.read_text()) == relay.pid
            assert relay.stdin is not None
            relay.stdin.write(b"after-owned-join\n")
            relay.stdin.close()
            assert relay.wait(timeout=5) == 0
            assert log_path.read_bytes() == b"after-owned-join\n"
            (tmp_path / "console-join-receipt.txt").write_text(
                f"pid={relay.pid}\njoined-before-ready=true\neof-exit=0\n"
            )
        finally:
            if relay is not None and relay.poll() is None:
                relay.kill()
                relay.wait(timeout=5)


@pytest.mark.skipif(sys.platform != "linux", reason="Android host launcher is Linux-only")
def test_console_is_bounded_retains_recent_output_and_survives_agent_exit(tmp_path: Path) -> None:
    log = tmp_path / "console.log"
    limit = 8 * 1024**2
    fd = os.open(log, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
    read_fd, write_fd = os.pipe()
    parent = r"""
import os, subprocess, sys
ready_read, ready_write = os.pipe()
p = subprocess.Popen(
    [sys.executable, '-I', sys.argv[1], sys.argv[2], sys.argv[4], str(ready_write)],
    stdin=int(sys.argv[3]), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    close_fds=True, pass_fds=(int(sys.argv[2]), ready_write), start_new_session=True,
    env={'PATH': os.defpath, 'LANG': 'C.UTF-8'},
)
os.close(ready_write)
assert os.read(ready_read, 1) == b'1'
os.close(ready_read)
print(p.pid, flush=True)
"""
    try:
        agent = subprocess.run(
            [sys.executable, "-I", "-c", parent, str(RELAY), str(fd), str(read_fd), str(limit)],
            pass_fds=(fd, read_fd),
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert agent.returncode == 0, agent.stderr
        relay_pid = int(agent.stdout.strip())
        os.close(read_fd)
        read_fd = -1
        # The parent has exited before any console bytes arrive.
        os.kill(relay_pid, 0)
        for index in range(32):
            os.write(write_fd, bytes([65 + index % 26]) * (512 * 1024))
            assert log.stat().st_size <= limit
        sentinel = b"\nlatest diagnostic after parent exit\n"
        os.write(write_fd, sentinel)
        os.close(write_fd)
        write_fd = -1
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            data = log.read_bytes()
            if data.endswith(sentinel):
                break
            time.sleep(0.01)
        assert data.endswith(sentinel)
        assert b"older console output truncated" in data
        assert len(data) <= limit
        receipt = tmp_path / "receipt.txt"
        receipt.write_text(
            f"parent-exited=true\nrelay-pid={relay_pid}\nretained={len(data)}\nlimit={limit}\n"
        )
    finally:
        os.close(fd)
        if read_fd >= 0:
            os.close(read_fd)
        if write_fd >= 0:
            os.close(write_fd)

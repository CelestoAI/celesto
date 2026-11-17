"""Real relay and file-ownership regressions designed before the repairs.

Failure inventory: close retains an already exited relay as a zombie; close
waits for or kills a still-running writer; a detached writer loses its reaping
owner after close; a waiter retains the closed manager; repeated close changes
ownership; a fresh bounded log loses the validated sudo user's uid/gid; failed
ownership transfer replaces the old file or leaks the unpublished new inode.
An ordinary owner must also keep access when the old group is no longer one of
their groups; only root can preserve that group on a new inode.

Root-only cases exercise real root/nobody permissions in an isolated container.
They do not request sudo credentials or change host users, services or files.
"""

import gc
import json
import os
import pwd
import subprocess
import sys
import tempfile
import threading
import time
import weakref
from pathlib import Path

import pytest

from celesto.vm import CelestoManager, _open_runtime_log, _start_bounded_console


def wait_until(predicate, message: str) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.005)
    raise AssertionError(message)


@pytest.mark.skipif(sys.platform != "linux", reason="relay process receipt uses /proc")
@pytest.mark.parametrize("running", [False, True], ids=["already-exited", "detached-live"])
def test_close_reaps_console_without_stopping_detached_writer(
    tmp_path: Path, running: bool
) -> None:
    manager = CelestoManager(data_dir=tmp_path / "state", backend="qemu")
    log_path = tmp_path / "console.log"
    log = _open_runtime_log(log_path, read_write=True)
    relay = _start_bounded_console(log, 8 * 1024**2)
    manager._qemu_console_relays["owned-fixture"] = relay
    manager._log_files["qemu:owned-fixture"] = log
    close_returned, watchdog_fired = threading.Event(), threading.Event()
    receipt = {"running_at_close": running, "relay_pid": relay.pid}

    def unblock_broken_close() -> None:
        # Bound a regression that incorrectly waits synchronously for EOF.
        if not close_returned.wait(5):
            watchdog_fired.set()
            relay.stdin.close()

    watchdog = threading.Thread(target=unblock_broken_close, daemon=True)
    try:
        if not running:
            relay.stdin.close()
            status = Path(f"/proc/{relay.pid}/stat")
            wait_until(
                lambda: status.read_text().rsplit(")", 1)[1].split()[0] == "Z",
                "Actual relay did not exit before close",
            )
        watchdog.start()
        manager.close()
        close_returned.set()
        manager.close()
        receipt["close_blocked_on_live_writer"] = watchdog_fired.is_set()
        receipt["manager_retains_relay"] = bool(manager._qemu_console_relays)
        assert not watchdog_fired.is_set(), receipt
        assert not manager._qemu_console_relays, receipt
        if running:
            assert relay.returncode is None and not relay.stdin.closed, receipt
            reference = weakref.ref(manager)
            manager = None
            gc.collect()
            receipt["closed_manager_collected_while_writer_runs"] = reference() is None
            assert reference() is None, receipt
            relay.stdin.write(b"output after manager close\n")
            relay.stdin.close()
            wait_until(
                lambda: relay.returncode is not None, "Detached relay was not reaped after EOF"
            )
            receipt["retained_output"] = log_path.read_text()
            assert receipt["retained_output"] == "output after manager close\n", receipt
        receipt["relay_exit"] = relay.returncode
        assert relay.returncode == 0, receipt
        assert not Path(f"/proc/{relay.pid}").exists(), receipt
    finally:
        close_returned.set()
        if relay.stdin is not None and not relay.stdin.closed:
            relay.stdin.close()
        try:
            relay.wait(timeout=5)
        except subprocess.TimeoutExpired:
            relay.kill()
            relay.wait(timeout=5)
        log.close()
        if manager is not None:
            manager.close()
        if watchdog.ident is not None:
            watchdog.join(timeout=1)
        receipt["owned_relay_reaped"] = relay.returncode is not None
        (tmp_path / "close-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")


@pytest.mark.skipif(os.geteuid() != 0, reason="real root/nobody ownership requires isolated root")
@pytest.mark.parametrize("deny_transfer", [False, True], ids=["preserve-owner", "transfer-refused"])
def test_bounded_log_preserves_validated_sudo_owner_before_replace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, deny_transfer: bool
) -> None:
    owner = pwd.getpwnam("nobody")
    monkeypatch.setenv("SUDO_USER", owner.pw_name)
    receipt = {"deny_transfer": deny_transfer, "owner": [owner.pw_uid, owner.pw_gid]}
    with tempfile.TemporaryDirectory(prefix="sudo-console-owner-") as temporary:
        directory = Path(temporary)
        os.chown(directory, owner.pw_uid, owner.pw_gid)
        path = directory / "console.log"
        path.write_text("previous owned log\n")
        path.chmod(0o600)
        os.chown(path, owner.pw_uid, owner.pw_gid)
        original = path.stat()
        if deny_transfer:

            def refuse(*_args) -> None:
                raise PermissionError("fixture ownership transfer refused")

            monkeypatch.setattr(os, "fchown", refuse)
            with (
                pytest.raises(PermissionError, match="ownership transfer refused"),
                _open_runtime_log(path, read_write=True),
            ):
                pass
            current = path.stat()
            assert current.st_ino == original.st_ino
            assert path.read_text() == "previous owned log\n"
            assert list(directory.iterdir()) == [path]
            receipt["original_inode_and_bytes_preserved"] = True
        else:
            with path.open("rb") as original_handle:
                with _open_runtime_log(path, read_write=True) as current_handle:
                    current_handle.write("new owned boot\n")
                    current_handle.flush()
                current = path.stat()
                assert current.st_ino != os.fstat(original_handle.fileno()).st_ino
            receipt["fresh_owner"] = [current.st_uid, current.st_gid]
            assert (current.st_uid, current.st_gid) == (owner.pw_uid, owner.pw_gid), receipt
            assert current.st_mode & 0o777 == 0o600
            reader = (
                "import os,sys; os.setgroups([]); os.setgid(int(sys.argv[2])); "
                "os.setuid(int(sys.argv[1])); print(open(sys.argv[3]).read(),end='')"
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-c",
                    reader,
                    str(owner.pw_uid),
                    str(owner.pw_gid),
                    str(path),
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            assert result.returncode == 0, result.stderr
            assert result.stdout == "new owned boot\n"
            receipt["original_user_can_read_new_boot"] = True
    (tmp_path / "owner-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")


@pytest.mark.skipif(os.geteuid() != 0, reason="two-user permissions require isolated root")
def test_nonroot_owner_can_replace_log_with_group_outside_current_groups(tmp_path: Path) -> None:
    import celesto.vm as runtime

    owner = pwd.getpwnam("nobody")
    with tempfile.TemporaryDirectory(prefix="ordinary-console-owner-") as temporary:
        directory = Path(temporary)
        os.chown(directory, owner.pw_uid, owner.pw_gid)
        path = directory / "console.log"
        path.write_text("old user-owned log\n")
        path.chmod(0o600)
        os.chown(path, owner.pw_uid, 0)
        before = path.stat()
        reader = (
            "import json,os,sys; from pathlib import Path; sys.path.insert(0,sys.argv[1]); "
            "from celesto.vm import _open_runtime_log; "
            "os.setgroups([]); os.setgid(int(sys.argv[3])); os.setuid(int(sys.argv[2])); "
            "path=Path(sys.argv[4]); handle=_open_runtime_log(path,read_write=True); "
            "handle.write('new ordinary boot\\n'); handle.close(); info=path.stat(); "
            "print(json.dumps({'uid':info.st_uid,'gid':info.st_gid,'mode':info.st_mode & 511,"
            "'content':path.read_text(),'groups':os.getgroups()}))"
        )
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-c",
                reader,
                str(Path(runtime.__file__).parents[1]),
                str(owner.pw_uid),
                str(owner.pw_gid),
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, result.stderr
        receipt = json.loads(result.stdout)
        assert receipt == {
            "uid": owner.pw_uid,
            "gid": owner.pw_gid,
            "mode": 0o600,
            "content": "new ordinary boot\n",
            "groups": [],
        }
        assert path.stat().st_ino != before.st_ino
    (tmp_path / "ordinary-owner-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")

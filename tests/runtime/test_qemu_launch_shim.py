"""Process-boundary contracts for joining a prepared QEMU cgroup before exec.

Failures guarded: late or expired launch; symlink substitution; absent cgroup;
PID changing between join and target; and target starting before the join. The
fake cgroup is a transport fixture, not evidence of kernel limit enforcement.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform != "linux", reason="Android host launcher is Linux-only"
)

SHIM = Path(__file__).resolve().parents[2] / "src/celesto/runtime/_qemu_launch.py"


def test_join_before_exec_preserves_owned_pid_and_receipt(tmp_path: Path) -> None:
    group = tmp_path / "cmp_123456789abc"
    group.mkdir()
    (group / "cgroup.procs").touch()
    receipt = tmp_path / "receipt.json"
    # Only the privileged helper transport is simulated in the child. Exec,
    # deadline handling, /proc identity and PID continuity are real processes;
    # the backend owns independent helper validation tests.
    driver = r"""
import os, pathlib, runpy, subprocess, sys
shim, group = sys.argv[1:3]
def join(command, **options):
    assert command[:4] == ['/usr/bin/sudo', '-n', '/usr/local/sbin/celesto-pool-vm-helper', 'join']
    assert command[4] == pathlib.Path(group).name
    assert command[5] == str(os.getpid())
    assert command[6].isdigit()
    assert options['close_fds'] is True
    assert options['env'] == {'PATH': os.defpath, 'LANG': 'C.UTF-8'}
    pathlib.Path(group, 'cgroup.procs').write_text(str(os.getpid()))
    return subprocess.CompletedProcess(command, 0)
subprocess.run = join
sys.argv = [shim, *sys.argv[2:]]
runpy.run_path(shim, run_name='__main__')
"""
    program = (
        "import json,os,pathlib,sys; "
        "p=pathlib.Path(sys.argv[1]); "
        "p.write_text(json.dumps({'pid':os.getpid(), "
        "'joined':int(pathlib.Path(sys.argv[2]).read_text())}))"
    )
    process = subprocess.Popen(
        [
            sys.executable,
            "-I",
            "-c",
            driver,
            str(SHIM),
            str(group),
            str(time.time() + 60),
            "--",
            sys.executable,
            "-I",
            "-c",
            program,
            str(receipt),
            str(group / "cgroup.procs"),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _, stderr = process.communicate(timeout=5)
    assert process.returncode == 0, stderr.decode()
    assert json.loads(receipt.read_text()) == {"pid": process.pid, "joined": process.pid}


@pytest.mark.parametrize("failure", ["expired", "missing", "symlink"])
def test_unsafe_prepared_launch_never_executes_target(tmp_path: Path, failure: str) -> None:
    group = tmp_path / "cmp_123456789abc"
    group.mkdir()
    (group / "cgroup.procs").touch()
    if failure == "missing":
        (group / "cgroup.procs").unlink()
    if failure == "symlink":
        alias = tmp_path / "alias"
        alias.symlink_to(group, target_is_directory=True)
        group = alias
    receipt = tmp_path / "must-not-exist"
    deadline = time.time() - 1 if failure == "expired" else time.time() + 60
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            str(SHIM),
            str(group),
            str(deadline),
            "--",
            sys.executable,
            "-I",
            "-c",
            "import pathlib,sys; pathlib.Path(sys.argv[1]).touch()",
            str(receipt),
        ],
        capture_output=True,
        timeout=5,
    )
    assert result.returncode != 0
    assert b"QEMU launch refused:" in result.stderr
    assert not receipt.exists()

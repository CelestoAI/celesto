"""Actual startup/pipe regressions, designed before the readiness repair.

Failure inventory: a readiness FD above 1023 rejects a healthy real relay;
timeout, EOF, an invalid byte or child death is mistaken for readiness; a failed
startup leaves a child, pipe or selector descriptor behind. Existing relay tests
use low FDs and the QEMU owner substitutes the console starter. Pressure lives
only in a disposable test process; no service/host descriptor policy is changed.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROBE = r"""
import json, os, pathlib, resource, signal, subprocess, sys, time
sys.path.insert(0, sys.argv[1])
import celesto.vm as runtime

root, mode = pathlib.Path(sys.argv[2]), sys.argv[3]
receipt = {'case': mode, 'sdk_source': runtime.__file__, 'log_limit': 8 * 1024**2}
fd_directory = '/proc/self/fd' if pathlib.Path('/proc/self/fd').is_dir() else '/dev/fd'
before = len(os.listdir(fd_directory))
reserved, children = [], []
relay = None
original_popen = subprocess.Popen
soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
receipt['nofile_before'] = [soft, hard]
receipt['child_soft_limit_changed'] = False

worker = r'''
import os, pathlib, signal, sys, time
ready, mode, started = int(sys.argv[1]), sys.argv[2], pathlib.Path(sys.argv[3])
if mode == 'timeout':
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
started.write_text('fixture child initialized\n')
if mode == 'child-death':
    os._exit(23)
if mode == 'eof':
    os.close(ready)
elif mode == 'invalid-byte':
    os.write(ready, b'0')
while True:
    time.sleep(60)
'''

def launch(command, **options):
    # Positive execution is transparent: same starter, command, relay and FDs.
    # Negative fixtures replace only the child at the process/pipe boundary.
    if mode != 'high-fd':
        ready = command[-1]
        started = root / 'fixture-started'
        command = [sys.executable, '-I', '-c', worker, ready, mode, str(started)]
    child = original_popen(command, **options)
    children.append(child)
    if mode != 'high-fd':
        deadline = time.monotonic() + 3
        while not started.exists():
            if time.monotonic() >= deadline:
                raise RuntimeError('Owned fixture child failed to initialize')
            time.sleep(.005)
    return child

try:
    if mode == 'high-fd' and soft != resource.RLIM_INFINITY and soft < 1100:
        if hard != resource.RLIM_INFINITY and hard < 1100:
            receipt['environment_blocked'] = (
                'Existing child hard limit cannot support FD 1024 plus startup headroom')
        else:
            resource.setrlimit(resource.RLIMIT_NOFILE, (1100, hard))
            receipt['child_soft_limit_changed'] = True
    if 'environment_blocked' not in receipt:
        with runtime._open_runtime_log(root / 'console.log', read_write=True) as log:
            if mode == 'high-fd':
                while not reserved or reserved[-1] < 1024:
                    reserved.append(os.open('/dev/null', os.O_RDONLY | os.O_CLOEXEC))
                receipt['highest_owned_reserved_fd'] = reserved[-1]
                receipt['readiness_fd_minimum'] = reserved[-1] + 1
            runtime.subprocess.Popen = launch
            started = time.monotonic()
            try:
                relay = runtime._start_bounded_console(log, receipt['log_limit'])
            except BaseException as error:
                receipt['error'] = {'type': type(error).__name__, 'message': str(error)}
            finally:
                receipt['startup_elapsed_seconds'] = time.monotonic() - started
                receipt['children_reaped_on_startup_return'] = all(
                    child.poll() is not None for child in children)
                receipt['stdin_closed_on_startup_return'] = all(
                    child.stdin is None or child.stdin.closed for child in children)
            if relay is not None:
                assert relay.stdin is not None
                relay.stdin.write(b'actual high descriptor relay\n')
                relay.stdin.close()
                relay.wait(timeout=5)
                receipt['output'] = (root / 'console.log').read_text()
                receipt['relay_exit'] = relay.returncode
            receipt['log_bytes'] = (root / 'console.log').stat().st_size
finally:
    runtime.subprocess.Popen = original_popen
    receipt['test_cleanup_had_to_stop_child'] = any(child.poll() is None for child in children)
    for child in children:
        if child.stdin is not None and not child.stdin.closed:
            child.stdin.close()
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=1)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=1)
    for descriptor in reserved:
        os.close(descriptor)
    receipt['children'] = [{'pid': child.pid, 'returncode': child.returncode} for child in children]
    receipt['all_children_reaped'] = all(child.poll() is not None for child in children)
    receipt['fd_count_before'] = before
    receipt['fd_count_after'] = len(os.listdir(fd_directory))
    receipt['nofile_after'] = list(resource.getrlimit(resource.RLIMIT_NOFILE))
    receipt['host_or_parent_limits_changed'] = False
    (root / 'startup-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
"""


@pytest.mark.skipif(os.name != "posix", reason="console readiness uses Unix pipes")
@pytest.mark.parametrize("case", ["high-fd", "timeout", "eof", "invalid-byte", "child-death"])
def test_actual_console_startup_readiness_and_cleanup(tmp_path: Path, case: str) -> None:
    import resource

    import celesto.vm as runtime

    imported_runtime = Path(runtime.__file__).resolve()
    parent_limits = resource.getrlimit(resource.RLIMIT_NOFILE)
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            PROBE,
            str(imported_runtime.parents[1]),
            str(tmp_path),
            case,
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    receipt = json.loads((tmp_path / "startup-receipt.json").read_text())
    assert Path(receipt["sdk_source"]).resolve() == imported_runtime
    assert resource.getrlimit(resource.RLIMIT_NOFILE) == parent_limits
    assert receipt["all_children_reaped"], receipt
    assert receipt["fd_count_after"] == receipt["fd_count_before"], receipt
    assert receipt["nofile_after"][1] == receipt["nofile_before"][1], receipt
    if "environment_blocked" in receipt:
        pytest.skip(receipt["environment_blocked"])
    assert len(receipt["children"]) == 1, receipt
    assert not receipt["test_cleanup_had_to_stop_child"], receipt
    if case == "high-fd":
        assert receipt["readiness_fd_minimum"] >= 1024
        assert "error" not in receipt, f"Actual high-FD console startup failed: {receipt}"
        assert receipt["relay_exit"] == 0
        assert receipt["output"] == "actual high descriptor relay\n"
        assert receipt["log_bytes"] <= receipt["log_limit"]
    else:
        assert receipt["children_reaped_on_startup_return"], receipt
        assert receipt["stdin_closed_on_startup_return"], receipt
        assert receipt["error"] == {
            "type": "CelestoError",
            "message": "The bounded QEMU console could not start.",
        }, receipt
        assert receipt["log_bytes"] == 0
        if case == "timeout":
            import signal

            assert receipt["startup_elapsed_seconds"] >= 5
            assert receipt["children"][0]["returncode"] == -signal.SIGKILL

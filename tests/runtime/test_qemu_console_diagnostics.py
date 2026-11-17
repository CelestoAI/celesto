"""Startup diagnostics at the real launcher/child boundary, designed before repair.

Failure inventory: the real launch shim's refusal is discarded; a verbose failed
child fills stderr before it can report readiness; capturing output retains an
unbounded buffer or file; cleanup loses child/pipe ownership; successful startup
inherits service secrets or leaves a diagnostic reader behind. The flood fixture
replaces only the spawned process, never product validation or readiness logic.
The join-refusal transport fixture substitutes the helper response and a fake
cgroup file; it exercises the real launch shim, not host kernel enforcement.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROBE = r"""
import json, os, pathlib, subprocess, sys, time
sys.path.insert(0, sys.argv[1])
import celesto.vm as runtime

root, case = pathlib.Path(sys.argv[2]), sys.argv[3]
before = len(os.listdir('/proc/self/fd'))
children, relay = [], None
original_popen = subprocess.Popen
worker = r'''
import os, signal, sys, time
signal.signal(signal.SIGTERM, signal.SIG_IGN)
remaining = 2 * 1024**2
while remaining:
    remaining -= os.write(2, b'x' * min(4096, remaining))
os.write(2, b'\nConsole fixture refused its resource budget.\n')
os.close(int(sys.argv[1]))
while True:
    time.sleep(60)
'''
join_worker = r'''
import runpy, subprocess, sys
def refuse(command, **options):
    raise subprocess.CalledProcessError(
        1, command, stderr=b'Computer allocation is no longer active.\n')
subprocess.run = refuse
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
'''

def launch(command, **options):
    if case == 'flood':
        command = [sys.executable, '-I', '-c', worker, command[-1]]
    elif case == 'join-refused':
        command = [sys.executable, '-I', '-c', join_worker, *command[2:]]
    child = original_popen(command, **options)
    children.append(child)
    return child

receipt = {'case': case, 'sdk_source': runtime.__file__}
os.environ['CELESTO_DIAGNOSTIC_TEST_SECRET'] = 'must-not-reach-console'
try:
    runtime.subprocess.Popen = launch
    with runtime._open_runtime_log(root / 'console.log', read_write=True) as log:
        options = {}
        if case == 'expired':
            options = {'group': root, 'deadline_epoch': time.time() - 1}
        elif case == 'invalid-group':
            options = {'group': pathlib.Path('relative-fixture')}
        elif case == 'join-refused':
            (root / 'cgroup.procs').write_text('')
            options = {'group': root}
        try:
            relay = runtime._start_bounded_console(log, 8 * 1024**2, **options)
        except runtime.CelestoError as error:
            receipt['error'] = str(error)
        if relay is not None:
            receipt['service_secret_inherited'] = b'CELESTO_DIAGNOSTIC_TEST_SECRET=' in (
                pathlib.Path(f'/proc/{relay.pid}/environ').read_bytes())
            relay.stdin.write(b'healthy console after diagnostics repair\n')
            relay.stdin.close()
            relay.wait(timeout=5)
        receipt['console'] = (root / 'console.log').read_text()
        receipt['children_reaped_on_return'] = all(child.poll() is not None for child in children)
        receipt['stdin_closed_on_return'] = all(
            child.stdin is None or child.stdin.closed for child in children)
        receipt['stderr_closed_on_return'] = all(
            child.stderr is None or child.stderr.closed for child in children)
finally:
    runtime.subprocess.Popen = original_popen
    for child in children:
        if child.stdin is not None and not child.stdin.closed:
            child.stdin.close()
        if child.poll() is None:
            child.kill()
        child.wait(timeout=5)
        if child.stderr is not None:
            child.stderr.close()
    receipt['fd_count_before'] = before
    receipt['fd_count_after'] = len(os.listdir('/proc/self/fd'))
    receipt['children'] = [{'pid': child.pid, 'returncode': child.returncode} for child in children]
    (root / 'diagnostic-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
"""


@pytest.mark.skipif(sys.platform != "linux", reason="process ownership receipt uses /proc")
@pytest.mark.parametrize("case", ["expired", "invalid-group", "join-refused", "flood", "healthy"])
def test_startup_keeps_bounded_diagnostics_and_reaps_child(tmp_path: Path, case: str) -> None:
    import celesto.vm as runtime

    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            PROBE,
            str(Path(runtime.__file__).parents[1]),
            str(tmp_path),
            case,
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    receipt = json.loads((tmp_path / "diagnostic-receipt.json").read_text())
    assert receipt["sdk_source"] == runtime.__file__
    assert receipt["children_reaped_on_return"], receipt
    assert receipt["stdin_closed_on_return"], receipt
    assert receipt["stderr_closed_on_return"], receipt
    assert receipt["fd_count_after"] == receipt["fd_count_before"], receipt
    if case == "healthy":
        assert "error" not in receipt, receipt
        assert not receipt["service_secret_inherited"], receipt
        assert receipt["console"] == "healthy console after diagnostics repair\n"
    else:
        prefix = "The bounded QEMU console could not start."
        assert receipt["error"].startswith(prefix), receipt
        assert len(receipt["error"]) <= len(prefix) + 1 + 4096, receipt
        expected = {
            "expired": "maximum runner lifetime expired",
            "invalid-group": "invalid cgroup path",
            "join-refused": "Computer allocation is no longer active.",
            "flood": "Console fixture refused its resource budget.",
        }[case]
        assert expected in receipt["error"], receipt
        assert receipt["console"] == ""

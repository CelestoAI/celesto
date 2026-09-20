"""Lifecycle contract independent of installed virtualization software."""

from unittest.mock import Mock

import pytest

from celesto import (
    CommandExitEvent,
    CommandOutputEvent,
    CommandResult,
    Computer,
    TerminalConnection,
)
from celesto.exceptions import CelestoError, VMNotFoundError


@pytest.fixture
def runtime(monkeypatch):
    vm = Mock(vm_id="sbx-test")
    vm.run.return_value = CommandResult(stdout="hello\n", stderr="", exit_code=0)
    vm.run_stream.return_value = iter(
        [
            CommandOutputEvent(type="stdout", data="hello\n"),
            CommandExitEvent(exit_code=0),
        ]
    )
    factory = Mock(return_value=vm)
    monkeypatch.setattr("celesto.sdk.Celesto", factory)
    monkeypatch.setattr(Computer, "_runtime_options", lambda self: self._options)
    return factory, vm


@pytest.mark.parametrize(
    "method,args",
    [
        ("publish_port", (8000,)),
        ("published_ports", ()),
        ("unpublish_port", (8000,)),
    ],
)
@pytest.mark.parametrize("state", ["fresh", "running", "attached"])
def test_local_published_ports_fail_without_partial_work(runtime, method, args, state):
    factory, vm = runtime
    if state == "attached":
        comp = Computer.get("sbx-test", local=True)
    else:
        comp = Computer(local=True)
        if state == "running":
            comp.run("echo hello")
    factory.reset_mock()
    vm.reset_mock()
    with pytest.raises(CelestoError, match=r"unavailable on local computers; use Computer\(\)"):
        getattr(comp, method)(*args)
    factory.assert_not_called()
    assert vm.mock_calls == []


def test_missing_cloud_key_and_invalid_lifetime_fail_before_allocation(runtime, monkeypatch):
    factory, _ = runtime
    monkeypatch.delenv("CELESTO_API_KEY", raising=False)
    with pytest.raises(ValueError, match="CELESTO_API_KEY"):
        Computer()
    with pytest.raises(ValueError, match="lifetime"):
        Computer(local=True, lifetime="forever")
    factory.assert_not_called()


def test_context_creates_once_and_deletes(runtime):
    factory, vm = runtime
    comp = Computer(local=True)
    assert comp.id is None
    factory.assert_not_called()
    with comp:
        assert comp.id == "sbx-test"
        assert comp.run("echo hello").stdout == "hello\n"
        comp.run("echo again")
    factory.assert_called_once()
    vm.start.assert_called_once()
    vm.delete.assert_called_once()
    comp.delete()
    vm.delete.assert_called_once()
    with pytest.raises(CelestoError, match="deleted"):
        comp.run("echo no")


def test_local_run_stream_uses_same_lazy_lifecycle(runtime):
    factory, vm = runtime
    comp = Computer(local=True)

    stream = comp.run_stream("echo hello")

    factory.assert_called_once()
    assert [(event.type, getattr(event, "data", None)) for event in stream] == [
        ("stdout", "hello\n"),
        ("exit", None),
    ]
    vm.run_stream.assert_called_once_with("echo hello", timeout=30)


def test_local_terminal_uses_same_lazy_lifecycle(runtime):
    factory, vm = runtime
    comp = Computer(local=True)

    terminal = comp.terminal()

    assert isinstance(terminal, TerminalConnection)
    assert terminal.terminal_id is None
    assert terminal.expires_at is None
    factory.assert_called_once()
    vm.start.assert_called_once()
    terminal.attach()
    vm.attach_shell.assert_called_once_with()


@pytest.mark.parametrize("terminal_id", ["", "term_", "bad", "term_!", 1])
def test_invalid_terminal_id_does_not_allocate(runtime, terminal_id):
    factory, _ = runtime

    with pytest.raises(ValueError, match="terminal_id"):
        Computer(local=True).terminal(terminal_id=terminal_id)

    factory.assert_not_called()


def test_local_terminal_reattachment_is_rejected_before_allocation(runtime):
    factory, _ = runtime

    with pytest.raises(ValueError, match="only supported for cloud"):
        Computer(local=True).terminal(terminal_id="term_existing")

    factory.assert_not_called()


def test_exceptional_exit_deletes_and_preserves_error(runtime):
    _, vm = runtime
    with pytest.raises(RuntimeError, match="body"), Computer(local=True):
        raise RuntimeError("body")
    vm.delete.assert_called_once()


def test_cleanup_failure_is_visible_and_retryable(runtime):
    _, vm = runtime
    vm.delete.side_effect = [RuntimeError("cleanup"), None]
    comp = Computer(local=True)
    with pytest.raises(ExceptionGroup) as error, comp:
        raise ValueError("body")
    assert [str(e) for e in error.value.exceptions] == ["body", "cleanup"]
    comp.delete()
    assert vm.delete.call_count == 2


def test_persistent_context_rejected_without_creation(runtime):
    factory, vm = runtime
    comp = Computer(local=True, lifetime="persistent")
    with pytest.raises(ValueError, match="Persistent"), comp:
        pass
    factory.assert_not_called()
    comp.run("echo hello")
    vm.delete.assert_not_called()
    comp.delete()


def test_start_failure_cleans_up(runtime):
    _, vm = runtime
    vm.start.side_effect = RuntimeError("boot failed")
    comp = Computer(local=True)
    with pytest.raises(RuntimeError, match="boot failed"):
        comp.run("echo hello")
    vm.delete.assert_called_once()


def test_start_and_cleanup_failure_keep_handle_for_retry(runtime):
    _, vm = runtime
    vm.start.side_effect = RuntimeError("boot failed")
    vm.delete.side_effect = [RuntimeError("cleanup"), None]
    comp = Computer(local=True)
    with pytest.raises(ExceptionGroup):
        comp.run("echo hello")
    assert comp.id == "sbx-test"
    with pytest.raises(CelestoError, match="failed to start"):
        comp.run("echo no")
    comp.delete()


def test_delete_before_creation_never_allocates(runtime):
    factory, _ = runtime
    comp = Computer(local=True)
    comp.delete()
    with pytest.raises(CelestoError, match="deleted"):
        comp.run("echo no")
    factory.assert_not_called()


def test_get_does_not_start_or_recreate_missing_computer(runtime):
    factory, vm = runtime
    comp = Computer.get("sbx-test", local=True)
    vm.start.assert_not_called()
    assert comp.id == "sbx-test"
    factory.side_effect = VMNotFoundError("missing")
    with pytest.raises(VMNotFoundError):
        Computer.get("missing", local=True)


def test_misspelled_option_rejected_without_runtime_setup():
    with pytest.raises(TypeError, match="unexpected keyword"):
        Computer(local=True, memroy=1024)


def test_invalid_command_does_not_allocate(runtime):
    factory, _ = runtime
    comp = Computer(local=True)
    with pytest.raises(ValueError, match="command"):
        comp.run("")
    with pytest.raises(ValueError, match="timeout"):
        comp.run("echo hello", timeout=0)
    factory.assert_not_called()


def test_cleanup_only_failure_can_be_retried(runtime):
    _, vm = runtime
    vm.delete.side_effect = [RuntimeError("cleanup"), None]
    comp = Computer(local=True)
    with pytest.raises(RuntimeError, match="cleanup"), comp:
        pass
    vm.close.assert_not_called()
    comp.delete()
    vm.close.assert_called_once()


def test_nested_context_does_not_delete_outer_computer(runtime):
    _, vm = runtime
    with Computer(local=True) as comp:
        with pytest.raises(ValueError, match="active"), comp:
            pass
        vm.delete.assert_not_called()
        comp.run("echo still-running")
    vm.delete.assert_called_once()


def test_already_missing_computer_can_be_deleted(runtime):
    _, vm = runtime
    comp = Computer.get("sbx-test", local=True)
    vm.delete.side_effect = VMNotFoundError("missing")
    comp.delete()
    comp.delete()
    vm.close.assert_called_once()
    vm.delete.assert_called_once()


def test_runtime_constructor_failure_leaves_no_handle(runtime):
    factory, _ = runtime
    factory.side_effect = RuntimeError("invalid config")
    comp = Computer(local=True)
    with pytest.raises(RuntimeError, match="invalid config"):
        comp.run("echo hello")
    assert comp.id is None
    comp.delete()


@pytest.mark.e2e
def test_persistent_computer_survives_creating_process(tmp_path):
    """Boot a real VM in a child and reconnect after that process exits."""
    import subprocess
    import sys

    # Record the ID even if command execution fails after provisioning, so
    # the parent can reconnect and clean up.
    script = """
from pathlib import Path
import sys
from celesto import Computer
root = Path(sys.argv[1])
comp = Computer(local=True, lifetime="persistent", data_dir=root)
try:
    result = comp.run("echo persistent-child")
    assert result.stdout.strip() == "persistent-child", result
finally:
    if comp.id:
        (root / "computer-id").write_text(comp.id)
"""
    comp = None
    try:
        child = subprocess.run(
            [sys.executable, "-c", script, str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=180,
        )
        id_file = tmp_path / "computer-id"
        if id_file.exists():
            comp = Computer.get(id_file.read_text(), local=True, data_dir=tmp_path)
        assert child.returncode == 0, child.stderr
        assert comp is not None
        assert comp.run("echo persistent-parent").stdout.strip() == "persistent-parent"
    finally:
        if comp is not None:
            comp.delete()

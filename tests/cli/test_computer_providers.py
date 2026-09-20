"""Local-first CLI selection and terminal ownership."""

import json
from unittest.mock import Mock

import pytest

from celesto.cli.main import main
from celesto.types import VMState


@pytest.fixture(autouse=True)
def isolated_state(monkeypatch, tmp_path):
    monkeypatch.setenv("SMOLVM_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("celesto.cli.commands.app._before_command", lambda **kwargs: None)


@pytest.mark.parametrize("flags", [[], ["--local"]])
@pytest.mark.parametrize("action", ["create", "list", "terminal", "delete"])
def test_local_selection(action, flags, monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.main._run_computer", handler)
    positional = ["computer-demo"] if action in {"terminal", "delete"} else []
    assert main(["computer", action, *positional, *flags]) == 0
    assert handler.call_args.args[0].provider == "local"


@pytest.mark.parametrize("action", ["create", "list", "terminal", "delete"])
def test_cloud_selection(action, monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.cloud_computers.run_cloud_computer", handler)
    positional = ["cloud-demo"] if action in {"terminal", "delete"} else []
    assert main(["computer", action, *positional, "--cloud"]) == 0
    assert handler.call_args.args[0].provider == "cloud"


def test_conflicting_flags_fail_without_dispatch(monkeypatch):
    handler = Mock()
    monkeypatch.setattr("celesto.cli.main._run_computer", handler)
    assert main(["computer", "create", "--cloud", "--local"]) == 2
    handler.assert_not_called()


def test_local_terminal_readiness_exit_code_and_close(monkeypatch):
    desktop = Mock()
    desktop.vm.attach_shell.return_value = 17
    monkeypatch.setattr("celesto.cli.main._require_display_session_mode", Mock())
    factory = Mock(return_value=desktop)
    monkeypatch.setattr("celesto.computer._ComputerSandbox.from_id", factory)
    readiness = Mock(side_effect=lambda *args, **kwargs: kwargs["wait"]())
    monkeypatch.setattr("celesto.cli.main._bring_sandbox_up", readiness)
    cloud = Mock(side_effect=AssertionError("must stay local"))
    monkeypatch.setattr("celesto.cli.cloud_computers.CloudComputer", cloud)
    assert main(["computer", "terminal", "computer-demo", "--boot-timeout", "12"]) == 17
    assert factory.call_args.args == ("computer-demo",)
    desktop.vm.wait_for_shell.assert_called_once_with(timeout=12)
    desktop.vm.attach_shell.assert_called_once_with(timeout=12)
    desktop.close.assert_called_once()
    desktop.delete.assert_not_called()
    cloud.assert_not_called()


def test_local_terminal_failure_closes_without_deleting(monkeypatch):
    desktop = Mock()
    monkeypatch.setattr("celesto.cli.main._require_display_session_mode", Mock())
    monkeypatch.setattr("celesto.computer._ComputerSandbox.from_id", Mock(return_value=desktop))
    monkeypatch.setattr("celesto.cli.main._bring_sandbox_up", Mock(side_effect=ValueError("bad")))
    assert main(["computer", "terminal", "computer-demo"]) == 1
    desktop.close.assert_called_once()
    desktop.delete.assert_not_called()
    desktop.vm.attach_shell.assert_not_called()


def test_cloud_create_is_persistent_and_closes(monkeypatch, capsys):
    handle = Mock(id="cloud-demo")
    factory = Mock(return_value=handle)
    monkeypatch.setattr("celesto.cli.cloud_computers.CloudComputer", factory)
    assert main(["computer", "create", "--cloud", "--json"]) == 0
    assert factory.call_args.kwargs["lifetime"] == "persistent"
    handle.start.assert_called_once()
    handle.close.assert_called_once()
    handle.delete.assert_not_called()
    assert json.loads(capsys.readouterr().out)["data"]["computer_id"] == "cloud-demo"


def test_cloud_terminal_closes_without_deleting(monkeypatch):
    handle = Mock()
    handle.terminal.return_value.attach.return_value = None
    factory = Mock()
    factory.get.return_value = handle
    monkeypatch.setattr("celesto.cli.cloud_computers.CloudComputer", factory)
    assert main(["computer", "terminal", "cloud-demo", "--cloud"]) == 0
    factory.get.assert_called_once_with("cloud-demo")
    handle.close.assert_called_once()
    handle.delete.assert_not_called()


def test_cloud_list_avoids_local_inventory(monkeypatch, capsys):
    monkeypatch.setattr("celesto.cli.main._cli_state_manager", Mock(side_effect=AssertionError))
    monkeypatch.setattr(
        "celesto._providers.cloud.list_cloud_computers",
        lambda: [
            {"computer_id": "cloud-demo", "status": "running"},
        ],
    )
    assert main(["computer", "list", "--cloud", "--json"]) == 0
    assert (
        json.loads(capsys.readouterr().out)["data"]["computers"][0]["computer_id"] == "cloud-demo"
    )


@pytest.mark.parametrize("action", ["open", "logs", "start", "templates"])
def test_unsupported_cloud_actions_never_run_local(action, monkeypatch):
    monkeypatch.setattr("celesto.cli.main._cli_state_manager", Mock(side_effect=AssertionError))
    positional = ["cloud-demo"] if action in {"open", "logs"} else []
    assert main(["computer", action, *positional, "--cloud"]) == 1


@pytest.mark.parametrize(
    "status", [VMState.CREATED, VMState.STOPPED, VMState.PAUSED, VMState.RUNNING]
)
def test_local_terminal_starts_or_resumes_existing_computer(status, monkeypatch):
    desktop = Mock()
    desktop.vm.status = status
    desktop.vm.attach_shell.return_value = 0
    monkeypatch.setattr("celesto.cli.main._require_display_session_mode", Mock())
    monkeypatch.setattr("celesto.computer._ComputerSandbox.from_id", Mock(return_value=desktop))
    assert main(["computer", "terminal", "computer-demo"]) == 0
    assert desktop.vm.start.call_count == int(status in {VMState.CREATED, VMState.STOPPED})
    assert desktop.vm.resume.call_count == int(status == VMState.PAUSED)
    desktop.vm.wait_for_shell.assert_called_once_with(timeout=30)
    desktop.close.assert_called_once()


def test_local_terminal_error_state_has_recovery(monkeypatch, capsys):
    desktop = Mock()
    desktop.vm.status = VMState.ERROR
    desktop.vm.vm_id = "sbx-demo"
    monkeypatch.setattr("celesto.cli.main._require_display_session_mode", Mock())
    monkeypatch.setattr("celesto.computer._ComputerSandbox.from_id", Mock(return_value=desktop))
    assert main(["computer", "terminal", "computer-demo"]) == 1
    output = " ".join(capsys.readouterr().err.replace("│", " ").split())
    assert "celesto sandbox logs sbx-demo" in output
    desktop.vm.attach_shell.assert_not_called()
    desktop.close.assert_called_once()


def test_missing_local_computer_has_recovery(capsys):
    assert main(["computer", "terminal", "missing"]) == 1
    assert "celesto computer list" in capsys.readouterr().err


def test_cloud_terminal_rejects_local_timeout(monkeypatch):
    handler = Mock()
    monkeypatch.setattr("celesto.cli.main._run_computer", handler)
    assert main(["computer", "terminal", "cloud-demo", "--cloud", "--boot-timeout", "12"]) == 2
    handler.assert_not_called()

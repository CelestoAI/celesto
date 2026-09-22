"""Local-first CLI selection and terminal ownership."""

import json
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from celesto.cli.commands.app import build_cli
from celesto.cli.main import main
from celesto.types import VMState


@pytest.fixture(autouse=True)
def isolated_state(monkeypatch, tmp_path):
    monkeypatch.setenv("CELESTO_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("celesto.cli.commands.app._before_command", lambda **kwargs: None)


@pytest.mark.parametrize("flags", [[], ["--local"]])
@pytest.mark.parametrize("action", ["create", "list", "terminal", "delete"])
def test_local_selection(action, flags, monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.main._run_computer", handler)
    positional = ["computer-demo"] if action in {"terminal", "delete"} else []
    if action == "delete":
        positional.append("--yes")
    assert main(["computer", action, *positional, *flags]) == 0
    assert handler.call_args.args[0].provider == "local"


@pytest.mark.parametrize("action", ["create", "list", "terminal", "delete"])
def test_cloud_selection(action, monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.cloud_computers.run_cloud_computer", handler)
    positional = ["cloud-demo"] if action in {"terminal", "delete"} else []
    if action == "delete":
        positional.append("--yes")
    assert main(["computer", action, *positional, "--cloud"]) == 0
    assert handler.call_args.args[0].provider == "cloud"


def test_conflicting_flags_fail_without_dispatch(monkeypatch):
    handler = Mock()
    monkeypatch.setattr("celesto.cli.main._run_computer", handler)
    assert main(["computer", "create", "--cloud", "--local"]) == 2
    handler.assert_not_called()


@pytest.mark.parametrize("flags", [[], ["--local"], ["--cloud"]])
@pytest.mark.parametrize("reply", ["n\n", "", "y\n"])
def test_delete_requires_confirmation(flags, reply, monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.main._run_computer", handler)
    result = CliRunner().invoke(build_cli(), ["computer", "delete", "demo", *flags], input=reply)
    assert "Delete" in result.output
    assert "demo" in result.output
    if reply == "y\n":
        assert result.exit_code == 0
        args = handler.call_args.args[0]
        assert (args.computer_action, args.computer_id) == ("delete", "demo")
        assert args.provider == ("cloud" if "--cloud" in flags else "local")
    else:
        assert result.exit_code != 0
        handler.assert_not_called()


@pytest.mark.parametrize("flags", [[], ["--local"], ["--cloud"]])
def test_delete_yes_skips_confirmation(flags, monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.main._run_computer", handler)
    confirm = Mock(side_effect=AssertionError("must not prompt"))
    monkeypatch.setattr("celesto.cli.commands.app.click.confirm", confirm)
    result = CliRunner().invoke(build_cli(), ["computer", "delete", "demo", *flags, "--yes"])
    assert result.exit_code == 0
    args = handler.call_args.args[0]
    assert (args.computer_action, args.computer_id) == ("delete", "demo")
    assert args.provider == ("cloud" if "--cloud" in flags else "local")
    confirm.assert_not_called()


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


def test_ssh_always_dispatches_to_cloud_terminal(monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.main._run_computer", handler)
    assert main(["computer", "ssh", "hypatia"]) == 0
    args = handler.call_args.args[0]
    assert (args.computer_action, args.computer_id, args.provider) == (
        "terminal",
        "hypatia",
        "cloud",
    )


def test_ssh_attaches_and_closes_without_deleting(monkeypatch):
    handle = Mock()
    handle.terminal.return_value.attach.return_value = None
    factory = Mock()
    factory.get.return_value = handle
    monkeypatch.setattr("celesto.cli.cloud_computers.CloudComputer", factory)
    assert main(["computer", "ssh", "hypatia"]) == 0
    factory.get.assert_called_once_with("hypatia")
    handle.close.assert_called_once()
    handle.delete.assert_not_called()


def test_stop_always_dispatches_to_cloud(monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.main._run_computer", handler)
    assert main(["computer", "stop", "hypatia"]) == 0
    args = handler.call_args.args[0]
    assert (args.computer_action, args.computer_id, args.provider) == ("stop", "hypatia", "cloud")


def test_cloud_stop_reports_status(monkeypatch, capsys):
    monkeypatch.setattr(
        "celesto._providers.cloud.stop_cloud_computer",
        lambda computer_id: {"computer_id": computer_id, "status": "stopped"},
    )
    assert main(["computer", "stop", "hypatia", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["data"] == {
        "computer_id": "hypatia",
        "status": "stopped",
    }


def test_start_with_id_forces_cloud_and_ignores_local_flag(monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.main._run_computer", handler)
    assert main(["computer", "start", "hypatia", "--local"]) == 0
    args = handler.call_args.args[0]
    assert (args.computer_action, args.computer_id, args.provider) == ("start", "hypatia", "cloud")


def test_start_without_id_keeps_local_create_default(monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.main._run_computer", handler)
    assert main(["computer", "start"]) == 0
    args = handler.call_args.args[0]
    assert (args.computer_action, args.computer_id, args.provider) == ("start", None, "local")


def test_cloud_start_without_id_fails_with_recovery(monkeypatch, capsys):
    assert main(["computer", "start", "--cloud", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert "computer create --cloud" in payload["error"]["message"]


def test_cloud_start_resumes_by_id(monkeypatch, capsys):
    monkeypatch.setattr(
        "celesto._providers.cloud.start_cloud_computer",
        lambda computer_id: {"computer_id": computer_id, "status": "running"},
    )
    assert main(["computer", "start", "hypatia", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["data"] == {
        "computer_id": "hypatia",
        "status": "running",
    }


def test_get_always_dispatches_to_cloud(monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.main._run_computer", handler)
    assert main(["computer", "get", "hypatia"]) == 0
    args = handler.call_args.args[0]
    assert (args.computer_action, args.computer_id, args.provider) == ("get", "hypatia", "cloud")


def test_run_always_dispatches_to_cloud(monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.main._run_computer", handler)
    assert main(["computer", "run", "hypatia", "uname -a"]) == 0
    args = handler.call_args.args[0]
    assert (args.computer_action, args.computer_id, args.provider) == ("run", "hypatia", "cloud")
    assert (args.run_command, args.timeout) == ("uname -a", 30)


def test_cloud_get_returns_public_fields(monkeypatch, capsys):
    monkeypatch.setattr(
        "celesto._providers.cloud.get_cloud_computer",
        lambda computer_id: {"computer_id": computer_id, "status": "running"},
    )
    assert main(["computer", "get", "hypatia", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["data"] == {
        "computer_id": "hypatia",
        "status": "running",
    }


def test_cloud_get_not_found_reports_error(monkeypatch, capsys):
    from celesto.exceptions import VMNotFoundError

    def boom(computer_id):
        raise VMNotFoundError(computer_id)

    monkeypatch.setattr("celesto._providers.cloud.get_cloud_computer", boom)
    assert main(["computer", "get", "missing", "--json"]) == 1
    assert "missing" in json.loads(capsys.readouterr().out)["error"]["message"]


def test_cloud_run_prints_stdout_and_returns_remote_exit_code(monkeypatch, capsys):
    from celesto.types import CommandResult

    handle = Mock()
    handle.run.return_value = CommandResult(exit_code=3, stdout="hi\n", stderr="")
    factory = Mock()
    factory.get.return_value = handle
    monkeypatch.setattr("celesto.cli.cloud_computers.CloudComputer", factory)

    assert main(["computer", "run", "hypatia", "uname -a"]) == 3

    factory.get.assert_called_once_with("hypatia")
    handle.run.assert_called_once_with("uname -a", timeout=30)
    assert capsys.readouterr().out == "hi\n"
    handle.close.assert_called_once()


def test_cloud_run_honors_custom_timeout(monkeypatch):
    from celesto.types import CommandResult

    handle = Mock()
    handle.run.return_value = CommandResult(exit_code=0, stdout="", stderr="")
    factory = Mock()
    factory.get.return_value = handle
    monkeypatch.setattr("celesto.cli.cloud_computers.CloudComputer", factory)

    assert main(["computer", "run", "hypatia", "uname -a", "--timeout", "90"]) == 0
    handle.run.assert_called_once_with("uname -a", timeout=90)


def test_cloud_run_json_reports_remote_exit_code(monkeypatch, capsys):
    from celesto.types import CommandResult

    handle = Mock()
    handle.run.return_value = CommandResult(exit_code=1, stdout="", stderr="boom\n")
    factory = Mock()
    factory.get.return_value = handle
    monkeypatch.setattr("celesto.cli.cloud_computers.CloudComputer", factory)

    assert main(["computer", "run", "hypatia", "false", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["data"]["exit_code"] == 1
    assert payload["data"]["stderr"] == "boom\n"

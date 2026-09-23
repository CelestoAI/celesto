"""Local-first CLI selection and terminal ownership."""

import json
from unittest.mock import Mock

import click
import pytest
from click.testing import CliRunner

from celesto.cli.commands.app import build_cli
from celesto.cli.main import main
from celesto.types import CommandResult, VMState


@pytest.fixture(autouse=True)
def isolated_state(monkeypatch, tmp_path):
    monkeypatch.setenv("CELESTO_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CELESTO_API_KEY", "test-key")
    monkeypatch.setattr("celesto.cli.commands.app._before_command", lambda **kwargs: None)


def test_computer_and_sandbox_share_one_command_tree():
    root = build_cli()
    assert root.commands["computer"] is root.commands["sandbox"]
    assert (
        root.commands["computer"].commands["snapshot"]
        is root.commands["sandbox"].commands["snapshot"]
    )
    assert root.commands["computer"].commands["port"] is root.commands["sandbox"].commands["port"]


def test_every_subcommand_is_available_under_both_nouns():
    def paths(group: click.Group, prefix: tuple[str, ...] = ()):
        for name, command in group.commands.items():
            path = (*prefix, name)
            yield path
            if isinstance(command, click.Group):
                yield from paths(command, path)

    runner = CliRunner()
    group = build_cli().commands["sandbox"]
    assert isinstance(group, click.Group)
    for path in paths(group):
        sandbox_help = runner.invoke(build_cli(), ["sandbox", *path, "--help"])
        computer_help = runner.invoke(build_cli(), ["computer", *path, "--help"])
        assert sandbox_help.exit_code == computer_help.exit_code == 0, path
        assert sandbox_help.output.splitlines()[1:] == computer_help.output.splitlines()[1:], path


def test_parse_error_json_is_identical_for_both_nouns(capsys):
    payloads = []
    for noun in ("sandbox", "computer"):
        assert main([noun, "start", "--json"]) == 2
        payloads.append(json.loads(capsys.readouterr().out))
    assert payloads[0] == payloads[1]


@pytest.mark.parametrize("noun", ["computer", "sandbox"])
@pytest.mark.parametrize("flags", [[], ["--local"]])
def test_local_create_uses_established_sandbox_handler(noun, flags, monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.main._run_create", handler)
    assert main([noun, "create", *flags]) == 0
    assert handler.call_args.args[0].command_name == "sandbox.create"


@pytest.mark.parametrize("noun", ["computer", "sandbox"])
def test_desktop_create_rejects_unsupported_backend(noun, monkeypatch):
    handler = Mock()
    monkeypatch.setattr("celesto.cli.main._run_computer", handler)
    result = CliRunner().invoke(build_cli(), [noun, "create", "--desktop", "--backend", "vz"])
    assert result.exit_code == 2
    assert "celesto computer create --desktop --backend auto" in result.output
    handler.assert_not_called()


@pytest.mark.parametrize("noun", ["computer", "sandbox"])
def test_local_list_uses_established_sandbox_handler(noun, monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.main._run_list", handler)
    assert main([noun, "list"]) == 0
    assert handler.call_args.kwargs["command_name"] == "sandbox.list"


@pytest.mark.parametrize("noun", ["computer", "sandbox"])
def test_local_exec_uses_established_sandbox_handler(noun, monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.main._run_exec", handler)
    assert main([noun, "exec", "demo", "--", "true"]) == 0
    assert handler.call_args.args[0].start is False


@pytest.mark.parametrize("noun", ["computer", "sandbox"])
def test_local_delete_uses_established_sandbox_handler(noun, monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.cleanup.run_delete", handler)
    assert main([noun, "delete", "demo"]) == 0
    assert handler.call_args.kwargs["vm_ids"] == ["demo"]


@pytest.mark.parametrize("noun", ["computer", "sandbox"])
@pytest.mark.parametrize("action", ["create", "list", "terminal", "exec", "delete"])
def test_cloud_selection_is_identical_for_both_nouns(noun, action, monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.main._run_computer", handler)
    positional = ["cloud-demo"] if action in {"terminal", "exec", "delete"} else []
    suffix = ["--", "true"] if action == "exec" else []
    confirmation = ["--yes"] if action == "delete" else []
    assert main([noun, action, *positional, "--cloud", *confirmation, *suffix]) == 0
    assert handler.call_args.args[0].provider == "cloud"


def test_conflicting_flags_fail_without_dispatch(monkeypatch):
    handler = Mock()
    monkeypatch.setattr("celesto.cli.main._run_create", handler)
    assert main(["computer", "create", "--cloud", "--local"]) == 2
    handler.assert_not_called()


@pytest.mark.parametrize("noun", ["computer", "sandbox"])
@pytest.mark.parametrize("reply", ["n\n", "y\n"])
def test_cloud_delete_requires_confirmation(noun, reply, monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.main._run_computer", handler)
    result = CliRunner().invoke(build_cli(), [noun, "delete", "demo", "--cloud"], input=reply)
    assert "Delete cloud computer 'demo'" in result.output
    if reply == "y\n":
        assert result.exit_code == 0
        assert handler.call_args.args[0].computer_action == "delete"
    else:
        assert result.exit_code != 0
        handler.assert_not_called()


@pytest.mark.parametrize("noun", ["computer", "sandbox"])
def test_cloud_delete_yes_skips_confirmation(noun, monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.main._run_computer", handler)
    confirm = Mock(side_effect=AssertionError("must not prompt"))
    monkeypatch.setattr("celesto.cli.commands.app.click.confirm", confirm)
    result = CliRunner().invoke(build_cli(), [noun, "delete", "demo", "--cloud", "--yes"])
    assert result.exit_code == 0
    assert handler.call_args.args[0].computer_action == "delete"
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


def test_cloud_exec_preserves_output_exit_and_close(monkeypatch, capsys):
    handle = Mock()
    handle.run.return_value = CommandResult(stdout="hello\n", stderr="warning\n", exit_code=7)
    factory = Mock()
    factory.get.return_value = handle
    monkeypatch.setattr("celesto.cli.cloud_computers.CloudComputer", factory)

    assert main(["computer", "exec", "cloud-demo", "--cloud", "--json", "--", "echo", "hello"]) == 7

    factory.get.assert_called_once_with("cloud-demo")
    handle.run.assert_called_once_with("echo hello", timeout=30)
    handle.close.assert_called_once()
    payload = json.loads(capsys.readouterr().out)
    assert payload["data"] == {"exit_code": 7, "stdout": "hello\n", "stderr": "warning\n"}
    assert payload["error"]["code"] == "command_failed"


def test_local_desktop_exec_starts_computer_and_preserves_exit(monkeypatch, capsys):
    desktop = Mock()
    desktop.vm.status = VMState.STOPPED
    desktop.run.return_value = CommandResult(stdout="ok\n", stderr="", exit_code=3)
    monkeypatch.setattr("celesto.cli.main._require_display_session_mode", Mock())
    monkeypatch.setattr("celesto.computer._ComputerSandbox.from_id", Mock(return_value=desktop))

    assert main(["computer", "exec", "computer-demo", "--desktop", "--json", "--", "false"]) == 3

    desktop.vm.start.assert_called_once()
    desktop.run.assert_called_once_with("false", timeout=30)
    desktop.close.assert_called_once()
    assert json.loads(capsys.readouterr().out)["data"]["exit_code"] == 3


def test_cloud_list_avoids_local_inventory(monkeypatch, capsys):
    monkeypatch.setattr("celesto.cli.main._cli_state_manager", Mock(side_effect=AssertionError))
    monkeypatch.setattr(
        "celesto._providers.cloud.list_cloud_computers",
        lambda limit: ([{"computer_id": "cloud-demo", "status": "running"}], False),
    )
    assert main(["computer", "list", "--cloud", "--json"]) == 0
    assert (
        json.loads(capsys.readouterr().out)["data"]["computers"][0]["computer_id"] == "cloud-demo"
    )


def test_cloud_list_reports_possible_truncation(monkeypatch, capsys):
    listing = Mock(return_value=([{"computer_id": "cloud-demo", "status": "running"}], True))
    monkeypatch.setattr("celesto._providers.cloud.list_cloud_computers", listing)

    assert main(["computer", "list", "--cloud", "--limit", "1", "--json"]) == 0

    listing.assert_called_once_with(limit=1)
    data = json.loads(capsys.readouterr().out)["data"]
    assert data["possibly_truncated"] is True
    assert data["limit"] == 1


def test_cloud_list_provider_marks_full_page_as_uncertain(monkeypatch):
    from celesto._providers.cloud import list_cloud_computers

    provider = Mock()
    provider._call.return_value = Mock(computers=[Mock(id="cloud-demo", status="running")], count=1)
    monkeypatch.setattr("celesto._providers.cloud.CloudProvider", Mock(return_value=provider))

    rows, possibly_truncated = list_cloud_computers(limit=1)

    assert rows == [{"computer_id": "cloud-demo", "status": "running"}]
    assert possibly_truncated is True
    assert provider._call.call_args.kwargs["limit"] == 1
    provider.close.assert_called_once()


def test_cloud_list_provider_marks_matching_count_as_uncertain(monkeypatch):
    from celesto._providers.cloud import list_cloud_computers

    provider = Mock()
    provider._call.return_value = Mock(computers=[Mock(id="cloud-demo", status="running")], count=1)
    monkeypatch.setattr("celesto._providers.cloud.CloudProvider", Mock(return_value=provider))

    rows, possibly_truncated = list_cloud_computers(limit=50)

    assert rows == [{"computer_id": "cloud-demo", "status": "running"}]
    assert possibly_truncated is True
    provider.close.assert_called_once()


@pytest.mark.parametrize("action", ["open", "logs", "templates"])
def test_unsupported_cloud_actions_never_run_local(action, monkeypatch, capsys):
    monkeypatch.setattr("celesto.cli.main._cli_state_manager", Mock(side_effect=AssertionError))
    positional = ["cloud-demo"] if action in {"open", "logs"} else []
    assert main(["computer", action, *positional, "--cloud"]) == 2
    message = capsys.readouterr().err
    assert "Celesto Cloud dashboard" in message
    assert "computer create --cloud" not in message


def test_cloud_only_errors_are_actionable(monkeypatch, capsys):
    monkeypatch.delenv("CELESTO_API_KEY")
    monkeypatch.setattr("celesto.cli._credentials.read_credentials", lambda: None)
    assert main(["computer", "list", "--cloud", "--json"]) == 1
    message = json.loads(capsys.readouterr().out)["error"]["message"]
    assert "celesto auth login" in message
    assert "api_key=" not in message


def test_missing_sandbox_exec_has_list_recovery(capsys):
    assert main(["sandbox", "exec", "missing", "--json", "--", "true"]) == 1
    message = json.loads(capsys.readouterr().out)["error"]["message"]
    assert "Sandbox 'missing'" in message
    assert "celesto sandbox list" in message


def test_unsupported_cloud_action_is_hidden_from_help(capsys):
    assert main(["computer", "logs", "--help"]) == 0
    assert "--cloud" not in capsys.readouterr().out


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
    assert main(["computer", "ssh", "hypatia", "--cloud"]) == 0
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
    assert main(["computer", "ssh", "hypatia", "--cloud"]) == 0
    factory.get.assert_called_once_with("hypatia")
    handle.close.assert_called_once()
    handle.delete.assert_not_called()


def test_stop_cloud_dispatch_is_explicit(monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.main._run_computer", handler)
    assert main(["computer", "stop", "hypatia", "--cloud"]) == 0
    args = handler.call_args.args[0]
    assert (args.computer_action, args.computer_id, args.provider) == ("stop", "hypatia", "cloud")


def test_cloud_stop_reports_status(monkeypatch, capsys):
    monkeypatch.setattr(
        "celesto._providers.cloud.stop_cloud_computer",
        lambda computer_id: {"computer_id": computer_id, "status": "stopped"},
    )
    assert main(["computer", "stop", "hypatia", "--cloud", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["data"] == {
        "computer_id": "hypatia",
        "status": "stopped",
    }


def test_start_with_id_defaults_to_local(monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.main._run_vm_start", handler)
    assert main(["computer", "start", "demo"]) == 0
    assert handler.call_args.args[0].vm_id == "demo"


def test_start_requires_id(capsys):
    assert main(["computer", "start", "--cloud", "--json"]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert "Missing argument" in payload["error"]["message"]


def test_cloud_start_resumes_by_id(monkeypatch, capsys):
    monkeypatch.setattr(
        "celesto._providers.cloud.start_cloud_computer",
        lambda computer_id: {"computer_id": computer_id, "status": "running"},
    )
    assert main(["computer", "start", "hypatia", "--cloud", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["data"] == {
        "computer_id": "hypatia",
        "status": "running",
    }


def test_port_publish_dispatches_to_cloud(monkeypatch):
    handler = Mock(return_value=0)
    monkeypatch.setattr("celesto.cli.main._run_computer", handler)
    assert main(["computer", "port", "publish", "hypatia", "--port", "8000"]) == 0
    args = handler.call_args.args[0]
    assert (args.computer_action, args.computer_id, args.port_number, args.provider) == (
        "port_publish",
        "hypatia",
        8000,
        "cloud",
    )


def test_cloud_port_publish_prints_url(monkeypatch, capsys):
    from celesto.types import PublishedPort

    handle = Mock()
    handle.publish_port.return_value = PublishedPort(
        computer_id="hypatia", port=8000, status="active", url="https://hypatia.celesto.dev:8000"
    )
    factory = Mock()
    factory.get.return_value = handle
    monkeypatch.setattr("celesto.cli.cloud_computers.CloudComputer", factory)

    assert main(["computer", "port", "publish", "hypatia", "--port", "8000"]) == 0

    handle.publish_port.assert_called_once_with(8000)
    assert capsys.readouterr().out.strip() == "https://hypatia.celesto.dev:8000"
    handle.close.assert_called_once()


def test_cloud_port_list_prints_rows(monkeypatch, capsys):
    from celesto.types import PublishedPort

    handle = Mock()
    handle.published_ports.return_value = [
        PublishedPort(
            computer_id="hypatia",
            port=8000,
            status="active",
            url="https://hypatia.celesto.dev:8000",
        )
    ]
    factory = Mock()
    factory.get.return_value = handle
    monkeypatch.setattr("celesto.cli.cloud_computers.CloudComputer", factory)

    assert main(["computer", "port", "list", "hypatia", "--cloud"]) == 0
    assert "8000" in capsys.readouterr().out


def test_cloud_port_list_empty(monkeypatch, capsys):
    handle = Mock()
    handle.published_ports.return_value = []
    factory = Mock()
    factory.get.return_value = handle
    monkeypatch.setattr("celesto.cli.cloud_computers.CloudComputer", factory)

    assert main(["computer", "port", "list", "hypatia", "--cloud"]) == 0
    assert "No published ports." in capsys.readouterr().out


def test_cloud_port_unpublish(monkeypatch, capsys):
    from celesto.types import PublishedPort

    handle = Mock()
    handle.unpublish_port.return_value = PublishedPort(
        computer_id="hypatia", port=8000, status="removed"
    )
    factory = Mock()
    factory.get.return_value = handle
    monkeypatch.setattr("celesto.cli.cloud_computers.CloudComputer", factory)

    assert main(["computer", "port", "unpublish", "hypatia", "--port", "8000"]) == 0
    handle.unpublish_port.assert_called_once_with(8000)
    assert "Unpublished port 8000" in capsys.readouterr().out


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

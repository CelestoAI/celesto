"""Regression coverage for provider boundaries and CLI failure cleanup."""

from unittest.mock import Mock

import pytest

from celesto import CloudComputer, LocalComputer
from celesto.cli.main import main


@pytest.mark.parametrize("factory", [LocalComputer, CloudComputer])
def test_failed_reconnection_closes_handle_without_deleting(factory, monkeypatch):
    error = RuntimeError("connection failed")
    adapter = Mock()
    adapter.attach.side_effect = error
    monkeypatch.setattr("celesto.sdk.make_provider", Mock(return_value=adapter))

    with pytest.raises(RuntimeError) as caught:
        factory.get("existing")

    assert caught.value is error
    adapter.close.assert_called_once()
    adapter.delete.assert_not_called()
    adapter.start.assert_not_called()


def test_cloud_options_rejected_locally_before_state_setup(monkeypatch):
    runtime_options = Mock(side_effect=AssertionError("must not set up local state"))
    monkeypatch.setattr("celesto._providers.local.LocalProvider._runtime_options", runtime_options)

    with pytest.raises(TypeError):
        LocalComputer(api_key="cloud-only-key")

    runtime_options.assert_not_called()


@pytest.fixture
def cloud_cli(monkeypatch, tmp_path):
    monkeypatch.setenv("SMOLVM_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("celesto.cli.commands.app._before_command", lambda **kwargs: None)
    handle = Mock(id="cloud-existing")
    factory = Mock(return_value=handle)
    factory.get.return_value = handle
    monkeypatch.setattr("celesto.cli.cloud_computers.CloudComputer", factory)
    return factory, handle


def test_cloud_delete_failure_closes_and_does_not_retry(cloud_cli, capsys):
    factory, handle = cloud_cli
    handle.delete.side_effect = RuntimeError("deletion failed")

    assert main(["computer", "delete", "cloud-existing", "--cloud"]) == 1

    factory.get.assert_called_once_with("cloud-existing")
    handle.delete.assert_called_once()
    handle.close.assert_called_once()
    assert "deletion failed" in capsys.readouterr().err


def test_cloud_terminal_failure_preserves_computer(cloud_cli, capsys):
    _, handle = cloud_cli
    handle.terminal.return_value.attach.side_effect = RuntimeError("terminal disconnected")

    assert main(["computer", "terminal", "cloud-existing", "--cloud"]) == 1

    handle.close.assert_called_once()
    handle.delete.assert_not_called()
    assert "terminal disconnected" in capsys.readouterr().err


def test_cloud_create_failure_closes_handle_and_reports_json(cloud_cli, capsys):
    import json

    _, handle = cloud_cli
    handle.start.side_effect = RuntimeError("creation failed")

    assert main(["computer", "create", "--cloud", "--json"]) == 1

    handle.close.assert_called_once()
    # The SDK owns cleanup after startup failure; the CLI must not replay it.
    handle.delete.assert_not_called()
    result = json.loads(capsys.readouterr().out)
    assert "creation failed" in str(result)

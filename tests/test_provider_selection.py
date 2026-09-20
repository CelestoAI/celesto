"""Provider selection must be explicit, stable, and independent of credentials."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from celesto import CloudComputer, Computer, LocalComputer
from celesto._providers.local import LocalProvider
from celesto.exceptions import BrowserSessionNotFoundError, VMNotFoundError


@pytest.mark.parametrize("factory", [Computer, LocalComputer])
def test_default_local_does_not_construct_cloud(factory, monkeypatch):
    monkeypatch.setenv("CELESTO_API_KEY", "present-but-irrelevant")
    cloud = Mock(side_effect=AssertionError("cloud must not be constructed"))
    monkeypatch.setattr("celesto._providers.cloud.CloudProvider", cloud)
    computer = factory()
    assert computer.provider == "local"
    assert computer.id is None
    computer.delete()
    cloud.assert_not_called()


@pytest.mark.parametrize(
    "factory,options",
    [
        (Computer, {"provider": "unknown"}),
        (Computer, {"provider": "cloud", "local": True}),
        (Computer, {"provider": "local", "local": False}),
        (Computer, {"local": "yes"}),
        (LocalComputer, {"provider": "cloud"}),
        (CloudComputer, {"provider": "local"}),
        (CloudComputer, {"local": True}),
    ],
)
def test_conflicts_fail_before_adapter_construction(factory, options, monkeypatch):
    make = Mock(side_effect=AssertionError("must validate first"))
    monkeypatch.setattr("celesto.sdk.make_provider", make)
    with pytest.raises(ValueError):
        factory(**options)
    with pytest.raises(ValueError):
        factory.get("existing", **options)
    make.assert_not_called()


@pytest.mark.parametrize(
    "factory,options,expected",
    [
        (Computer, {}, "local"),
        (LocalComputer, {}, "local"),
        (CloudComputer, {}, "cloud"),
        (Computer, {"provider": "cloud"}, "cloud"),
        (Computer, {"local": False}, "cloud"),
        (Computer, {"local": True}, "local"),
    ],
)
def test_reconnection_preserves_provider_and_subclass(factory, options, expected, monkeypatch):
    adapter = Mock(id="existing")
    make = Mock(return_value=adapter)
    monkeypatch.setattr("celesto.sdk.make_provider", make)
    handle = factory.get("existing", **options)
    assert type(handle) is factory
    assert handle.provider == expected
    assert handle.lifetime == "persistent"
    assert handle.id == "existing"
    make.assert_called_once_with(expected, {})
    adapter.attach.assert_called_once_with("existing")
    handle.run("echo hello")
    adapter.start.assert_not_called()
    with pytest.raises(ValueError, match="Persistent"):
        handle.__enter__()
    handle.close()
    adapter.delete.assert_not_called()


def test_local_desktop_reconnect_preserves_public_id_and_user(monkeypatch):
    state = Mock()
    state.get_browser_session_config.return_value = SimpleNamespace(mode="computer")
    desktop = Mock(computer_id="computer-demo")
    desktop.vm.vm_id = "sbx-underlying"
    factory = Mock(return_value=desktop)
    monkeypatch.setattr("celesto.computer._ComputerSandbox.from_id", factory)
    monkeypatch.setattr(LocalProvider, "_runtime_options", lambda self: {"state_manager": state})
    computer = Computer.get("computer-demo")
    assert computer.id == "computer-demo"
    desktop.start.assert_not_called()
    desktop.vm.start.assert_not_called()
    computer.run("whoami")
    desktop.run.assert_called_once_with("whoami", timeout=30)
    computer.run_stream("whoami")
    desktop.vm.run_stream.assert_called_once_with(
        "runuser -u agent -- sh -lc whoami", timeout=30, shell="raw"
    )
    computer.delete()
    desktop.delete.assert_called_once()
    desktop.close.assert_called_once()


def test_desktop_reconnect_rejects_unsupported_connection_options(monkeypatch):
    state = Mock()
    state.get_browser_session_config.return_value = SimpleNamespace(mode="computer")
    monkeypatch.setattr(
        LocalProvider,
        "_runtime_options",
        lambda self: {"state_manager": state, **self._options},
    )
    with pytest.raises(ValueError, match="ssh_user.*omit those options and retry"):
        Computer.get("computer-demo", ssh_user="root")


def test_browser_id_rejected_without_vm_lookup(monkeypatch):
    state = Mock()
    state.get_browser_session_config.return_value = SimpleNamespace(mode="browser")
    monkeypatch.setattr(LocalProvider, "_runtime_options", lambda self: {"state_manager": state})
    local = Mock()
    monkeypatch.setattr("celesto._providers.local.Celesto", local)
    with pytest.raises(ValueError, match="celesto computer list"):
        Computer.get("browser-demo")
    local.assert_not_called()


def test_missing_local_id_never_falls_back_to_cloud(monkeypatch):
    state = Mock()
    state.get_browser_session.side_effect = BrowserSessionNotFoundError("missing")
    monkeypatch.setattr(LocalProvider, "_runtime_options", lambda self: {"state_manager": state})
    local = Mock(side_effect=VMNotFoundError("missing"))
    monkeypatch.setattr("celesto._providers.local.Celesto", local)
    cloud = Mock(side_effect=AssertionError("no fallback"))
    monkeypatch.setattr("celesto._providers.cloud.CloudProvider", cloud)
    with pytest.raises(VMNotFoundError):
        Computer.get("missing")
    cloud.assert_not_called()


def test_close_does_not_delete_and_start_provisions_once(monkeypatch):
    adapter = Mock(id=None)
    monkeypatch.setattr("celesto.sdk.make_provider", Mock(return_value=adapter))
    computer = Computer(lifetime="persistent")
    computer.start().start()
    adapter.start.assert_called_once()
    computer.close()
    adapter.close.assert_called_once()
    adapter.delete.assert_not_called()

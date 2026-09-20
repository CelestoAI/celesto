"""Local connection contracts, including ownership and failure recovery."""

import json
from dataclasses import FrozenInstanceError
from unittest.mock import MagicMock

import httpx
import pytest

from celesto import BrowserConnection, CelestoError, Computer, DisplayConnection, _connections
from celesto.types import CommandResult, VMState


@pytest.fixture
def runtime(monkeypatch):
    vm = MagicMock()
    vm.vm_id = "sbx-connection"
    vm.refresh.return_value = vm
    vm.status = VMState.RUNNING
    vm.expose_local.return_value = 45123
    vm.run.side_effect = [
        CommandResult(
            stdout=json.dumps(
                {"version": 1, "browser": True, "read_only": True, "read_write": True}
            ),
            stderr="",
            exit_code=0,
        ),
        CommandResult(stdout='{"port":9223}', stderr="", exit_code=0),
    ]
    monkeypatch.setattr("celesto.browser._guest_browser_proxy_endpoint", lambda _: None)
    monkeypatch.setattr(_connections, "_forward_alive", lambda _: True)
    return vm


def mock_cdp(monkeypatch, *, status=200, body=None):
    requests = []
    real_client = httpx.Client

    def respond(request):
        requests.append(request)
        return httpx.Response(
            status,
            json=body
            or {"webSocketDebuggerUrl": "ws://guest-internal:9223/devtools/browser/unique"},
        )

    monkeypatch.setattr(
        _connections.httpx,
        "Client",
        lambda **kwargs: real_client(**kwargs, transport=httpx.MockTransport(respond)),
    )
    return requests


def test_browser_returns_forwarded_websocket_not_guest_address(runtime, monkeypatch):
    requests = mock_cdp(monkeypatch)
    forwards = {}
    result = _connections.local_connection(runtime, "browser", forwards)
    assert result == BrowserConnection("ws://127.0.0.1:45123/devtools/browser/unique", None)
    assert requests[0].url.path == "/json/version"
    assert forwards == {9223: 45123}
    runtime.expose_local.assert_called_once_with(9223, host_port=None, guest_loopback=True)
    runtime.start.assert_not_called()
    runtime.delete.assert_not_called()


@pytest.mark.parametrize("mode,port", [("read_only", 6081), ("read_write", 6082)])
def test_display_modes_use_independent_endpoints(runtime, mode, port):
    runtime.run.side_effect = [
        CommandResult(stdout=json.dumps({"version": 1, mode: True}), stderr="", exit_code=0),
        CommandResult(stdout=json.dumps({"port": port}), stderr="", exit_code=0),
    ]
    result = _connections.local_connection(runtime, mode, {})
    assert result == DisplayConnection("ws://127.0.0.1:45123/", None, mode)
    runtime.expose_local.assert_called_once_with(port, host_port=None, guest_loopback=True)


def test_capability_failure_opens_no_forward_and_preserves_vm(runtime):
    runtime.run.side_effect = [
        CommandResult(stdout='{"version":1,"browser":false}', stderr="", exit_code=0)
    ]
    with pytest.raises(CelestoError, match="does not support"):
        _connections.local_connection(runtime, "browser", {})
    runtime.expose_local.assert_not_called()
    runtime.delete.assert_not_called()
    assert runtime.run.call_count == 1


@pytest.mark.parametrize("previous", [None, 45123])
def test_discovery_failure_rolls_back_only_new_forward(runtime, monkeypatch, previous):
    mock_cdp(monkeypatch, body={"webSocketDebuggerUrl": "wss://secret@evil.example/path"})
    forwards = {9223: previous} if previous else {}
    with pytest.raises(CelestoError) as exc:
        _connections.local_connection(runtime, "browser", forwards)
    assert "secret" not in str(exc.value)
    if previous is None:
        runtime.unexpose_local.assert_called_once_with(45123, 9223)
        assert not forwards
    else:
        runtime.unexpose_local.assert_not_called()
        assert forwards == {9223: previous}


def test_repeated_browser_request_rediscovers_without_new_forward(runtime, monkeypatch):
    mock_cdp(monkeypatch)
    replies = list(runtime.run.side_effect)
    runtime.run.side_effect = replies * 2
    forwards = {}
    assert _connections.local_connection(
        runtime, "browser", forwards
    ) == _connections.local_connection(runtime, "browser", forwards)
    assert runtime.expose_local.call_args_list[-1].kwargs["host_port"] == 45123


@pytest.mark.parametrize("status", [VMState.STOPPED, VMState.CREATED])
def test_attach_does_not_start_stopped_vm(runtime, status):
    runtime.status = status
    with pytest.raises(CelestoError, match="not running"):
        _connections.local_connection(runtime, "browser", {})
    runtime.run.assert_not_called()
    runtime.start.assert_not_called()


def test_secret_connection_fields_are_immutable_and_hidden():
    for value in (
        BrowserConnection("secret", None),
        DisplayConnection("secret", None, "read_only"),
    ):
        assert "secret" not in repr(value) + str(value)
        with pytest.raises(FrozenInstanceError):
            value.url = "changed"


@pytest.mark.parametrize(
    "options",
    [
        {"template_id": "missing"},
        {"template_id": "browser-agent", "os": "alpine"},
        {"template_id": "browser-agent", "disk_size": 0},
        {"template_id": "browser-agent", "disk_size": 4096},
        {"template_id": "browser-agent", "template_version": "latest"},
    ],
)
def test_invalid_local_template_options_fail_before_provisioning(options, monkeypatch):
    build = MagicMock()
    monkeypatch.setattr("celesto.browser._build_browser_vm_config", build)
    with pytest.raises(ValueError):
        Computer(local=True, **options)
    build.assert_not_called()


def test_local_template_validation_is_lazy():
    comp = Computer(local=True, template_id="browser-agent", memory=2048, disk_size=8192)
    assert comp.id is None
    comp.delete()


def test_dead_forward_is_replaced(runtime, monkeypatch):
    mock_cdp(monkeypatch)
    monkeypatch.setattr(_connections, "_forward_alive", lambda _: False)
    forwards = {9223: 45122}
    _connections.local_connection(runtime, "browser", forwards)
    runtime.unexpose_local.assert_called_once_with(45122, 9223)
    runtime.expose_local.assert_called_once_with(9223, host_port=None, guest_loopback=True)
    assert forwards == {9223: 45123}


def test_restricted_network_fails_before_starting_services(runtime):
    runtime.info.config.internet_settings.has_explicit_restrictions = True
    runtime.info.config.backend = "firecracker"
    with pytest.raises(CelestoError, match="network configuration"):
        _connections.local_connection(runtime, "browser", {})
    assert runtime.run.call_count == 1  # Capability probe only, no service start.
    runtime.expose_local.assert_not_called()


def test_public_local_methods_share_runtime_and_id(runtime, monkeypatch):
    monkeypatch.setattr("celesto.sdk.Celesto", MagicMock(return_value=runtime))
    comp = Computer(local=True)
    connection = MagicMock(return_value=BrowserConnection("ws://local", None))
    monkeypatch.setattr(_connections, "local_connection", connection)
    assert comp.browser().url == "ws://local"
    connection.return_value = DisplayConnection("ws://local-display", None, "read_only")
    assert comp.display().mode == "read_only"
    assert comp.id == "sbx-connection"
    assert connection.call_args.args[0] is runtime
    runtime.start.assert_called_once()
    comp.delete()
    with pytest.raises(CelestoError, match="deleted"):
        comp.browser()

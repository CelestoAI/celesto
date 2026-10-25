"""Local connection contracts, including ownership and failure recovery."""

import json
import os
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any, Literal
from unittest.mock import MagicMock, call

import httpx
import pytest

from celesto import BrowserConnection, CelestoError, Computer, DisplayConnection, _connections
from celesto._providers.local import LocalProvider
from celesto.types import CommandResult, VMState

_TOKEN = "a" * 64


@pytest.fixture
def runtime(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
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
        CommandResult(
            stdout=json.dumps({"port": 9222, "capability": _TOKEN}), stderr="", exit_code=0
        ),
    ]
    monkeypatch.setattr("celesto.browser._guest_browser_proxy_endpoint", lambda _: None)
    monkeypatch.setattr(_connections, "_forward_alive", lambda _: True)
    return vm


def mock_cdp(
    monkeypatch: pytest.MonkeyPatch, *, status: int = 200, body: dict[str, object] | None = None
) -> list[httpx.Request]:
    requests: list[httpx.Request] = []
    real_client = httpx.Client

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            status,
            json=body
            or {
                "webSocketDebuggerUrl": f"ws://guest-internal:9222/{_TOKEN}/devtools/browser/unique"
            },
        )

    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kwargs: real_client(**kwargs, transport=httpx.MockTransport(respond)),
    )
    return requests


def test_browser_returns_forwarded_websocket_not_guest_address(
    runtime: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    requests = mock_cdp(monkeypatch)
    forwards: dict[int, int] = {}
    result = _connections.local_connection(runtime, "browser", forwards)
    assert result == BrowserConnection(
        f"ws://127.0.0.1:45123/{_TOKEN}/devtools/browser/unique", None
    )
    assert requests[0].url.path == f"/{_TOKEN}/json/version"
    assert forwards == {9222: 45123}
    runtime.expose_local.assert_called_once_with(9222, host_port=None, guest_loopback=False)
    runtime.start.assert_not_called()
    runtime.delete.assert_not_called()


@pytest.mark.parametrize("mode,port", [("read_only", 6081), ("read_write", 6082)])
def test_display_modes_use_independent_endpoints(
    runtime: MagicMock, mode: Literal["read_only", "read_write"], port: int
) -> None:
    runtime.run.side_effect = [
        CommandResult(stdout=json.dumps({"version": 1, mode: True}), stderr="", exit_code=0),
        CommandResult(
            stdout=json.dumps({"port": port, "capability": _TOKEN}), stderr="", exit_code=0
        ),
    ]
    result = _connections.local_connection(runtime, mode, {})
    assert result == DisplayConnection(f"ws://127.0.0.1:45123/{_TOKEN}/", None, mode)
    runtime.expose_local.assert_called_once_with(port, host_port=None, guest_loopback=False)


def test_capability_failure_opens_no_forward_and_preserves_vm(runtime: MagicMock) -> None:
    runtime.run.side_effect = [
        CommandResult(stdout='{"version":1,"browser":false}', stderr="", exit_code=0)
    ]
    with pytest.raises(CelestoError, match="does not support"):
        _connections.local_connection(runtime, "browser", {})
    runtime.expose_local.assert_not_called()
    runtime.delete.assert_not_called()
    assert runtime.run.call_count == 1


@pytest.mark.parametrize("previous", [None, 45123])
def test_discovery_failure_rolls_back_only_new_forward(
    runtime: MagicMock, monkeypatch: pytest.MonkeyPatch, previous: int | None
) -> None:
    mock_cdp(monkeypatch, body={"webSocketDebuggerUrl": "wss://secret@evil.example/path"})
    forwards = {9222: previous} if previous else {}
    with pytest.raises(CelestoError) as exc:
        _connections.local_connection(runtime, "browser", forwards)
    assert "secret" not in str(exc.value)
    if previous is None:
        runtime.unexpose_local.assert_called_once_with(45123, 9222)
        assert not forwards
    else:
        runtime.unexpose_local.assert_not_called()
        assert forwards == {9222: previous}


def test_repeated_browser_request_rediscovers_without_new_forward(
    runtime: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    mock_cdp(monkeypatch)
    replies = list(runtime.run.side_effect)
    runtime.run.side_effect = replies * 2
    forwards: dict[int, int] = {}
    assert _connections.local_connection(
        runtime, "browser", forwards
    ) == _connections.local_connection(runtime, "browser", forwards)
    assert runtime.expose_local.call_args_list[-1].kwargs["host_port"] == 45123


@pytest.mark.parametrize("status", [VMState.STOPPED, VMState.CREATED])
def test_attach_does_not_start_stopped_vm(runtime: MagicMock, status: VMState) -> None:
    runtime.status = status
    with pytest.raises(CelestoError, match="not running"):
        _connections.local_connection(runtime, "browser", {})
    runtime.run.assert_not_called()
    runtime.start.assert_not_called()


def test_secret_connection_fields_are_immutable_and_hidden() -> None:
    for value in (
        BrowserConnection("secret", None),
        DisplayConnection("secret", None, "read_only"),
    ):
        assert "secret" not in repr(value) + str(value)
        with pytest.raises(FrozenInstanceError):
            field = "url"
            setattr(value, field, "changed")


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
def test_invalid_local_template_options_fail_before_provisioning(
    options: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    build = MagicMock()
    monkeypatch.setattr("celesto.browser._build_browser_vm_config", build)
    with pytest.raises(ValueError):
        Computer(local=True, **options)
    build.assert_not_called()


def test_local_template_validation_is_lazy() -> None:
    comp = Computer(local=True, template_id="browser-agent", memory=2048, disk_size=8192)
    assert comp.id is None
    comp.delete()


def test_dead_forward_is_replaced(runtime: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    mock_cdp(monkeypatch)
    monkeypatch.setattr(_connections, "_forward_alive", lambda _: False)
    forwards = {9222: 45122}
    _connections.local_connection(runtime, "browser", forwards)
    runtime.unexpose_local.assert_called_once_with(45122, 9222)
    runtime.expose_local.assert_called_once_with(9222, host_port=None, guest_loopback=False)
    assert forwards == {9222: 45123}


def test_restricted_network_fails_before_starting_services(runtime: MagicMock) -> None:
    runtime.info.config.internet_settings.has_explicit_restrictions = True
    runtime.info.config.backend = "firecracker"
    with pytest.raises(CelestoError, match="network configuration"):
        _connections.local_connection(runtime, "browser", {})
    assert runtime.run.call_count == 1  # Capability probe only, no service start.
    runtime.expose_local.assert_not_called()


def test_public_local_methods_share_runtime_and_id(
    runtime: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("celesto._providers.local.Celesto", MagicMock(return_value=runtime))
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


def test_close_releases_only_attached_handle_resources(
    runtime: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    other_runtime = MagicMock(vm_id="sbx-connection")
    monkeypatch.setattr(
        "celesto._providers.local.Celesto", MagicMock(side_effect=[runtime, other_runtime])
    )
    owner = Computer.get("sbx-connection", local=True)
    attached = Computer.get("sbx-connection", local=True)
    assert isinstance(attached._provider, LocalProvider)
    attached._provider._connection_forwards[9222] = 45123
    attached.close()
    assert other_runtime.method_calls == [
        call._cleanup_local_forwards(),
        call.close(),
    ]
    assert attached._provider._connection_forwards == {}
    assert runtime.method_calls == []
    assert owner.id == attached.id
    attached.close()  # Repeated release never deletes or stops the computer.
    other_runtime.delete.assert_not_called()
    other_runtime.stop.assert_not_called()


def test_close_unstarted_local_computer_does_not_allocate(monkeypatch: pytest.MonkeyPatch) -> None:
    factory = MagicMock()
    monkeypatch.setattr("celesto._providers.local.Celesto", factory)
    computer = Computer(local=True)
    computer.close()
    factory.assert_not_called()


def test_close_unstarted_cloud_computer_releases_http_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cloud = MagicMock()
    monkeypatch.setattr("celesto._providers.cloud.CloudProvider", MagicMock(return_value=cloud))
    computer = Computer(provider="cloud")
    computer.close()
    cloud.close.assert_called_once()
    cloud.start.assert_not_called()
    cloud.delete.assert_not_called()


def test_guest_helper_supplies_system_path_for_raw_commands(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from celesto.images import guest_connections

    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    monkeypatch.setattr(sys, "argv", ["helper", "capabilities"])

    def capabilities() -> dict[str, int | bool]:
        # runuser lives in /usr/sbin on the supported Debian desktop image.
        assert "/usr/sbin" in os.environ["PATH"].split(":")
        return {"version": 1, "browser": True}

    monkeypatch.setattr(guest_connections, "capabilities", capabilities)
    assert guest_connections.main() == 0
    assert json.loads(capsys.readouterr().out)["browser"] is True


def test_guest_helper_uses_legacy_browser_paths_on_published_images(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    legacy_session = Path("/usr/local/bin/smolvm-browser-session")
    legacy_root = Path("/opt/smolvm-browser")

    monkeypatch.setattr(
        Path,
        "is_file",
        lambda path: path == legacy_session,
    )
    monkeypatch.setattr(
        Path,
        "is_dir",
        lambda path: path == legacy_root,
    )
    namespace: dict[str, object] = {"__name__": "guest_helper_test"}
    exec(
        compile(
            Path("src/celesto/images/guest_connections.py").read_text(),
            "guest_connections.py",
            "exec",
        ),
        namespace,
    )
    assert str(namespace["_BROWSER_SESSION"]) == str(legacy_session)
    assert str(namespace["_BROWSER_ROOT"]) == str(legacy_root)


def test_connection_forwards_only_authenticated_gateway(
    runtime: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    mock_cdp(monkeypatch)
    result = _connections.local_connection(runtime, "browser", {})
    assert result.url.startswith(f"ws://127.0.0.1:45123/{_TOKEN}/")
    runtime.expose_local.assert_called_once_with(9222, host_port=None, guest_loopback=False)
    runtime._ensure_ssh_for_operation.assert_not_called()

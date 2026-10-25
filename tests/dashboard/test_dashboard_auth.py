"""Exercise authentication before dashboard handlers touch inventory."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from celesto.dashboard import server
from celesto.types import VMInfo


def test_dashboard_requires_capability_and_rejects_foreign_origin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(server.app.state, "auth_token", "owner-secret", raising=False)
    client = TestClient(server.app)
    assert client.get("/api/health").status_code == 401
    assert client.get("/api/health", headers={"Authorization": "Bearer wrong"}).status_code == 401
    authorized = {"Authorization": "Bearer owner-secret"}
    assert client.get("/api/health", headers=authorized).status_code == 200
    assert (
        client.post(
            "/api/vms/victim/stop", headers={**authorized, "Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    with (
        pytest.raises(WebSocketDisconnect),
        client.websocket_connect("/api/stream", headers={"Origin": "https://evil.example"}),
    ):
        pass


def test_dashboard_login_never_grants_ambient_cookie_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(server.app.state, "auth_token", "owner-secret", raising=False)
    client = TestClient(server.app)
    page = client.get("/login")
    assert page.status_code == 200
    assert "owner-secret" not in page.text
    assert (
        client.post(
            "/api/session",
            headers={"Origin": "http://testserver", "Authorization": "Bearer owner-secret"},
        ).status_code
        == 204
    )
    assert not client.cookies
    assert client.get("/api/health").status_code == 401
    client.cookies.set("celesto_dashboard", "owner-secret")
    assert client.get("/api/health").status_code == 401
    assert client.get("/api/health", headers={"Origin": "https://evil.example"}).status_code == 403


def test_dashboard_websocket_requires_origin_bound_capability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from celesto.dashboard.connection_manager import ConnectionManager

    class Inventory:
        def list_vms(self) -> list[VMInfo]:
            return []

    monkeypatch.setattr(server.app.state, "auth_token", "owner-secret", raising=False)
    monkeypatch.setattr(server, "_get_conn_manager", lambda _app: ConnectionManager())
    monkeypatch.setattr(server, "_get_state_manager", lambda _app: Inventory())
    client = TestClient(server.app)
    for origin, protocol in [
        ("http://testserver", "celesto-auth.wrong"),
        ("https://other.example", "celesto-auth.owner-secret"),
    ]:
        with (
            pytest.raises(WebSocketDisconnect),
            client.websocket_connect(
                "/api/stream", headers={"Origin": origin}, subprotocols=[protocol]
            ),
        ):
            pass
    with client.websocket_connect(
        "/api/stream",
        headers={"Origin": "http://testserver"},
        subprotocols=["celesto-dashboard-v1", "celesto-auth.owner-secret"],
    ) as websocket:
        assert websocket.accepted_subprotocol == "celesto-dashboard-v1"
        assert websocket.receive_json() == {"type": "snapshot", "vms": []}


def test_dashboard_rejects_stale_bundle_and_serves_public_auth_bootstrap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(server, "_ui_dist", tmp_path)
    monkeypatch.setattr(server.app.state, "auth_token", "owner-secret", raising=False)
    index = tmp_path / "index.html"
    index.write_text("<html>Old dashboard</html>")
    client = TestClient(server.app)
    assert client.get("/").status_code == 503
    index.write_text('<html><meta name="celesto-dashboard-auth-v1">New dashboard</html>')
    response = client.get("/")
    assert response.status_code == 200
    assert "New dashboard" in response.text
    assert "owner-secret" not in response.text


@pytest.mark.parametrize("compatible", [False, True])
def test_dashboard_update_preserves_working_bundle_until_compatible(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, compatible: bool
) -> None:
    # The release lookup is external, but extraction and publication use real files.
    # Regressions: an older release must not replace a working local auth build;
    # a compatible release must still install and update its cached tag.
    import io
    import tarfile

    target = tmp_path / "ui" / "dist"
    target.mkdir(parents=True)
    current = '<meta name="celesto-dashboard-auth-v1">Local build'
    (target / "index.html").write_text(current)
    incoming = '<meta name="celesto-dashboard-auth-v1">Release' if compatible else "Old release"

    def download(_url: str, destination: Path) -> None:
        with tarfile.open(destination, "w:gz") as archive:
            member = tarfile.TarInfo("dist/index.html")
            payload = incoming.encode()
            member.size = len(payload)
            archive.addfile(member, io.BytesIO(payload))

    monkeypatch.setattr(server, "_latest_dashboard_release_asset", lambda **_: ("v1", "unused"))
    monkeypatch.setattr(server, "_download_asset", download)
    assert server._ensure_latest_dashboard_ui_dist(target) is compatible
    assert (target / "index.html").read_text() == (incoming if compatible else current)
    assert (target.parent / ".dashboard-ui-tag").exists() is compatible

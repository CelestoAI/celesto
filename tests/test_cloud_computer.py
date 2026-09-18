"""Exercise the public facade through real generated code and mock HTTP only."""

import json
from types import SimpleNamespace

import httpx
import pytest

from celesto import CelestoError, CloudAPIError, Computer, VMNotFoundError
from celesto._cloud import _CloudComputer
from celesto._generated.client import AuthenticatedClient


def computer(status="running"):
    return {
        "id": "cloud-test",
        "name": "trial",
        "status": status,
        "vcpus": 2,
        "ram_mb": 2048,
        "disk_size_mb": 10240,
        "image": "ubuntu-desktop-24.04",
        "created_at": "2026-09-19T00:00:00Z",
    }


@pytest.fixture
def cloud(monkeypatch):
    monkeypatch.setenv("CELESTO_API_KEY", "test-key")
    requests = []
    replies = []

    def respond(request):
        requests.append(request)
        assert request.headers["authorization"] == "Bearer test-key"
        reply = replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        code, body = reply
        return httpx.Response(code, json=body)

    def make_client(**kwargs):
        return AuthenticatedClient(**kwargs, httpx_args={"transport": httpx.MockTransport(respond)})

    monkeypatch.setattr("celesto._cloud.AuthenticatedClient", make_client)
    monkeypatch.setattr("celesto._cloud.time.sleep", lambda seconds: None)
    return requests, replies


def test_cloud_context_runs_and_confirms_cleanup(cloud):
    requests, replies = cloud
    replies.extend(
        [
            (201, computer("creating")),
            (200, computer()),
            (200, {"stdout": "hello\n", "stderr": "", "exit_code": 0}),
            (200, computer("deleting")),
            (404, {}),
        ]
    )
    comp = Computer(organization_id="org-test", vcpus=2)
    assert comp.id is None and not requests
    with comp:
        assert comp.run("echo hello").stdout == "hello\n"
    assert comp.id == "cloud-test"
    assert [r.method for r in requests] == ["POST", "GET", "POST", "DELETE", "GET"]
    assert all(r.headers["x-current-organization"] == "org-test" for r in requests)
    assert json.loads(requests[0].content)["vcpus"] == 2
    comp.delete()
    with pytest.raises(CelestoError, match="deleted"):
        comp.run("again")
    assert not replies


def test_persistent_rejects_context_without_allocating(cloud):
    requests, replies = cloud
    comp = Computer(lifetime="persistent")
    with pytest.raises(ValueError, match="Persistent"), comp:
        pass
    assert not requests
    replies.extend([(201, computer()), (200, {"stdout": "", "stderr": "oops", "exit_code": 2})])
    assert comp.run("false").exit_code == 2
    assert [r.method for r in requests] == ["POST", "POST"]
    # Persistence controls resource ownership, not the external-volume option.
    assert json.loads(requests[0].content)["external_volume_enabled"] is False


def test_attach_does_not_create_or_start(cloud):
    requests, replies = cloud
    replies.append((200, computer()))
    comp = Computer.get("cloud-test")
    assert comp.id == "cloud-test"
    assert [r.method for r in requests] == ["GET"]
    with pytest.raises(ValueError, match="Persistent"), comp:
        pass


def test_attach_missing_does_not_recreate(cloud):
    requests, replies = cloud
    replies.append((404, {}))
    with pytest.raises(VMNotFoundError):
        Computer.get("cloud-test")
    assert len(requests) == 1


def test_create_timeout_never_replayed(cloud):
    requests, replies = cloud
    replies.append(httpx.ReadTimeout("lost response"))
    comp = Computer()
    with pytest.raises(CelestoError, match="unknown"):
        comp.run("hello")
    with pytest.raises(CelestoError):
        comp.run("hello")
    assert len(requests) == 1 and comp.id is None


def test_run_transport_error_never_replayed(cloud):
    requests, replies = cloud
    replies.extend(
        [(201, computer()), httpx.ReadTimeout("lost response"), (200, computer("deleted"))]
    )
    with pytest.raises(CelestoError, match="unknown"), Computer() as comp:
        comp.run("charge-card")
    assert [r.method for r in requests] == ["POST", "POST", "DELETE"]


@pytest.mark.parametrize("status", [401, 403, 422, 429, 500])
def test_api_errors_are_typed(cloud, status):
    requests, replies = cloud
    payload = (
        {"detail": "Validation error", "errors": [], "status_code": 422} if status == 422 else {}
    )
    replies.append((status, payload))
    with pytest.raises(CloudAPIError) as exc:
        Computer().run("echo hi")
    assert exc.value.status_code == status and len(requests) == 1


def test_start_failure_deletes_allocated_resource(cloud):
    requests, replies = cloud
    replies.extend([(201, computer("error")), (200, computer("deleted"))])
    with pytest.raises(CelestoError, match="error"):
        Computer().run("echo hi")
    assert [r.method for r in requests] == ["POST", "DELETE"]


def test_body_and_cleanup_failure_retained_and_retryable(cloud):
    requests, replies = cloud
    replies.extend([(201, computer()), (503, {}), (200, computer("deleted"))])
    comp = Computer()
    with pytest.raises(ExceptionGroup) as exc, comp:
        raise RuntimeError("body")
    assert isinstance(exc.value.exceptions[0], RuntimeError)
    assert isinstance(exc.value.exceptions[1], CloudAPIError)
    comp.delete()
    assert [r.method for r in requests] == ["POST", "DELETE", "DELETE"]


def test_delete_conflict_is_polled_not_success(cloud):
    requests, replies = cloud
    replies.extend([(200, computer()), (409, {}), (200, computer("deleting")), (404, {})])
    Computer.get("cloud-test").delete()
    assert [r.method for r in requests] == ["GET", "DELETE", "GET", "GET"]


def test_delete_timeout_keeps_handle_retryable(cloud):
    _, replies = cloud
    replies.extend([(200, computer()), (200, computer("deleting")), (200, computer("deleted"))])
    comp = Computer.get("cloud-test", cleanup_timeout=0.0000001)
    with pytest.raises(CelestoError, match="in time"):
        comp.delete()
    comp.delete()


def test_delete_conflict_followed_by_completed_deletion_succeeds(cloud):
    requests, replies = cloud
    replies.extend([(200, computer()), (409, {}), (200, computer("deleted"))])
    comp = Computer.get("cloud-test")
    comp.delete()
    comp.delete()
    assert [r.method for r in requests] == ["GET", "DELETE", "GET"]


def test_invalid_cloud_command_does_not_allocate(cloud):
    requests, _ = cloud
    comp = Computer()
    for command, timeout in [("x" * 10001, 30), ("hello", 301)]:
        with pytest.raises(ValueError):
            comp.run(command, timeout=timeout)
    comp.delete()
    assert not requests


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "https://example.com/v1",
        "https://user@example.com",
        "https://example.com?key=x",
    ],
)
def test_unsafe_endpoint_rejected(cloud, url):
    with pytest.raises(ValueError, match="base_url"):
        Computer(base_url=url)


def test_local_only_options_rejected_for_cloud(cloud):
    with pytest.raises(TypeError, match="mounts"):
        Computer(mounts=["."])


def test_bad_response_is_not_retried(cloud):
    requests, replies = cloud
    replies.append((201, {}))
    with pytest.raises(CelestoError, match="invalid response"):
        Computer().run("echo hi")
    assert len(requests) == 1


def test_no_unbounded_wait(cloud):
    adapter = _CloudComputer(startup_timeout=1)
    with pytest.raises(CelestoError, match="in time"):
        adapter._wait(0, "start")


def test_startup_poll_timeout_cleans_allocated_computer(cloud, monkeypatch):
    requests, replies = cloud
    replies.extend([(201, computer("creating")), (200, computer("deleted"))])
    ticks = iter([0, 0, 2, 2])
    monkeypatch.setattr(
        "celesto._cloud.time",
        SimpleNamespace(monotonic=lambda: next(ticks), sleep=lambda seconds: None),
    )
    comp = Computer(startup_timeout=1)
    with pytest.raises(CelestoError, match="in time"):
        comp.run("echo hi")
    assert comp.id == "cloud-test"
    assert [r.method for r in requests] == ["POST", "DELETE"]

"""Exercise the public facade through real generated code and mock HTTP only."""

import json
from types import SimpleNamespace

import httpx
import pytest

from _celesto_cloud_api.client import AuthenticatedClient
from celesto import (
    CelestoError,
    CloudAPIError,
    CommandExitEvent,
    CommandOutputEvent,
    CommandStartedEvent,
    Computer,
    PublishedPort,
    VMNotFoundError,
)
from celesto._cloud import _CloudComputer


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
        if isinstance(reply, httpx.Response):
            return reply
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


def published_port(**overrides):
    return {
        "computer_id": "cloud-test",
        "port": 8000,
        "status": "published",
        "id": "route-test",
        "url": "https://route.example.test",
        "created_at": "2026-09-19T00:00:00Z",
        **overrides,
    }


def test_cloud_published_port_lifecycle_and_reconnection(cloud):
    requests, replies = cloud
    route = published_port()
    removed = published_port(status="unpublished")
    replies.extend(
        [
            (201, computer()),
            (200, route),
            (200, computer()),
            (200, [route, published_port(port=9000, id="other")]),
            (200, removed),
            (200, []),
            (200, {"computer_id": "cloud-test", "port": 8000, "status": "unpublished"}),
            (200, computer("deleting")),
            (404, {}),
        ]
    )
    comp = Computer(organization_id="org-test")
    assert comp.id is None and not requests
    with comp:
        result = comp.publish_port(8000)
        assert type(result) is PublishedPort
        assert result.model_dump() == route
        attached = Computer.get(comp.id, organization_id="org-test")
        routes = attached.published_ports()
        assert [r.port for r in routes] == [8000, 9000]
        assert all(type(r) is PublishedPort for r in routes)
        assert attached.unpublish_port(8000).model_dump() == removed
        assert attached.published_ports() == []
        absent = attached.unpublish_port(8000)
        assert absent.status == "unpublished"
        assert absent.url is absent.id is absent.created_at is None
        attached._cloud.close()
    assert [r.method for r in requests] == [
        "POST",
        "POST",
        "GET",
        "GET",
        "DELETE",
        "GET",
        "DELETE",
        "DELETE",
        "GET",
    ]
    assert [r.url.path for r in requests[1:7]] == [
        "/v1/computers/cloud-test/published-ports",
        "/v1/computers/cloud-test",
        "/v1/computers/cloud-test/published-ports",
        "/v1/computers/cloud-test/published-ports/8000",
        "/v1/computers/cloud-test/published-ports",
        "/v1/computers/cloud-test/published-ports/8000",
    ]
    assert json.loads(requests[1].content) == {"port": 8000, "force": False}
    assert all(r.headers["x-current-organization"] == "org-test" for r in requests)
    assert not replies


@pytest.mark.parametrize("method", ["publish_port", "unpublish_port"])
@pytest.mark.parametrize("port", [True, False, None, "8000", 8000.0, -1, 0, 1023, 65536])
def test_invalid_published_port_never_allocates(cloud, method, port):
    requests, _ = cloud
    comp = Computer()
    with pytest.raises(ValueError, match="integer from 1024 to 65535"):
        getattr(comp, method)(port)
    assert comp.id is None and not requests


@pytest.mark.parametrize("method", ["publish_port", "unpublish_port"])
@pytest.mark.parametrize("port", [1024, 65535])
def test_published_port_bounds_are_valid(cloud, method, port):
    requests, replies = cloud
    replies.extend([(201, computer()), (200, published_port(port=port))])
    assert getattr(Computer(), method)(port).port == port
    assert len(requests) == 2 and not replies


@pytest.mark.parametrize(
    "method,args",
    [
        ("publish_port", (8000,)),
        ("published_ports", ()),
        ("unpublish_port", (8000,)),
    ],
)
def test_published_ports_reject_deleted_and_failed_handles(cloud, method, args):
    requests, _ = cloud
    comp = Computer()
    comp.delete()
    with pytest.raises(CelestoError, match="deleted"):
        getattr(comp, method)(*args)
    failed = Computer()
    failed._failed = True
    with pytest.raises(CelestoError, match="failed to start"):
        getattr(failed, method)(*args)
    assert not requests


@pytest.mark.parametrize(
    "method,args",
    [
        ("publish_port", (8000,)),
        ("published_ports", ()),
        ("unpublish_port", (8000,)),
    ],
)
@pytest.mark.parametrize("status", [400, 401, 403, 404, 409, 422, 500, 502])
def test_published_port_errors_are_typed_sanitized_and_not_replayed(cloud, method, args, status):
    requests, replies = cloud
    body = {"detail": "credential-secret", "body": "secret"}
    if status == 422:
        body = {
            "detail": "Validation error",
            "errors": [{"input": "credential-secret"}],
            "status_code": 422,
        }
    replies.extend([(201, computer()), (status, body)])
    error_type = VMNotFoundError if status == 404 else CloudAPIError
    with pytest.raises(error_type) as exc:
        getattr(Computer(), method)(*args)
    assert "secret" not in str(exc.value)
    assert "secret" not in repr(exc.value.details)
    if status != 404:
        assert exc.value.status_code == status
    assert len(requests) == 2 and not replies


def test_publish_port_policy_rejection_names_safe_recovery(cloud):
    requests, replies = cloud
    replies.extend(
        [
            (201, computer()),
            (400, {"detail": "credential-secret: reserved by internal service"}),
        ]
    )

    with pytest.raises(
        CloudAPIError,
        match=r"HTTP 400\. Port 2049 cannot be published; choose another port and retry\.",
    ) as exc:
        Computer().publish_port(2049)

    assert "credential-secret" not in str(exc.value)
    assert exc.value.details == {}
    assert len(requests) == 2 and not replies


@pytest.mark.parametrize(
    "method,args",
    [
        ("publish_port", (8000,)),
        ("published_ports", ()),
        ("unpublish_port", (8000,)),
    ],
)
def test_published_port_transport_errors_are_not_replayed(cloud, method, args):
    requests, replies = cloud
    replies.extend([(201, computer()), httpx.ReadTimeout("credential-secret")])
    comp = Computer()
    with pytest.raises(CelestoError, match="outcome may be unknown") as exc:
        getattr(comp, method)(*args)
    assert "credential-secret" not in str(exc.value)
    assert comp.id == "cloud-test"
    assert len(requests) == 2 and not replies


@pytest.mark.parametrize("metadata", [{}, {"id": None, "url": None, "created_at": None}])
def test_published_port_normalizes_optional_metadata(cloud, metadata):
    _, replies = cloud
    replies.extend(
        [
            (201, computer()),
            (
                200,
                {
                    "computer_id": "cloud-test",
                    "port": 8000,
                    "status": "future-status",
                    "token": "credential-secret",
                    **metadata,
                },
            ),
        ]
    )
    route = Computer().publish_port(8000)
    assert route.id is route.url is route.created_at is None
    assert route.status == "future-status"
    assert "token" not in route.model_dump()


@pytest.mark.parametrize(
    "method,args",
    [
        ("publish_port", (8000,)),
        ("published_ports", ()),
        ("unpublish_port", (8000,)),
    ],
)
@pytest.mark.parametrize(
    "bad_route",
    [
        {},
        None,
        "credential-secret",
        published_port(port=True),
        published_port(port="8000"),
        published_port(port=65536),
        published_port(url={"token": "credential-secret"}),
        published_port(status=None),
        published_port(computer_id=42),
    ],
)
def test_malformed_published_port_responses_are_sanitized(cloud, method, args, bad_route):
    requests, replies = cloud
    body = [bad_route] if method == "published_ports" else bad_route
    replies.extend([(201, computer()), (200, body)])
    with pytest.raises(CelestoError, match="invalid") as exc:
        getattr(Computer(), method)(*args)
    assert "credential-secret" not in str(exc.value)
    if method in {"publish_port", "unpublish_port"}:
        assert "operation may have succeeded" in str(exc.value)
        assert "call published_ports() before retrying" in str(exc.value)
    else:
        assert "may have succeeded" not in str(exc.value)
    assert len(requests) == 2 and not replies


@pytest.mark.parametrize("body", [{}, "", None, 123])
def test_port_list_rejects_non_lists(cloud, body):
    _, replies = cloud
    replies.extend([(201, computer()), (200, body)])
    with pytest.raises(CelestoError, match="response"):
        Computer().published_ports()


def test_published_port_hides_url_and_is_immutable():
    from pydantic import ValidationError

    route = PublishedPort(**published_port(url="https://route.example.test/?token=secret"))
    assert "secret" not in repr(route)
    assert "secret" not in str(route)
    assert route.url.endswith("token=secret")
    with pytest.raises(ValidationError):
        route.port = 9000


def test_cloud_run_stream_yields_typed_events(cloud):
    requests, replies = cloud
    stream = (
        'data: {"type":"started","command_id":"cmd-1",'
        '"started_at_unix_ms":1,"timeout_seconds":30}\n'
        'data: {"type":"stdout","data":"hello\\n"}\n'
        'data: {"type":"stderr","data":"warning\\n"}\n'
        'data: {"type":"exit","exit_code":0,"command_id":"cmd-1",'
        '"timed_out":false}\n'
    )
    replies.extend(
        [
            (201, computer()),
            httpx.Response(200, text=stream, headers={"content-type": "text/event-stream"}),
        ]
    )

    events = list(Computer(organization_id="org-test").run_stream("echo hello"))

    assert [type(event) for event in events] == [
        CommandStartedEvent,
        CommandOutputEvent,
        CommandOutputEvent,
        CommandExitEvent,
    ]
    assert [event.type for event in events] == ["started", "stdout", "stderr", "exit"]
    assert requests[1].url.path == "/v1/computers/cloud-test/exec/stream"
    assert requests[1].headers["x-current-organization"] == "org-test"
    assert json.loads(requests[1].content) == {"command": "echo hello", "timeout": 30}


def test_cloud_run_stream_rejects_incomplete_stream(cloud):
    _, replies = cloud
    replies.extend(
        [
            (201, computer()),
            httpx.Response(
                200,
                text='data: {"type":"stdout","data":"partial"}\n\n',
                headers={"content-type": "text/event-stream"},
            ),
        ]
    )

    with pytest.raises(CelestoError, match="before the command exited"):
        list(Computer().run_stream("echo hello"))


def test_cloud_run_stream_transport_error_is_not_replayed(cloud):
    requests, replies = cloud
    replies.extend([(201, computer()), httpx.ReadTimeout("stream lost")])

    with pytest.raises(CelestoError, match="may still be running"):
        list(Computer(lifetime="persistent").run_stream("charge-card"))

    assert [request.method for request in requests] == ["POST", "POST"]


def test_cloud_run_stream_retains_only_documented_bad_request_detail(cloud):
    _, replies = cloud
    replies.extend(
        [
            (201, computer()),
            httpx.Response(400, json={"detail": "Invalid command", "private": "hidden"}),
        ]
    )

    with pytest.raises(CloudAPIError) as exc:
        list(Computer(lifetime="persistent").run_stream("echo hello"))

    assert exc.value.status_code == 400
    assert exc.value.details == {"detail": "Invalid command"}


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
        with pytest.raises(ValueError):
            comp.run_stream(command, timeout=timeout)
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


@pytest.mark.parametrize("detail", ["Unsupported image", "x" * 700])
def test_bad_request_retains_only_bounded_detail(cloud, detail):
    _, replies = cloud
    replies.append((400, {"detail": detail, "unrelated": "must not escape"}))
    with pytest.raises(CloudAPIError) as exc:
        Computer().run("echo hi")
    assert exc.value.status_code == 400
    assert exc.value.details == {"detail": detail[:500]}
    assert str(exc.value) == (
        "Cloud API returned HTTP 400. Check the request and cloud dashboard before retrying."
    )


@pytest.mark.parametrize(
    "body",
    [
        b"not JSON",
        b"[]",
        b"null",
        b"{}",
        b'{"detail": {"secret": "hidden"}}',
        b'{"detail": ["hidden"]}',
        b'{"detail": 42}',
        b'{"detail": null}',
    ],
)
def test_bad_request_does_not_forward_arbitrary_body(cloud, body):
    _, replies = cloud
    replies.append(httpx.Response(400, content=body))
    with pytest.raises(CloudAPIError) as exc:
        Computer().run("echo hi")
    assert exc.value.status_code == 400
    assert exc.value.details == {}


@pytest.mark.parametrize("status", [401, 403, 422, 500])
def test_other_error_statuses_do_not_retain_detail(cloud, status):
    _, replies = cloud
    body = {
        "detail": "Validation error" if status == 422 else "private diagnostic",
        "errors": [],
        "status_code": status,
        "unrelated": "must not escape",
    }
    replies.append((status, body))
    with pytest.raises(CloudAPIError) as exc:
        Computer().run("echo hi")
    assert exc.value.status_code == status
    assert exc.value.details == {}


def test_cloud_error_bounds_direct_constructor_detail():
    assert CloudAPIError(400, detail="x" * 501).details == {"detail": "x" * 500}
    assert CloudAPIError(500, detail="hidden").details == {}


def test_documented_bad_request_response_retains_bounded_detail(cloud):
    adapter = _CloudComputer()
    response = SimpleNamespace(
        status_code=400, content=b'{"detail": "Invalid option", "extra": "hidden"}', parsed=None
    )
    with pytest.raises(CloudAPIError) as exc:
        adapter._call(lambda **kwargs: response, object)
    assert exc.value.details == {"detail": "Invalid option"}

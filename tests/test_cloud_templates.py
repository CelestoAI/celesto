"""Exercise the public Template class through real generated code and mock HTTP only."""

import json
import re
from pathlib import Path

import httpx
import pytest

from _celesto_cloud_api.client import AuthenticatedClient
from celesto import (
    CelestoError,
    CloudAPIError,
    CloudComputer,
    Template,
    TemplateBuildError,
    ValidationError,
)

BASE = "https://api.celesto.ai"


def template(status="queued", **overrides):
    data = {
        "id": "tpl_abc123",
        "name": "data-env",
        "organization_id": "org-1",
        "created_by": "user-1",
        "base_template_id": "coding-agent",
        "base_template_version": "v1",
        "build_script": "pip install pandas",
        "status": status,
        "default_vcpus": 2,
        "default_ram_mb": 4096,
        "default_disk_size_mb": 30720,
        "created_at": "2026-10-21T00:00:00Z",
        "updated_at": "2026-10-21T00:00:00Z",
        "warnings": [],
    }
    data.update(overrides)
    return data


def log(status, text, offset, size, **extra):
    """A /logs response body."""
    return {
        "template_id": "tpl_abc123",
        "status": status,
        "log": text,
        "offset": offset,
        "size": size,
        **extra,
    }


def detail(code, message):
    return {"detail": {"error_code": code, "message": message}}


@pytest.fixture
def cloud(monkeypatch):
    """Answer requests from a queue; check every request exists in the OpenAPI snapshot."""
    monkeypatch.setenv("CELESTO_API_KEY", "test-key")
    requests = []
    replies = []
    clock = [1000.0]
    sleeps = []

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

    def fake_sleep(seconds):
        sleeps.append(seconds)
        clock[0] += seconds

    monkeypatch.setattr("celesto._cloud.AuthenticatedClient", make_client)
    monkeypatch.setattr("celesto.templates.time.sleep", fake_sleep)
    monkeypatch.setattr("celesto.templates.time.monotonic", lambda: clock[0])
    yield requests, replies, sleeps

    schema_path = Path(__file__).resolve().parents[1] / "openapi" / "cloud.json"
    paths = json.loads(schema_path.read_text())["paths"]
    for request in requests:
        assert any(
            request.method.lower() in operations
            and re.fullmatch(
                "".join(
                    "[^/]+" if part.startswith("{") else re.escape(part)
                    for part in re.split(r"(\{[^{}]+\})", path)
                ),
                request.url.raw_path.decode().split("?")[0],
            )
            for path, operations in paths.items()
        ), f"{request.method} {request.url.path} is absent from the cloud OpenAPI schema"


def loaded(cloud, status="queued", **overrides):
    """A Template loaded with get(), leaving the reply queue empty."""
    requests, replies, _ = cloud
    replies.append((200, template(status, **overrides)))
    result = Template.get("tpl_abc123")
    requests.clear()
    return result


# --- create, get, list, lint --------------------------------------------------


def test_create_sends_script_base_and_computer_size(cloud):
    requests, replies, _ = cloud
    replies.append(
        (
            201,
            template(warnings=[{"line": 1, "code": "apt_without_yes", "message": "add -y"}]),
        )
    )

    created = Template.create(
        name="data-env",
        build_script="apt-get install ffmpeg",
        base_template_id="coding-agent",
        vcpus=2,
        ram_mb=4096,
        disk_size_mb=30720,
        organization_id="org-1",
    )

    assert requests[0].method == "POST"
    assert requests[0].url.path == "/v1/templates"
    assert requests[0].headers["x-current-organization"] == "org-1"
    assert json.loads(requests[0].content) == {
        "name": "data-env",
        "build_script": "apt-get install ffmpeg",
        "base_template_id": "coding-agent",
        "default_vcpus": 2,
        "default_ram_mb": 4096,
        "default_disk_size_mb": 30720,
    }
    assert created.id == "tpl_abc123"
    assert created.status == "queued"
    assert (created.vcpus, created.ram_mb, created.disk_size_mb) == (2, 4096, 30720)
    assert [w.code for w in created.warnings] == ["apt_without_yes"]
    assert created.warnings[0].line == 1


def test_create_leaves_base_and_size_to_the_api_when_omitted(cloud):
    requests, replies, _ = cloud
    replies.append((201, template()))

    Template.create(name="data-env", build_script="pip install pandas")

    assert json.loads(requests[0].content) == {
        "name": "data-env",
        "build_script": "pip install pandas",
    }


def test_create_rejects_a_partial_size_before_calling_the_api(cloud):
    requests, _, _ = cloud

    with pytest.raises(ValidationError, match="together"):
        Template.create(name="x", build_script="true", vcpus=2)
    assert requests == []


def test_constructing_a_template_directly_is_not_supported():
    with pytest.raises(TypeError, match="Template.create"):
        Template()


@pytest.mark.parametrize(
    "call",
    [
        lambda: Template.list(),
        lambda: Template.lint("true"),
        lambda: Template.create(name="x", build_script="true"),
    ],
    ids=["list", "lint", "create"],
)
def test_collection_404_says_templates_are_not_enabled(cloud, call):
    _, replies, _ = cloud
    replies.append((404, {"detail": "Not Found"}))

    with pytest.raises(CloudAPIError, match="not enabled") as excinfo:
        call()
    assert excinfo.value.status_code == 404


def test_get_404_names_the_missing_template(cloud):
    _, replies, _ = cloud
    replies.append((404, detail("template_not_found", "Template not found")))

    with pytest.raises(CloudAPIError, match="tpl_missing") as excinfo:
        Template.get("tpl_missing")
    assert "not enabled" not in str(excinfo.value)


def test_template_ids_are_escaped_in_the_url(cloud):
    requests, replies, _ = cloud
    replies.append((404, detail("template_not_found", "Template not found")))

    with pytest.raises(CloudAPIError):
        Template.get("../computers/cmp_1")
    assert requests[0].url.raw_path == b"/v1/templates/..%2Fcomputers%2Fcmp_1"


def test_list_and_lint(cloud):
    requests, replies, _ = cloud
    replies.extend(
        [
            (200, {"templates": [template()], "count": 1}),
            (
                200,
                {"warnings": [{"line": 1, "code": "file_reference", "message": "list packages"}]},
            ),
        ]
    )

    templates = Template.list()
    warnings = Template.lint("pip install -r requirements.txt", base_template_id="scratch")

    assert [t.id for t in templates] == ["tpl_abc123"]
    assert warnings[0].code == "file_reference"
    assert json.loads(requests[1].content) == {
        "build_script": "pip install -r requirements.txt",
        "base_template_id": "scratch",
    }


def test_validation_errors_name_each_field(cloud):
    _, replies, _ = cloud
    replies.append(
        (
            422,
            {
                "detail": "Validation error",
                "errors": [
                    {
                        "type": "string_pattern_mismatch",
                        "loc": ["body", "name"],
                        "msg": "String should match pattern '^[a-z]+$'",
                    }
                ],
            },
        )
    )

    with pytest.raises(CloudAPIError) as excinfo:
        Template.create(name="bad/name!", build_script="true")
    assert excinfo.value.status_code == 422
    # The name rule is stated in plain words, not as the API's pattern.
    assert "name: use only letters, digits, spaces, dots, underscores and dashes" in str(
        excinfo.value
    )
    assert "pattern" not in str(excinfo.value)


def test_unknown_base_keeps_the_api_explanation(cloud):
    _, replies, _ = cloud
    replies.append(
        (
            400,
            detail("unknown_base_template", "Unknown sandbox template 'gpu'; expected scratch"),
        )
    )

    with pytest.raises(CloudAPIError, match="Unknown sandbox template 'gpu'"):
        Template.create(name="x", build_script="true", base_template_id="gpu")


def test_create_explains_the_concurrent_build_limit(cloud):
    _, replies, _ = cloud
    replies.append((429, detail("template_build_limit", "busy")))

    with pytest.raises(CloudAPIError, match="2 template builds"):
        Template.create(name="x", build_script="true")


def test_duplicate_name_says_to_choose_another(cloud):
    _, replies, _ = cloud
    replies.append((409, detail("template_name_taken", "A template named 'x' already exists")))

    with pytest.raises(CloudAPIError, match="already exists") as excinfo:
        Template.create(name="x", build_script="true")
    assert excinfo.value.status_code == 409


# --- wait() and log following -------------------------------------------------


def test_wait_without_on_log_polls_the_template(cloud):
    t = loaded(cloud)
    requests, replies, _ = cloud
    replies.extend([(200, template("building")), (200, template("ready"))])

    assert t.wait() is t
    assert t.status == "ready"
    assert [r.url.path for r in requests] == ["/v1/templates/tpl_abc123"] * 2


def test_wait_with_on_log_makes_one_request_per_poll_and_streams_new_text(cloud):
    t = loaded(cloud)
    requests, replies, _ = cloud
    replies.extend(
        [
            (200, log("building", "step 1\n", 0, 7)),
            (200, log("building", "", 7, 7, unchanged=True)),
            (200, log("ready", "step 1\nstep 2\n", 0, 14)),
            (200, template("ready")),
        ]
    )
    chunks = []

    t.wait(on_log=chunks.append)

    assert chunks == ["step 1\n", "step 2\n"]
    assert [r.url.path for r in requests] == ["/v1/templates/tpl_abc123/logs"] * 3 + [
        "/v1/templates/tpl_abc123"
    ]
    assert "known_size" not in requests[0].url.params
    assert requests[1].url.params["known_size"] == "7"


def test_wait_delivers_a_character_split_across_polls_once(cloud):
    t = loaded(cloud)
    _, replies, _ = cloud
    # The server stored b"abc\xc3" (half of "é"), which decodes to "abc�".
    replies.extend(
        [
            (200, log("building", "abc�", 0, 4)),
            (200, log("ready", "abcédef\n", 0, 9)),
            (200, template("ready")),
        ]
    )
    chunks = []

    t.wait(on_log=chunks.append)

    assert "".join(chunks) == "abcédef\n"


def test_wait_keeps_invalid_bytes_and_later_text(cloud):
    t = loaded(cloud)
    _, replies, _ = cloud
    replies.extend(
        [
            (200, log("building", "ab�\n", 0, 4)),
            (200, log("building", "ab�\ncd\n", 0, 7)),
            (200, log("ready", "ab�\ncd\nef\n", 0, 10)),
            (200, template("ready")),
        ]
    )
    chunks = []

    t.wait(on_log=chunks.append)

    assert "".join(chunks) == "ab�\ncd\nef\n"


def test_wait_holding_a_character_does_not_refetch_the_whole_log(cloud):
    t = loaded(cloud)
    requests, replies, _ = cloud
    replies.extend(
        [
            (200, log("building", "abc�", 0, 4)),
            (200, log("building", "", 4, 4, unchanged=True)),
            (200, log("ready", "", 4, 4, unchanged=True)),
            (200, log("ready", "abcé", 0, 5)),
            (200, template("ready")),
        ]
    )
    chunks = []

    t.wait(on_log=chunks.append)

    assert "".join(chunks) == "abcé"
    assert [r.url.params.get("known_size") for r in requests[:4]] == [None, "4", "4", None]


def test_wait_flushes_a_trailing_replacement_character_when_the_build_ends(cloud):
    t = loaded(cloud)
    _, replies, _ = cloud
    replies.extend([(200, log("failed", "boom�", 0, 5)), (200, template("failed"))])
    chunks = []

    with pytest.raises(TemplateBuildError):
        t.wait(on_log=chunks.append)
    assert "".join(chunks) == "boom�"


def test_wait_marks_log_text_the_window_skipped(cloud):
    t = loaded(cloud)
    _, replies, _ = cloud
    replies.extend(
        [
            (200, log("building", "abc", 0, 3)),
            (200, log("ready", "xyz", 500, 503, truncated=True)),
            (200, template("ready")),
        ]
    )
    chunks = []

    t.wait(on_log=chunks.append)

    assert chunks[0] == "abc"
    assert "497 bytes" in chunks[1]
    assert chunks[2] == "xyz"


def test_wait_skips_only_what_it_delivered_when_the_window_slides(cloud):
    t = loaded(cloud)
    _, replies, _ = cloud
    replies.extend(
        [
            (200, log("building", "aé", 0, 3)),
            (200, log("ready", "ébc", 1, 5, truncated=True)),
            (200, template("ready")),
        ]
    )
    chunks = []

    t.wait(on_log=chunks.append)

    assert "".join(chunks) == "aébc"


def test_wait_starts_over_when_a_new_build_resets_the_log(cloud):
    t = loaded(cloud)
    _, replies, _ = cloud
    replies.extend(
        [
            (200, log("building", "old build output\n", 0, 17)),
            (200, log("building", "new\n", 0, 4)),
            (200, log("ready", "new\nbuild\n", 0, 10)),
            (200, template("ready")),
        ]
    )
    chunks = []

    t.wait(on_log=chunks.append)

    assert "".join(chunks) == "old build output\nnew\nbuild\n"


def test_wait_keeps_going_through_a_log_503_a_429_and_a_network_error(cloud):
    t = loaded(cloud)
    _, replies, sleeps = cloud
    replies.extend(
        [
            (503, detail("build_log_unavailable", "try again")),
            (429, {"detail": "Too Many Requests"}),
            httpx.ConnectError("connection reset"),
            (200, log("ready", "done\n", 0, 5)),
            (200, template("ready")),
        ]
    )
    chunks = []

    assert t.wait(on_log=chunks.append) is t
    assert chunks == ["done\n"]
    # Exponential backoff from the poll interval.
    assert sleeps == [3, 6, 12]


def test_wait_does_not_retry_a_conflict(cloud):
    t = loaded(cloud)
    _, replies, _ = cloud
    replies.append((409, detail("template_build_in_progress", "busy")))

    with pytest.raises(CloudAPIError) as excinfo:
        t.wait()
    assert excinfo.value.status_code == 409


def test_wait_does_not_retry_or_repeat_when_on_log_raises(cloud):
    t = loaded(cloud)
    requests, replies, _ = cloud
    replies.append((200, log("building", "step 1\n", 0, 7)))
    calls = []

    def on_log(text):
        calls.append(text)
        raise CelestoError("my sink is down")

    with pytest.raises(CelestoError, match="my sink"):
        t.wait(on_log=on_log)
    assert calls == ["step 1\n"]
    assert len(requests) == 1


def test_wait_times_out_while_still_building(cloud):
    t = loaded(cloud)
    _, replies, _ = cloud
    replies.append((200, template("building")))

    with pytest.raises(TimeoutError, match="still building"):
        t.wait(timeout=0)


def test_wait_times_out_naming_the_last_error_while_retrying(cloud):
    t = loaded(cloud)
    _, replies, _ = cloud
    replies.append((503, {"detail": "unavailable"}))

    with pytest.raises(TimeoutError) as excinfo:
        t.wait(timeout=0)
    assert isinstance(excinfo.value.__cause__, CloudAPIError)


def test_wait_never_sleeps_past_the_deadline(cloud):
    t = loaded(cloud)
    _, replies, sleeps = cloud
    replies.extend([(200, template("building")), (200, template("building"))])

    with pytest.raises(TimeoutError):
        t.wait(timeout=2, poll_interval=60)
    assert sleeps and all(s <= 2 for s in sleeps)


@pytest.mark.parametrize(
    "kwargs",
    [{"poll_interval": 0}, {"poll_interval": float("nan")}, {"timeout": float("nan")}],
)
def test_wait_rejects_bad_timing_before_calling_the_api(cloud, kwargs):
    t = loaded(cloud)
    requests, _, _ = cloud

    with pytest.raises(ValidationError):
        t.wait(**kwargs)
    assert requests == []


def test_failed_build_names_the_line_exit_code_and_hint(cloud):
    t = loaded(cloud)
    _, replies, _ = cloud
    failure = {
        "line": "pip install nope",
        "line_number": 2,
        "exit_code": 1,
        "hint": "check the package name",
    }
    replies.append((200, template("failed", failure=failure)))

    with pytest.raises(TemplateBuildError) as excinfo:
        t.wait()

    message = str(excinfo.value)
    assert "line 2" in message and "pip install nope" in message and "exit code 1" in message
    assert "check the package name" in message
    assert excinfo.value.failure.line_number == 2
    assert excinfo.value.template_id == "tpl_abc123"


@pytest.mark.parametrize(
    "extra,expected",
    [
        ({"error": "builder crashed"}, "builder crashed"),
        ({"failure": {"hint": "retry later"}}, "Hint: retry later"),
        ({}, "build failed"),
    ],
    ids=["error-only", "hint-only", "bare"],
)
def test_failed_build_message_shapes(cloud, extra, expected):
    t = loaded(cloud)
    _, replies, _ = cloud
    replies.append((200, template("failed", **extra)))

    with pytest.raises(TemplateBuildError, match=expected):
        t.wait()


def test_needs_rebuild_says_to_rebuild(cloud):
    t = loaded(cloud)
    _, replies, _ = cloud
    replies.append((200, template("needs_rebuild")))

    with pytest.raises(TemplateBuildError, match="rebuild"):
        t.wait()


# --- admin routes -------------------------------------------------------------


def test_edit_rebuild_and_delete(cloud):
    t = loaded(cloud, "ready")
    requests, replies, _ = cloud
    replies.extend(
        [
            (200, template("ready", build_script="pip install polars")),
            (202, template("queued")),
            (204, None),
        ]
    )

    t.edit(build_script="pip install polars")
    t.rebuild()
    t.delete()

    assert [(r.method, r.url.path) for r in requests] == [
        ("PATCH", "/v1/templates/tpl_abc123"),
        ("POST", "/v1/templates/tpl_abc123/rebuild"),
        ("DELETE", "/v1/templates/tpl_abc123"),
    ]
    assert json.loads(requests[0].content) == {"build_script": "pip install polars"}
    assert t.status == "queued"


def test_rebuild_while_building_says_to_wait(cloud):
    t = loaded(cloud, "building")
    _, replies, _ = cloud
    replies.append((409, detail("template_build_in_progress", "busy")))

    with pytest.raises(CloudAPIError, match="wait") as excinfo:
        t.rebuild()
    assert excinfo.value.status_code == 409


def test_edit_needs_a_change_and_a_whole_size(cloud):
    t = loaded(cloud)
    requests, _, _ = cloud

    with pytest.raises(ValidationError):
        t.edit()
    with pytest.raises(ValidationError, match="together"):
        t.edit(vcpus=2)
    assert requests == []


# --- computers from a template ------------------------------------------------


def test_create_computer_uses_the_template_and_its_connection(cloud):
    t = loaded(cloud, "ready")
    requests, replies, _ = cloud

    computer = t.create_computer(vcpus=4)

    assert isinstance(computer, CloudComputer)
    assert computer.id is None and requests == []
    replies.append(
        (
            201,
            {
                "id": "cloud-test",
                "name": "trial",
                "status": "running",
                "vcpus": 4,
                "ram_mb": 4096,
                "disk_size_mb": 30720,
                "image": "ubuntu-desktop-24.04",
                "compute_location": {
                    "provider": "aws",
                    "region": "us-east-1",
                    "country_code": "US",
                },
                "created_at": "2026-10-21T00:00:00Z",
            },
        )
    )
    computer.start()
    body = json.loads(requests[0].content)
    assert body["template_id"] == "tpl_abc123"
    assert body["vcpus"] == 4


def test_create_computer_before_the_first_build_says_to_wait(cloud):
    t = loaded(cloud, "building")

    with pytest.raises(CelestoError, match="wait"):
        t.create_computer()


def test_create_computer_while_rebuilding_uses_the_previous_build(cloud):
    t = loaded(cloud, "building", rootfs_size_mb=900)

    assert isinstance(t.create_computer(), CloudComputer)


def test_create_computer_on_needs_rebuild_says_to_rebuild(cloud):
    t = loaded(cloud, "needs_rebuild", rootfs_size_mb=900)

    with pytest.raises(TemplateBuildError, match="rebuild"):
        t.create_computer()


def test_create_computer_refuses_another_template_id(cloud):
    t = loaded(cloud, "ready")

    with pytest.raises(ValidationError, match="template_id"):
        t.create_computer(template_id="coding-agent")

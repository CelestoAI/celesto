# Copyright 2026 Celesto AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Custom templates: Celesto Cloud computers that start with your packages installed.

A custom template is a built-in base template plus a shell build script.
Celesto runs the script once, saves the result, and every computer created
from the template's ``tpl_...`` ID starts from it.
"""

from __future__ import annotations

import builtins
import contextlib
import json
import math
import time
from collections.abc import Callable
from datetime import datetime
from types import ModuleType
from typing import Any, NoReturn, Self

import httpx
from typing_extensions import Unpack

from _celesto_cloud_api.api.templates import (
    create_template_v1_templates_post as create_endpoint,
)
from _celesto_cloud_api.api.templates import (
    delete_template_v1_templates_template_id_delete as delete_endpoint,
)
from _celesto_cloud_api.api.templates import (
    get_template_logs_v1_templates_template_id_logs_get as logs_endpoint,
)
from _celesto_cloud_api.api.templates import (
    get_template_v1_templates_template_id_get as get_endpoint,
)
from _celesto_cloud_api.api.templates import (
    lint_template_v1_templates_lint_post as lint_endpoint,
)
from _celesto_cloud_api.api.templates import (
    list_templates_v1_templates_get as list_endpoint,
)
from _celesto_cloud_api.api.templates import (
    rebuild_template_v1_templates_template_id_rebuild_post as rebuild_endpoint,
)
from _celesto_cloud_api.api.templates import (
    update_template_v1_templates_template_id_patch as update_endpoint,
)
from _celesto_cloud_api.errors import UnexpectedStatus
from _celesto_cloud_api.models.custom_template_create import CustomTemplateCreate
from _celesto_cloud_api.models.custom_template_lint_request import CustomTemplateLintRequest
from _celesto_cloud_api.models.custom_template_lint_response import (
    CustomTemplateLintResponse,
)
from _celesto_cloud_api.models.custom_template_list_response import (
    CustomTemplateListResponse,
)
from _celesto_cloud_api.models.custom_template_logs_response import (
    CustomTemplateLogsResponse,
)
from _celesto_cloud_api.models.custom_template_response import CustomTemplateResponse
from _celesto_cloud_api.models.custom_template_update import CustomTemplateUpdate
from _celesto_cloud_api.models.lint_warning import LintWarning
from _celesto_cloud_api.models.template_build_failure import (
    TemplateBuildFailure as GeneratedFailure,
)
from _celesto_cloud_api.types import UNSET, Unset
from celesto._cloud import _CloudComputer
from celesto._providers.options import CloudOptions
from celesto.exceptions import (
    CelestoError,
    CloudAPIError,
    TemplateBuildError,
    ValidationError,
)
from celesto.sdk import CloudComputer
from celesto.types import TemplateBuildFailure, TemplateLintWarning

# Statuses that mean a build is still on its way to ready or failed.
_BUILDING_STATUSES = frozenset({"queued", "building"})
# Builds are capped at 30 minutes; the rest covers time spent queued.
_DEFAULT_WAIT_TIMEOUT = 40 * 60
# wait() polls the /templates routes, which allow 60 requests a minute.
_MIN_POLL_INTERVAL = 1.0
# Longest pause between retries of a failed poll, and the exponent cap that
# keeps the backoff arithmetic finite.
_MAX_RETRY_BACKOFF = 30.0
_MAX_BACKOFF_EXPONENT = 16
# API messages copied into errors are capped like other cloud error details.
_MAX_MESSAGE_LENGTH = 500
# Where a 422 field error came from; the field path after it is what users wrote.
_REQUEST_PARTS = {"body", "query", "path", "header", "cookie"}
# The template name rule the API enforces with a pattern, in plain words.
_NAME_RULE = (
    "use only letters, digits, spaces, dots, underscores and dashes, "
    "without a space at the start or end"
)

# The connection options a template keeps and hands to computers created from it.
_CONNECTION_OPTIONS = ("api_key", "base_url", "organization_id")


class _CloudNetworkError(CelestoError):
    """A template request that never got an answer; wait() retries these."""


class _LogCallbackError(Exception):
    """Carries an exception raised by the caller's ``on_log`` out of a poll.

    wait() retries failed API calls; wrapping keeps it from mistaking a
    callback's own error for one of those.
    """

    def __init__(self, error: Exception) -> None:
        super().__init__(str(error))
        self.error = error


class _Connection:
    """One authenticated cloud client and the calls templates make with it.

    It reuses the cloud computer transport for API-key lookup, base URL checks
    and the organization header, so templates and computers resolve
    credentials the same way.
    """

    def __init__(self, options: dict[str, Any]) -> None:
        self.options = options
        self._transport = _CloudComputer(**options)

    def close(self) -> None:
        self._transport.close()

    def call(
        self,
        endpoint: ModuleType,
        expected: type | None,
        *,
        collection: bool = False,
        template_id: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Call a generated endpoint module and turn failures into Celesto errors.

        The request is built and the success body parsed by the generated
        code, but errors are read from the raw response first: the API's 422
        body (``detail`` plus ``errors``) does not fit the generated
        validation-error model, which would otherwise fail to parse it.

        ``collection`` marks routes (create, list, lint) whose 404 means
        custom templates are not enabled; ``template_id`` is the
        single-template route's path parameter, also named in its 404.
        """
        if template_id is not None:
            kwargs["template_id"] = template_id
        client = self._transport._client
        request = endpoint._get_kwargs(
            x_current_organization=self._transport._organization, **kwargs
        )
        try:
            response = client.get_httpx_client().request(**request)
        except httpx.TransportError as exc:
            raise _CloudNetworkError(
                f"Cloud request failed ({type(exc).__name__}); its outcome may be unknown. "
                "Check your templates with Template.list() before retrying."
            ) from None
        if response.status_code >= 400:
            raise _api_error(response.status_code, response.content, collection, template_id)
        try:
            parsed = endpoint._build_response(client=client, response=response).parsed
        except (ValueError, KeyError, TypeError, UnexpectedStatus):
            raise _invalid_response() from None
        if expected is not None and not isinstance(parsed, expected):
            raise _invalid_response()
        return parsed


class Template:
    """A custom template in Celesto Cloud.

    Create one with :meth:`create`, load one with :meth:`get`, and list your
    organization's templates with :meth:`list`. Creating a template queues its
    build; :meth:`wait` blocks until it is ready, and :meth:`create_computer`
    returns a computer that starts from it.

    Example:
        >>> template = Template.create(
        ...     name="data-env",
        ...     build_script="apt-get install -y ffmpeg\\npip install pandas",
        ... )
        >>> template.wait(on_log=print)
        >>> with template.create_computer() as computer:
        ...     computer.run("ffmpeg -version")
    """

    _data: CustomTemplateResponse
    _connection: _Connection

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "Use Template.create(...) to create a template, or Template.get(id) to load one."
        )

    @classmethod
    def _wrap(cls, data: CustomTemplateResponse, connection: _Connection) -> Template:
        instance = cls.__new__(cls)
        instance._data = data
        instance._connection = connection
        return instance

    # --- loading and creating ---------------------------------------------

    @classmethod
    def create(
        cls,
        *,
        name: str,
        build_script: str,
        base_template_id: str | None = None,
        vcpus: int | None = None,
        ram_mb: int | None = None,
        disk_size_mb: int | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        organization_id: str | None = None,
    ) -> Template:
        """Create a custom template and queue its first build.

        Args:
            name: A label your team sees: letters, digits, spaces, dots,
                underscores and dashes. Unique within the organization.
            build_script: Shell commands Celesto runs once, as root, to build
                the template. At most 64 KB.
            base_template_id: The built-in template to start from. The API
                uses ``coding-agent`` when omitted.
            vcpus, ram_mb, disk_size_mb: The size of computers created from
                this template, unless a computer asks for another. Pass all
                three or none; they must match a sandbox size. The base
                template's size is used when omitted. The finished image must
                fit in ``disk_size_mb``.
            api_key, base_url, organization_id: Connection options, as for
                ``CloudComputer``. Computers created from this template reuse
                them.

        Raises:
            CloudAPIError: The API refused the template, for example because
                custom templates are not enabled for the account (404), the
                name is taken (409) or the organization already has 2 builds
                running (429).
        """
        size = _size_fields(vcpus, ram_mb, disk_size_mb)
        body = CustomTemplateCreate(
            name=name,
            build_script=build_script,
            base_template_id=base_template_id if base_template_id is not None else UNSET,
            **size,
        )
        connection = _Connection(_connection_options(api_key, base_url, organization_id))
        try:
            data = connection.call(
                create_endpoint, CustomTemplateResponse, collection=True, body=body
            )
        except BaseException:
            connection.close()
            raise
        return cls._wrap(data, connection)

    @classmethod
    def get(
        cls,
        template_id: str,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        organization_id: str | None = None,
    ) -> Template:
        """Load an existing template by its ``tpl_...`` ID."""
        connection = _Connection(_connection_options(api_key, base_url, organization_id))
        try:
            data = connection.call(
                get_endpoint,
                CustomTemplateResponse,
                template_id=template_id,
            )
        except BaseException:
            connection.close()
            raise
        return cls._wrap(data, connection)

    @classmethod
    def list(
        cls,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        organization_id: str | None = None,
    ) -> builtins.list[Template]:
        """List your organization's custom templates, newest first."""
        options = _connection_options(api_key, base_url, organization_id)
        connection = _Connection(options)
        try:
            listing = connection.call(list_endpoint, CustomTemplateListResponse, collection=True)
        finally:
            connection.close()
        # Each template gets its own connection, so closing one leaves the
        # others usable. A connection opens nothing until its first request.
        return [cls._wrap(item, _Connection(dict(options))) for item in listing.templates]

    @classmethod
    def lint(
        cls,
        build_script: str,
        *,
        base_template_id: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        organization_id: str | None = None,
    ) -> builtins.list[TemplateLintWarning]:
        """Check a build script without creating or building anything."""
        body = CustomTemplateLintRequest(
            build_script=build_script,
            base_template_id=base_template_id if base_template_id is not None else UNSET,
        )
        connection = _Connection(_connection_options(api_key, base_url, organization_id))
        try:
            result = connection.call(
                lint_endpoint,
                CustomTemplateLintResponse,
                collection=True,
                body=body,
            )
        finally:
            connection.close()
        return [_lint_warning(warning) for warning in result.warnings]

    # --- fields -----------------------------------------------------------

    @property
    def id(self) -> str:
        return self._data.id

    @property
    def name(self) -> str:
        return self._data.name

    @property
    def status(self) -> str:
        """``queued``, ``building``, ``ready``, ``failed`` or ``needs_rebuild``."""
        return self._data.status.value

    @property
    def base_template_id(self) -> str:
        return self._data.base_template_id

    @property
    def build_script(self) -> str:
        return self._data.build_script

    @property
    def vcpus(self) -> int:
        """vCPUs of computers created from this template, unless they ask for another size."""
        return self._data.default_vcpus

    @property
    def ram_mb(self) -> int:
        return self._data.default_ram_mb

    @property
    def disk_size_mb(self) -> int:
        return self._data.default_disk_size_mb

    @property
    def warnings(self) -> builtins.list[TemplateLintWarning]:
        """Lint warnings from the last create or edit; empty otherwise."""
        warnings = self._data.warnings
        return [] if isinstance(warnings, Unset) else [_lint_warning(w) for w in warnings]

    @property
    def failure(self) -> TemplateBuildFailure | None:
        """Where the last build failed, when its script exited with an error."""
        return _failure(self._data.failure)

    @property
    def error(self) -> str | None:
        """Why the last build failed, when the failure came from outside the script."""
        error = self._data.error
        return None if isinstance(error, Unset) else error

    @property
    def created_at(self) -> datetime:
        return self._data.created_at

    @property
    def updated_at(self) -> datetime:
        return self._data.updated_at

    def __repr__(self) -> str:
        return f"Template(id={self.id!r}, name={self.name!r}, status={self.status!r})"

    # --- builds -----------------------------------------------------------

    def refresh(self) -> Self:
        """Reload this template, including its build status."""
        self._data = self._connection.call(
            get_endpoint,
            CustomTemplateResponse,
            template_id=self.id,
        )
        return self

    def logs(self, *, known_size: int | None = None) -> str:
        """Return the end of the latest build's log (at most the last 256 KB)."""
        return self._read_log(known_size).log or ""

    def _read_log(self, known_size: int | None) -> _LogPage:
        result = self._connection.call(
            logs_endpoint,
            CustomTemplateLogsResponse,
            template_id=self.id,
            known_size=known_size if known_size is not None else UNSET,
        )
        return _LogPage(result)

    def wait(
        self,
        *,
        timeout: float = _DEFAULT_WAIT_TIMEOUT,
        poll_interval: float = 3,
        on_log: Callable[[str], None] | None = None,
    ) -> Self:
        """Block until the build is ready.

        Polls once every ``poll_interval`` seconds: the template's status, or,
        with ``on_log``, the build log, which carries the status too. A failed
        poll (rate limit, server error or network error) is retried with
        backoff until ``timeout``, since the build keeps running.

        Args:
            timeout: Seconds to wait in total. The default covers the
                30-minute build limit plus time spent queued.
            poll_interval: Seconds between polls; at least 1.
            on_log: Called with each new piece of build log text.

        Raises:
            TemplateBuildError: The build failed or the template needs a
                rebuild. ``failure`` names the failing script line when known.
            TimeoutError: The build was still running after ``timeout``, or
                polls kept failing until then (the last error is the cause).
            ValidationError: ``poll_interval`` is under 1 second, or either
                argument is NaN.
        """
        if math.isnan(timeout):
            raise ValidationError("timeout must be a number of seconds.")
        if math.isnan(poll_interval) or poll_interval < _MIN_POLL_INTERVAL:
            raise ValidationError(f"poll_interval must be at least {_MIN_POLL_INTERVAL:g} second.")
        deadline = time.monotonic() + timeout
        follower = _LogFollower(on_log) if on_log is not None else None
        failed_polls = 0
        while True:
            try:
                status = self._poll(follower)
            except _LogCallbackError as error:
                # The caller's on_log failed, not the API: never retry it.
                raise error.error from None
            except Exception as error:
                if not _is_transient(error):
                    raise
                failed_polls += 1
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(
                        f"Template {self.id} could not be checked before the "
                        f"{timeout:g}s timeout: {error}"
                    ) from error
                time.sleep(min(_retry_delay(poll_interval, failed_polls), remaining))
                continue
            failed_polls = 0
            if status == "ready":
                return self
            if status not in _BUILDING_STATUSES:
                _raise_build_error(self._data)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"Template {self.id} was still {status} after {timeout:g}s.")
            time.sleep(min(poll_interval, remaining))

    def _poll(self, follower: _LogFollower | None) -> str:
        """Check the build once and return its status.

        With a log follower this is one request (the log answer carries the
        status); the template is read again only once the build ends, to pick
        up the failure details and final fields.
        """
        if follower is None:
            return self.refresh().status
        page = self._read_log(follower.known_size)
        finished = page.status not in _BUILDING_STATUSES
        if finished and page.unchanged and follower.holding:
            # The log stopped growing with a character held back: read it
            # once more in full so the last character is delivered.
            page = self._read_log(None)
        follower.feed(page, finished=finished)
        if not finished:
            return page.status
        return self.refresh().status

    # --- changes ----------------------------------------------------------

    def edit(
        self,
        *,
        name: str | None = None,
        build_script: str | None = None,
        vcpus: int | None = None,
        ram_mb: int | None = None,
        disk_size_mb: int | None = None,
    ) -> Self:
        """Change the name, build script or computer size. Organization admins only.

        A new build script takes effect on the next :meth:`rebuild`.
        """
        size = _size_fields(vcpus, ram_mb, disk_size_mb)
        if name is None and build_script is None and not size:
            raise ValidationError("Pass name, build_script or a size to edit the template.")
        body = CustomTemplateUpdate(
            name=name if name is not None else UNSET,
            build_script=build_script if build_script is not None else UNSET,
            **size,
        )
        self._data = self._connection.call(
            update_endpoint,
            CustomTemplateResponse,
            template_id=self.id,
            body=body,
        )
        return self

    def rebuild(self) -> Self:
        """Build again with the current script and the latest base. Organization admins only.

        Follow it with :meth:`wait`. Computers created while the template
        rebuilds start from its previous build.
        """
        self._data = self._connection.call(
            rebuild_endpoint,
            CustomTemplateResponse,
            template_id=self.id,
        )
        return self

    def delete(self) -> None:
        """Delete this template. Organization admins only.

        Computers already created from it keep running.
        """
        self._connection.call(delete_endpoint, None, template_id=self.id)

    # --- computers --------------------------------------------------------

    def create_computer(self, **options: Unpack[CloudOptions]) -> CloudComputer:
        """Return a cloud computer that starts from this template.

        Like ``CloudComputer(...)``, the computer is created on first use or
        when entering a ``with`` block. It reuses this template's connection
        options unless you pass your own. Other options, such as ``vcpus``,
        override the template's size for this computer.

        Raises:
            CelestoError: The template has no ready build yet.
            TemplateBuildError: The template needs a rebuild first.
        """
        if "template_id" in options:
            raise ValidationError(
                "create_computer() uses this template's ID; remove the template_id option."
            )
        self._check_usable_build()
        for key, value in self._connection.options.items():
            options.setdefault(key, value)  # type: ignore[misc]
        options["template_id"] = self.id
        return CloudComputer(**options)

    def _check_usable_build(self) -> None:
        """Fail early, with the next step, when no computer can boot this template.

        The API refuses these with 409. ``rootfs_size_mb`` is written only
        when a build succeeds and is kept through rebuilds, so it says whether
        a usable build exists.
        """
        if self.status == "needs_rebuild":
            _raise_build_error(self._data)
        has_build = not isinstance(self._data.rootfs_size_mb, Unset) and (
            self._data.rootfs_size_mb is not None
        )
        if self.status == "ready" or has_build:
            return
        next_step = (
            "call wait() first"
            if self.status in _BUILDING_STATUSES
            else "fix the build script, then call rebuild() and wait()"
        )
        raise CelestoError(
            f"Template {self.id} has no ready build yet ({self.status}); {next_step}."
        )

    # --- lifetime ---------------------------------------------------------

    def close(self) -> None:
        """Close this template's HTTP connection. Computers it created are unaffected."""
        self._connection.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


class _LogPage:
    """One /logs answer with the generated client's ``Unset`` fields filled in."""

    def __init__(self, result: CustomTemplateLogsResponse) -> None:
        self.status = result.status.value
        self.log = "" if isinstance(result.log, Unset) else result.log
        self.offset = 0 if isinstance(result.offset, Unset) else result.offset
        self.size = 0 if isinstance(result.size, Unset) else result.size
        self.unchanged = False if isinstance(result.unchanged, Unset) else result.unchanged


class _LogFollower:
    """Hands ``on_log`` each piece of a build log once, across polls.

    The API returns at most the last 256 KB of the log: ``log`` is the stored
    bytes from ``offset`` to ``size``, decoded with invalid bytes replaced by
    U+FFFD, and starting on a character boundary. Decoded text and byte counts
    don't line up once a replacement happens, so while the window stays put
    (``offset`` unchanged, the usual case) the follower counts delivered
    characters, which stay stable from one poll to the next. Only when the
    window slides does it convert bytes to characters, and that is exact
    unless the log has invalid bytes there.

    A poll can end in the middle of a multi-byte character, which then decodes
    as a trailing U+FFFD. That last character is held back until the next poll
    shows it whole, or the build ends.
    """

    def __init__(self, on_log: Callable[[str], None]) -> None:
        self._on_log = on_log
        # The ``offset`` of the last window read, and how many of its
        # characters were delivered.
        self._window_offset: int | None = None
        self._chars = 0
        # The log byte position delivered up to, and the last ``size`` seen.
        self._end = 0
        self._size = 0
        # Sent back as ``known_size`` so an unchanged log is not re-sent.
        self.known_size: int | None = None
        # True while a trailing character is held back for the next poll.
        self.holding = False

    def feed(self, page: _LogPage, *, finished: bool) -> None:
        if page.unchanged:
            return
        text, offset, size = page.log, page.offset, page.size
        if size < self._size:
            # The log got shorter: a new build started a new log.
            self._window_offset, self._chars, self._end = None, 0, 0
        chunks = []
        if offset == self._window_offset:
            start = self._chars
        elif offset > self._end:
            # More was written between polls than the window holds.
            chunks.append(f"[... {offset - self._end} bytes of build log not shown ...]\n")
            start = 0
        else:
            start = _char_index(text, self._end - offset)
        new = text[start:]
        self.holding = not finished and new.endswith("�")
        if self.holding:
            new = new[:-1]
        if new:
            chunks.append(new)
        # Record what is delivered before calling on_log, so a callback that
        # raises can never cause the same text to be delivered twice.
        self._window_offset = offset
        self._chars = len(text) - self.holding
        self._size = size
        self.known_size = size
        if self.holding:
            self._end = min(offset + len(text[: self._chars].encode("utf-8")), size)
        else:
            self._end = size
        for chunk in chunks:
            try:
                self._on_log(chunk)
            except Exception as error:
                raise _LogCallbackError(error) from error


def _char_index(text: str, byte_count: int) -> int:
    """The index of the first character of ``text`` after its first ``byte_count`` UTF-8 bytes."""
    consumed = 0
    for index, char in enumerate(text):
        if consumed >= byte_count:
            return index
        consumed += len(char.encode("utf-8"))
    return len(text)


def _is_transient(error: Exception) -> bool:
    """Whether a failed poll is worth retrying: the build itself is unaffected."""
    if isinstance(error, _CloudNetworkError):
        return True
    return isinstance(error, CloudAPIError) and (
        error.status_code == 429 or error.status_code >= 500
    )


def _retry_delay(poll_interval: float, failed_polls: int) -> float:
    """Exponential backoff from ``poll_interval``, capped at ``_MAX_RETRY_BACKOFF``.

    The generated client does not expose Retry-After on errors, so the
    backoff alone spaces retries out.
    """
    exponent = min(failed_polls - 1, _MAX_BACKOFF_EXPONENT)
    return float(min(poll_interval * 2**exponent, _MAX_RETRY_BACKOFF))


def _connection_options(
    api_key: str | None, base_url: str | None, organization_id: str | None
) -> dict[str, Any]:
    """The connection options the caller passed, leaving the rest to their defaults."""
    given = {"api_key": api_key, "base_url": base_url, "organization_id": organization_id}
    return {key: value for key, value in given.items() if value is not None}


def _size_fields(vcpus: int | None, ram_mb: int | None, disk_size_mb: int | None) -> dict[str, int]:
    """The API's default-size fields, which it takes all together or not at all."""
    values = {
        "default_vcpus": vcpus,
        "default_ram_mb": ram_mb,
        "default_disk_size_mb": disk_size_mb,
    }
    given = {key: value for key, value in values.items() if value is not None}
    if given and len(given) != len(values):
        raise ValidationError("Pass vcpus, ram_mb and disk_size_mb together, or none of them.")
    return given


def _lint_warning(warning: LintWarning) -> TemplateLintWarning:
    return TemplateLintWarning(line=warning.line, code=warning.code.value, message=warning.message)


def _failure(failure: GeneratedFailure | None | Unset) -> TemplateBuildFailure | None:
    if not isinstance(failure, GeneratedFailure):
        return None

    def value(field: Any) -> Any:
        return None if isinstance(field, Unset) else field

    return TemplateBuildFailure(
        line=value(failure.line),
        line_number=value(failure.line_number),
        exit_code=value(failure.exit_code),
        hint=value(failure.hint),
    )


def _raise_build_error(data: CustomTemplateResponse) -> NoReturn:
    """Raise the error for a finished build that did not end ready."""
    status = data.status.value
    failure = _failure(data.failure)
    if status == "needs_rebuild":
        message = (
            f"Template {data.id} needs a rebuild because its base template changed; "
            "call rebuild(), then wait()."
        )
    else:
        message = f"Template {data.id} build {status}"
        if failure and failure.line:
            message += f" at line {failure.line_number}: {failure.line!r}"
            if failure.exit_code is not None:
                message += f" (exit code {failure.exit_code})"
        elif not isinstance(data.error, Unset) and data.error:
            message += f": {data.error}"
        message += "."
        if failure and failure.hint:
            message += f" Hint: {failure.hint}"
        message += " Fix the script with edit(), then call rebuild()."
    raise TemplateBuildError(message, template_id=data.id, status=status, failure=failure)


def _invalid_response() -> CelestoError:
    return CelestoError(
        "Cloud returned an invalid response; check the API version before retrying."
    )


def _api_error(
    status_code: int, content: bytes, collection: bool, template_id: str | None
) -> CloudAPIError:
    """A CloudAPIError whose recovery says what to do for this template failure."""
    body: Any = None
    with contextlib.suppress(ValueError, RecursionError):
        body = json.loads(content)
    detail = body.get("detail") if isinstance(body, dict) else None
    code = detail.get("error_code") if isinstance(detail, dict) else None
    message = detail.get("message") if isinstance(detail, dict) else detail
    message = message[:_MAX_MESSAGE_LENGTH] if isinstance(message, str) else None
    field_errors = body.get("errors") if isinstance(body, dict) else None
    if not isinstance(field_errors, list):
        field_errors = detail if isinstance(detail, list) else None

    recovery: str | None = None
    if status_code == 404 and collection:
        recovery = (
            "Custom templates are not enabled for this account; "
            "contact support@celesto.ai to turn them on."
        )
    elif status_code == 404:
        recovery = f"Template '{template_id}' was not found; run Template.list() to see yours."
    elif status_code == 409 and code == "template_build_in_progress":
        recovery = "A build is already queued or running; call wait(), then rebuild()."
    elif status_code == 409 and message:
        recovery = (
            f"{message}; choose another name." if code == "template_name_taken" else f"{message}."
        )
    elif status_code == 429 and code == "template_build_limit":
        recovery = (
            "Your organization already has 2 template builds queued or running; "
            "wait for one to finish."
        )
    elif status_code == 422 and field_errors:
        described = _describe_field_errors(field_errors)
        if described:
            recovery = f"Fix these fields: {described}"
    elif status_code in (400, 422) and message:
        recovery = f"{message}."
    return CloudAPIError(
        status_code,
        detail=message if status_code == 400 else None,
        recovery=recovery,
    )


def _describe_field_errors(errors: list[Any]) -> str:
    """Turn 422 field errors into ``field: message; ...`` text."""
    parts = []
    for error in errors:
        if not isinstance(error, dict) or not error.get("msg"):
            continue
        text = str(error["msg"]).removeprefix("Value error, ")
        location = [str(part) for part in error.get("loc") or []]
        if location and location[0] in _REQUEST_PARTS:
            location = location[1:]
        if location == ["name"] and error.get("type") == "string_pattern_mismatch":
            # The API states the rule as a regular expression; say it in words.
            text = _NAME_RULE
        parts.append(f"{'.'.join(location)}: {text}" if location else text)
    return "; ".join(parts)[:_MAX_MESSAGE_LENGTH]

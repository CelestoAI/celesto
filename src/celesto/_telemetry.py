"""Small, optional usage counters for local Celesto operations."""

from __future__ import annotations

import atexit
import importlib.metadata
import json
import os
import platform
import sys
import tempfile
from collections.abc import Callable
from contextlib import contextmanager, suppress
from contextvars import ContextVar, Token
from datetime import UTC, datetime
from functools import wraps
from pathlib import Path
from threading import Lock, Thread, current_thread
from typing import Any, Literal, TypeVar
from uuid import uuid4

import httpx

Surface = Literal["cli", "python_sdk"]
Feature = Literal[
    "setup", "computer", "command_execution", "browser", "desktop", "image", "snapshot"
]
Marker = tuple[Literal["active", "features"], str, str]

# Set only after PostHog configuration and privacy review are complete. This is a
# public capture key, never a personal API key. An empty key disables collection.
HONEYS_FAV_FOOD = "phc_vjIHlkZ5iOYWdZx0LXiifLKGl53QehS8LjudWiuSRND"
_CAPTURE_URL = "https://us.i.posthog.com/capture/"
_STATE_PATH = Path.home() / ".celesto" / "telemetry.json"
_NOTICE = (
    "Celesto may send limited local usage counts (installation ID, feature category, "
    "version, OS family). PostHog may retain your IP address. "
    "No commands, files, or URLs are sent. "
    "See https://celesto.ai/legal/privacy-policy. "
    "Opt out: celesto config telemetry off or CELESTO_NO_TELEMETRY=1."
)
_cli_active: ContextVar[bool] = ContextVar("celesto_telemetry_cli_active", default=False)
_sdk_depth: ContextVar[bool] = ContextVar("celesto_telemetry_sdk_depth", default=False)
_notice_this_process = False
_pending: set[Thread] = set()
_pending_lock = Lock()
F = TypeVar("F", bound=Callable[..., Any])


def _truthy(value: str | None) -> bool:
    return value is not None and value.strip().lower() not in {"", "0", "false", "no", "off"}


def _environment_override() -> str | None:
    if _truthy(os.environ.get("CELESTO_NO_TELEMETRY")):
        return "CELESTO_NO_TELEMETRY"
    if _truthy(os.environ.get("DO_NOT_TRACK")):
        return "DO_NOT_TRACK"
    if _truthy(os.environ.get("CI")) or _truthy(os.environ.get("PYTEST_CURRENT_TEST")):
        return "test or CI environment"
    return None


def _read_state() -> dict[str, Any]:
    if not _STATE_PATH.exists():
        return {}
    if _STATE_PATH.is_symlink():
        raise ValueError("Telemetry state must not be a symbolic link")
    value = json.loads(_STATE_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Telemetry state must be an object")
    return value


@contextmanager
def _state_lock() -> Any:
    directory = _STATE_PATH.parent
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock_path = directory / "telemetry.lock"
    if lock_path.is_symlink():
        raise ValueError("Telemetry lock must not be a symbolic link")
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    locked = False
    try:
        os.chmod(lock_path, 0o600)
        if os.name == "nt":
            import msvcrt

            os.write(fd, b"0")
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_LOCK, 1)  # type: ignore[attr-defined]
        else:
            import fcntl

            fcntl.flock(fd, fcntl.LOCK_EX)
        locked = True
        yield
    finally:
        try:
            if locked:
                if os.name == "nt":
                    import msvcrt

                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)  # type: ignore[attr-defined]
                else:
                    import fcntl

                    fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _write_state(state: dict[str, Any]) -> None:
    data = json.dumps(state, separators=(",", ":"))
    fd, tmp_name = tempfile.mkstemp(prefix="telemetry-", suffix=".tmp", dir=_STATE_PATH.parent)
    try:
        os.chmod(tmp_name, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(data)
        os.replace(tmp_name, _STATE_PATH)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def status() -> tuple[bool, str]:
    """Return the effective preference and why it has that value."""
    override = _environment_override()
    if override is not None:
        return False, override
    try:
        state = _read_state()
    except (OSError, ValueError, json.JSONDecodeError):
        return False, "unavailable state"
    if state.get("enabled") is False:
        return False, "saved preference"
    if not HONEYS_FAV_FOOD:
        return False, "collection unavailable in this build"
    return True, "default" if "enabled" not in state else "saved preference"


def set_enabled(enabled: bool) -> None:
    """Save one preference shared by the CLI and Python SDK."""
    with _state_lock():
        try:
            state = _read_state()
        except (OSError, ValueError, json.JSONDecodeError):
            state = {}
        state["enabled"] = enabled
        _write_state(state)


def cli_enter() -> Token[bool]:
    return _cli_active.set(True)


def cli_exit(token: Token[bool]) -> None:
    _cli_active.reset(token)


def begin_local_use(surface: Surface) -> bool:
    """Show first-use notice; return whether this process may emit events."""
    global _notice_this_process
    if (
        not HONEYS_FAV_FOOD
        or _notice_this_process
        or (surface == "python_sdk" and (_cli_active.get() or _sdk_depth.get()))
    ):
        return False
    if not status()[0]:
        return False
    try:
        with _state_lock():
            if _notice_this_process:
                return False
            state = _read_state()
            if state.get("enabled") is False:
                return False
            if not state.get("notice_shown"):
                state["notice_shown"] = True
                _write_state(state)
                _notice_this_process = True
                print(_NOTICE, file=sys.stderr)
                return False
    except (OSError, ValueError, json.JSONDecodeError):
        return False
    return True


def _send(event: dict[str, Any], marker: Marker) -> None:
    try:
        if not status()[0]:
            return
        with _state_lock():
            if _environment_override() is not None:
                return
            state = _read_state()
            if state.get("enabled") is False or not state.get("notice_shown"):
                return
            bucket, key, value = marker
            markers = state.get(bucket)
            if not isinstance(markers, dict) or markers.get(key) == value:
                return
            response = httpx.post(_CAPTURE_URL, json=event, timeout=0.2)
            if 200 <= response.status_code < 300:
                markers[key] = value
                _write_state(state)
    except Exception:
        pass
    finally:
        with _pending_lock:
            _pending.discard(current_thread())


def _queue(event: dict[str, Any], marker: Marker) -> None:
    thread = Thread(target=_send, args=(event, marker), daemon=True)
    with _pending_lock:
        _pending.add(thread)
    try:
        thread.start()
    except Exception:
        with _pending_lock:
            _pending.discard(thread)


def _flush() -> None:
    from time import monotonic

    deadline = monotonic() + 0.25
    with _pending_lock:
        threads = tuple(_pending)
    for thread in threads:
        with suppress(RuntimeError):
            thread.join(max(0.0, deadline - monotonic()))


atexit.register(_flush)


def record_success(surface: Surface, feature: Feature) -> None:
    """Queue at most one active and feature event per local time bucket."""
    if not HONEYS_FAV_FOOD or _notice_this_process or not status()[0]:
        return
    if surface == "python_sdk" and _cli_active.get():
        return
    now = datetime.now(UTC)
    day = now.date().isoformat()
    year, week, _ = now.isocalendar()
    week_key = f"{year}-W{week:02d}"
    try:
        with _state_lock():
            state = _read_state()
            if state.get("enabled") is False or not state.get("notice_shown"):
                return
            installation_id = state.get("installation_id")
            if not isinstance(installation_id, str) or not installation_id:
                installation_id = f"celesto-oss-{uuid4()}"
                state["installation_id"] = installation_id
            active = state.setdefault("active", {})
            features = state.setdefault("features", {})
            if not isinstance(active, dict) or not isinstance(features, dict):
                return
            send_active = active.get(surface) != day
            feature_key = f"{surface}:{feature}"
            send_feature = features.get(feature_key) != week_key
            if not send_active and not send_feature:
                return
            _write_state(state)
    except (OSError, ValueError, json.JSONDecodeError):
        return

    try:
        version = importlib.metadata.version("celesto")
    except importlib.metadata.PackageNotFoundError:
        version = "unknown"
    properties: dict[str, Any] = {
        "schema_version": 1,
        "surface": surface,
        "celesto_version": version,
        "os_family": platform.system().lower(),
        "$process_person_profile": False,
        "$geoip_disable": True,
    }
    base = {
        "api_key": HONEYS_FAV_FOOD,
        "distinct_id": installation_id,
        "timestamp": now.isoformat(),
    }
    if send_active:
        _queue(
            {**base, "event": "celesto_oss_active", "properties": properties},
            ("active", surface, day),
        )
    if send_feature:
        _queue(
            {
                **base,
                "event": "celesto_oss_feature_used",
                "properties": {**properties, "feature": feature},
            },
            ("features", feature_key, week_key),
        )


def observe_sdk_operation(feature: Feature) -> Callable[[F], F]:
    """Count a completed top-level local SDK operation once."""

    def decorate(function: F) -> F:
        @wraps(function)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            if args and getattr(args[0], "_provider_name", "local") == "cloud":
                return function(*args, **kwargs)
            if _sdk_depth.get() or _cli_active.get():
                return function(*args, **kwargs)
            eligible = begin_local_use("python_sdk")
            token = _sdk_depth.set(True)
            try:
                result = function(*args, **kwargs)
            finally:
                _sdk_depth.reset(token)
            if eligible:
                record_success("python_sdk", feature)
            return result

        return wrapped  # type: ignore[return-value]

    return decorate

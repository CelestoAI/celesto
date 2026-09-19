"""Shared parsing helpers for command event streams."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from typing import Any

from pydantic import ValidationError

from celesto.exceptions import CelestoError
from celesto.types import (
    CommandEvent,
    CommandExitEvent,
    CommandOutputEvent,
    CommandStartedEvent,
)

_MAX_EVENT_BYTES = 1024 * 1024


def _is_json_object(value: str) -> bool:
    try:
        return isinstance(json.loads(value), dict)
    except (json.JSONDecodeError, RecursionError):
        return False


def parse_command_event(data: str) -> CommandEvent:
    """Parse one JSON SSE payload without exposing untrusted response content."""
    if len(data.encode("utf-8")) > _MAX_EVENT_BYTES:
        raise CelestoError("Command stream returned an event that was too large.")
    try:
        payload: Any = json.loads(data)
        if not isinstance(payload, dict):
            raise ValueError
        event_type = payload.get("type")
        if event_type == "started":
            return CommandStartedEvent.model_validate(payload)
        if event_type in {"stdout", "stderr"}:
            return CommandOutputEvent.model_validate(payload)
        if event_type == "exit":
            return CommandExitEvent.model_validate(payload)
    except (json.JSONDecodeError, UnicodeError, ValidationError, ValueError, TypeError):
        pass
    raise CelestoError("Command stream returned an invalid event; check the API version.")


def iter_sse_data(lines: Iterable[str | bytes]) -> Iterator[str]:
    """Yield assembled ``data`` fields from an SSE line iterator."""
    data_lines: list[str] = []
    size = 0
    for raw_line in lines:
        line = (
            raw_line.decode("utf-8", errors="replace") if isinstance(raw_line, bytes) else raw_line
        )
        line = line.rstrip("\r\n")
        if not line:
            if data_lines:
                yield "\n".join(data_lines)
                data_lines = []
                size = 0
            continue
        if line.startswith(":"):
            continue
        field, separator, value = line.partition(":")
        if field != "data":
            continue
        if separator and value.startswith(" "):
            value = value[1:]
        value_size = len(value.encode("utf-8"))
        if value_size > _MAX_EVENT_BYTES:
            raise CelestoError("Command stream returned an event that was too large.")
        # Some deployed proxies preserve each JSON ``data`` line but drop the
        # blank SSE delimiter between events. Split only when both sides are
        # independently complete JSON objects, preserving valid multiline SSE.
        if data_lines and _is_json_object("\n".join(data_lines)) and _is_json_object(value):
            yield "\n".join(data_lines)
            data_lines = []
            size = 0
        size += value_size
        if size > _MAX_EVENT_BYTES:
            raise CelestoError("Command stream returned an event that was too large.")
        data_lines.append(value)
    if data_lines:
        yield "\n".join(data_lines)

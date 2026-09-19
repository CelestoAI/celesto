from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
import datetime


T = TypeVar("T", bound="SandboxCommandEventRequest")


@_attrs_define
class SandboxCommandEventRequest:
    """Command lifecycle event from a host agent or backend fallback.

    Attributes:
        computer_id (str):
        command_id (str):
        status (str):
        runtime_instance_id (None | str | Unset):
        source (str | Unset):  Default: 'exec'.
        started_at (datetime.datetime | None | Unset):
        ended_at (datetime.datetime | None | Unset):
        duration_ms (int | None | Unset):
        timeout_seconds (int | None | Unset):
        exit_code (int | None | Unset):
        stdout_bytes (int | None | Unset):
        stderr_bytes (int | None | Unset):
        error_type (None | str | Unset):
        observed_at (datetime.datetime | None | Unset):
    """

    computer_id: str
    command_id: str
    status: str
    runtime_instance_id: None | str | Unset = UNSET
    source: str | Unset = "exec"
    started_at: datetime.datetime | None | Unset = UNSET
    ended_at: datetime.datetime | None | Unset = UNSET
    duration_ms: int | None | Unset = UNSET
    timeout_seconds: int | None | Unset = UNSET
    exit_code: int | None | Unset = UNSET
    stdout_bytes: int | None | Unset = UNSET
    stderr_bytes: int | None | Unset = UNSET
    error_type: None | str | Unset = UNSET
    observed_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        computer_id = self.computer_id

        command_id = self.command_id

        status = self.status

        runtime_instance_id: None | str | Unset
        if isinstance(self.runtime_instance_id, Unset):
            runtime_instance_id = UNSET
        else:
            runtime_instance_id = self.runtime_instance_id

        source = self.source

        started_at: None | str | Unset
        if isinstance(self.started_at, Unset):
            started_at = UNSET
        elif isinstance(self.started_at, datetime.datetime):
            started_at = self.started_at.isoformat()
        else:
            started_at = self.started_at

        ended_at: None | str | Unset
        if isinstance(self.ended_at, Unset):
            ended_at = UNSET
        elif isinstance(self.ended_at, datetime.datetime):
            ended_at = self.ended_at.isoformat()
        else:
            ended_at = self.ended_at

        duration_ms: int | None | Unset
        if isinstance(self.duration_ms, Unset):
            duration_ms = UNSET
        else:
            duration_ms = self.duration_ms

        timeout_seconds: int | None | Unset
        if isinstance(self.timeout_seconds, Unset):
            timeout_seconds = UNSET
        else:
            timeout_seconds = self.timeout_seconds

        exit_code: int | None | Unset
        if isinstance(self.exit_code, Unset):
            exit_code = UNSET
        else:
            exit_code = self.exit_code

        stdout_bytes: int | None | Unset
        if isinstance(self.stdout_bytes, Unset):
            stdout_bytes = UNSET
        else:
            stdout_bytes = self.stdout_bytes

        stderr_bytes: int | None | Unset
        if isinstance(self.stderr_bytes, Unset):
            stderr_bytes = UNSET
        else:
            stderr_bytes = self.stderr_bytes

        error_type: None | str | Unset
        if isinstance(self.error_type, Unset):
            error_type = UNSET
        else:
            error_type = self.error_type

        observed_at: None | str | Unset
        if isinstance(self.observed_at, Unset):
            observed_at = UNSET
        elif isinstance(self.observed_at, datetime.datetime):
            observed_at = self.observed_at.isoformat()
        else:
            observed_at = self.observed_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "computer_id": computer_id,
                "command_id": command_id,
                "status": status,
            }
        )
        if runtime_instance_id is not UNSET:
            field_dict["runtime_instance_id"] = runtime_instance_id
        if source is not UNSET:
            field_dict["source"] = source
        if started_at is not UNSET:
            field_dict["started_at"] = started_at
        if ended_at is not UNSET:
            field_dict["ended_at"] = ended_at
        if duration_ms is not UNSET:
            field_dict["duration_ms"] = duration_ms
        if timeout_seconds is not UNSET:
            field_dict["timeout_seconds"] = timeout_seconds
        if exit_code is not UNSET:
            field_dict["exit_code"] = exit_code
        if stdout_bytes is not UNSET:
            field_dict["stdout_bytes"] = stdout_bytes
        if stderr_bytes is not UNSET:
            field_dict["stderr_bytes"] = stderr_bytes
        if error_type is not UNSET:
            field_dict["error_type"] = error_type
        if observed_at is not UNSET:
            field_dict["observed_at"] = observed_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        computer_id = d.pop("computer_id")

        command_id = d.pop("command_id")

        status = d.pop("status")

        def _parse_runtime_instance_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        runtime_instance_id = _parse_runtime_instance_id(
            d.pop("runtime_instance_id", UNSET)
        )

        source = d.pop("source", UNSET)

        def _parse_started_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                started_at_type_0 = datetime.datetime.fromisoformat(data)

                return started_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        started_at = _parse_started_at(d.pop("started_at", UNSET))

        def _parse_ended_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                ended_at_type_0 = datetime.datetime.fromisoformat(data)

                return ended_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        ended_at = _parse_ended_at(d.pop("ended_at", UNSET))

        def _parse_duration_ms(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        duration_ms = _parse_duration_ms(d.pop("duration_ms", UNSET))

        def _parse_timeout_seconds(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        timeout_seconds = _parse_timeout_seconds(d.pop("timeout_seconds", UNSET))

        def _parse_exit_code(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        exit_code = _parse_exit_code(d.pop("exit_code", UNSET))

        def _parse_stdout_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        stdout_bytes = _parse_stdout_bytes(d.pop("stdout_bytes", UNSET))

        def _parse_stderr_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        stderr_bytes = _parse_stderr_bytes(d.pop("stderr_bytes", UNSET))

        def _parse_error_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error_type = _parse_error_type(d.pop("error_type", UNSET))

        def _parse_observed_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                observed_at_type_0 = datetime.datetime.fromisoformat(data)

                return observed_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        observed_at = _parse_observed_at(d.pop("observed_at", UNSET))

        sandbox_command_event_request = cls(
            computer_id=computer_id,
            command_id=command_id,
            status=status,
            runtime_instance_id=runtime_instance_id,
            source=source,
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=duration_ms,
            timeout_seconds=timeout_seconds,
            exit_code=exit_code,
            stdout_bytes=stdout_bytes,
            stderr_bytes=stderr_bytes,
            error_type=error_type,
            observed_at=observed_at,
        )

        sandbox_command_event_request.additional_properties = d
        return sandbox_command_event_request

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties

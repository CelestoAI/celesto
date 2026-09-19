from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="ComputerExecResponse")


@_attrs_define
class ComputerExecResponse:
    """Response from command execution.

    Attributes:
        exit_code (int):
        stdout (str):
        stderr (str):
        command_id (None | str | Unset):
        duration_ms (int | None | Unset):
        timed_out (bool | None | Unset):
    """

    exit_code: int
    stdout: str
    stderr: str
    command_id: None | str | Unset = UNSET
    duration_ms: int | None | Unset = UNSET
    timed_out: bool | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        exit_code = self.exit_code

        stdout = self.stdout

        stderr = self.stderr

        command_id: None | str | Unset
        if isinstance(self.command_id, Unset):
            command_id = UNSET
        else:
            command_id = self.command_id

        duration_ms: int | None | Unset
        if isinstance(self.duration_ms, Unset):
            duration_ms = UNSET
        else:
            duration_ms = self.duration_ms

        timed_out: bool | None | Unset
        if isinstance(self.timed_out, Unset):
            timed_out = UNSET
        else:
            timed_out = self.timed_out

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
            }
        )
        if command_id is not UNSET:
            field_dict["command_id"] = command_id
        if duration_ms is not UNSET:
            field_dict["duration_ms"] = duration_ms
        if timed_out is not UNSET:
            field_dict["timed_out"] = timed_out

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        exit_code = d.pop("exit_code")

        stdout = d.pop("stdout")

        stderr = d.pop("stderr")

        def _parse_command_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        command_id = _parse_command_id(d.pop("command_id", UNSET))

        def _parse_duration_ms(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        duration_ms = _parse_duration_ms(d.pop("duration_ms", UNSET))

        def _parse_timed_out(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        timed_out = _parse_timed_out(d.pop("timed_out", UNSET))

        computer_exec_response = cls(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            command_id=command_id,
            duration_ms=duration_ms,
            timed_out=timed_out,
        )

        computer_exec_response.additional_properties = d
        return computer_exec_response

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

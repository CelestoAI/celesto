from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset


T = TypeVar("T", bound="OpenClawExecResponse")


@_attrs_define
class OpenClawExecResponse:
    """
    Attributes:
        exit_code (int):
        stdout (str):
        stderr (str):
    """

    exit_code: int
    stdout: str
    stderr: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        exit_code = self.exit_code

        stdout = self.stdout

        stderr = self.stderr

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        exit_code = d.pop("exit_code")

        stdout = d.pop("stdout")

        stderr = d.pop("stderr")

        open_claw_exec_response = cls(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
        )

        open_claw_exec_response.additional_properties = d
        return open_claw_exec_response

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

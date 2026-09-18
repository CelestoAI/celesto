from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast

if TYPE_CHECKING:
    from ..models.sandbox_command_invocation_response import (
        SandboxCommandInvocationResponse,
    )


T = TypeVar("T", bound="SandboxCommandInvocationsResponse")


@_attrs_define
class SandboxCommandInvocationsResponse:
    """
    Attributes:
        commands (list[SandboxCommandInvocationResponse]):
        count (int):
    """

    commands: list[SandboxCommandInvocationResponse]
    count: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.sandbox_command_invocation_response import (
            SandboxCommandInvocationResponse,
        )  # noqa: PLC0415

        commands = []
        for commands_item_data in self.commands:
            commands_item = commands_item_data.to_dict()
            commands.append(commands_item)

        count = self.count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "commands": commands,
                "count": count,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sandbox_command_invocation_response import (
            SandboxCommandInvocationResponse,
        )  # noqa: PLC0415

        d = dict(src_dict)
        commands = []
        _commands = d.pop("commands")
        for commands_item_data in _commands:
            commands_item = SandboxCommandInvocationResponse.from_dict(
                commands_item_data
            )

            commands.append(commands_item)

        count = d.pop("count")

        sandbox_command_invocations_response = cls(
            commands=commands,
            count=count,
        )

        sandbox_command_invocations_response.additional_properties = d
        return sandbox_command_invocations_response

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

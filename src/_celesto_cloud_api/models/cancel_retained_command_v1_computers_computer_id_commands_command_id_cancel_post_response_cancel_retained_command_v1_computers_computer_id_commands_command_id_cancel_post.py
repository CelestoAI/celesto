from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset


T = TypeVar(
    "T",
    bound="CancelRetainedCommandV1ComputersComputerIdCommandsCommandIdCancelPostResponseCancelRetainedCommandV1ComputersComputerIdCommandsCommandIdCancelPost",
)


@_attrs_define
class CancelRetainedCommandV1ComputersComputerIdCommandsCommandIdCancelPostResponseCancelRetainedCommandV1ComputersComputerIdCommandsCommandIdCancelPost:
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cancel_retained_command_v1_computers_computer_id_commands_command_id_cancel_post_response_cancel_retained_command_v1_computers_computer_id_commands_command_id_cancel_post = cls()

        cancel_retained_command_v1_computers_computer_id_commands_command_id_cancel_post_response_cancel_retained_command_v1_computers_computer_id_commands_command_id_cancel_post.additional_properties = d
        return cancel_retained_command_v1_computers_computer_id_commands_command_id_cancel_post_response_cancel_retained_command_v1_computers_computer_id_commands_command_id_cancel_post

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

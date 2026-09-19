from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="ComputerTerminalSessionRequest")


@_attrs_define
class ComputerTerminalSessionRequest:
    """Request to create or reattach to a durable terminal session.

    Attributes:
        terminal_id (None | str | Unset): Existing terminal session id to reattach. Omit to create a new session.
    """

    terminal_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        terminal_id: None | str | Unset
        if isinstance(self.terminal_id, Unset):
            terminal_id = UNSET
        else:
            terminal_id = self.terminal_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if terminal_id is not UNSET:
            field_dict["terminal_id"] = terminal_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_terminal_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        terminal_id = _parse_terminal_id(d.pop("terminal_id", UNSET))

        computer_terminal_session_request = cls(
            terminal_id=terminal_id,
        )

        computer_terminal_session_request.additional_properties = d
        return computer_terminal_session_request

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

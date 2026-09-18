from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.computer_display_connection_request_mode import (
    ComputerDisplayConnectionRequestMode,
)
from ..types import UNSET, Unset


T = TypeVar("T", bound="ComputerDisplayConnectionRequest")


@_attrs_define
class ComputerDisplayConnectionRequest:
    """Request to attach to a computer's graphical display.

    Attributes:
        mode (ComputerDisplayConnectionRequestMode | Unset): read_only viewers can watch but not click or type. Default:
            ComputerDisplayConnectionRequestMode.READ_ONLY.
    """

    mode: ComputerDisplayConnectionRequestMode | Unset = (
        ComputerDisplayConnectionRequestMode.READ_ONLY
    )
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        mode: str | Unset = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if mode is not UNSET:
            field_dict["mode"] = mode

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _mode = d.pop("mode", UNSET)
        mode: ComputerDisplayConnectionRequestMode | Unset
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = ComputerDisplayConnectionRequestMode(_mode)

        computer_display_connection_request = cls(
            mode=mode,
        )

        computer_display_connection_request.additional_properties = d
        return computer_display_connection_request

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

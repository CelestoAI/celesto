from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast

if TYPE_CHECKING:
    from ..models.computer_response import ComputerResponse


T = TypeVar("T", bound="ComputerListResponse")


@_attrs_define
class ComputerListResponse:
    """Response for listing compute VMs.

    Attributes:
        computers (list[ComputerResponse]):
        count (int):
    """

    computers: list[ComputerResponse]
    count: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.computer_response import ComputerResponse  # noqa: PLC0415

        computers = []
        for computers_item_data in self.computers:
            computers_item = computers_item_data.to_dict()
            computers.append(computers_item)

        count = self.count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "computers": computers,
                "count": count,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.computer_response import ComputerResponse  # noqa: PLC0415

        d = dict(src_dict)
        computers = []
        _computers = d.pop("computers")
        for computers_item_data in _computers:
            computers_item = ComputerResponse.from_dict(computers_item_data)

            computers.append(computers_item)

        count = d.pop("count")

        computer_list_response = cls(
            computers=computers,
            count=count,
        )

        computer_list_response.additional_properties = d
        return computer_list_response

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

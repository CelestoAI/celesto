from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast

if TYPE_CHECKING:
    from ..models.inventory import Inventory


T = TypeVar("T", bound="PollRequest")


@_attrs_define
class PollRequest:
    """
    Attributes:
        epoch (int):
        state_id (str):
        inventory (Inventory):
    """

    epoch: int
    state_id: str
    inventory: Inventory
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.inventory import Inventory  # noqa: PLC0415

        epoch = self.epoch

        state_id = self.state_id

        inventory = self.inventory.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "epoch": epoch,
                "state_id": state_id,
                "inventory": inventory,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory import Inventory  # noqa: PLC0415

        d = dict(src_dict)
        epoch = d.pop("epoch")

        state_id = d.pop("state_id")

        inventory = Inventory.from_dict(d.pop("inventory"))

        poll_request = cls(
            epoch=epoch,
            state_id=state_id,
            inventory=inventory,
        )

        poll_request.additional_properties = d
        return poll_request

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

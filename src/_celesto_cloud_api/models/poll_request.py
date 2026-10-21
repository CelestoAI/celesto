from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

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
        active_command_ids (list[str] | Unset):
        inventory_complete (bool | Unset):  Default: True.
    """

    epoch: int
    state_id: str
    inventory: Inventory
    active_command_ids: list[str] | Unset = UNSET
    inventory_complete: bool | Unset = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.inventory import Inventory  # noqa: PLC0415

        epoch = self.epoch

        state_id = self.state_id

        inventory = self.inventory.to_dict()

        active_command_ids: list[str] | Unset = UNSET
        if not isinstance(self.active_command_ids, Unset):
            active_command_ids = self.active_command_ids

        inventory_complete = self.inventory_complete

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "epoch": epoch,
                "state_id": state_id,
                "inventory": inventory,
            }
        )
        if active_command_ids is not UNSET:
            field_dict["active_command_ids"] = active_command_ids
        if inventory_complete is not UNSET:
            field_dict["inventory_complete"] = inventory_complete

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory import Inventory  # noqa: PLC0415

        d = dict(src_dict)
        epoch = d.pop("epoch")

        state_id = d.pop("state_id")

        inventory = Inventory.from_dict(d.pop("inventory"))

        active_command_ids = cast(list[str], d.pop("active_command_ids", UNSET))

        inventory_complete = d.pop("inventory_complete", UNSET)

        poll_request = cls(
            epoch=epoch,
            state_id=state_id,
            inventory=inventory,
            active_command_ids=active_command_ids,
            inventory_complete=inventory_complete,
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

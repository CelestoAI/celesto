from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from uuid import UUID


T = TypeVar("T", bound="FleetReleaseRunningComputerState")


@_attrs_define
class FleetReleaseRunningComputerState:
    """The non-public host binding needed by a release continuity check.

    Attributes:
        computer_id (str):
        host_id (str):
        state_id (UUID):
        computer_status (str):
        allocation_state (str):
    """

    computer_id: str
    host_id: str
    state_id: UUID
    computer_status: str
    allocation_state: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        computer_id = self.computer_id

        host_id = self.host_id

        state_id = str(self.state_id)

        computer_status = self.computer_status

        allocation_state = self.allocation_state

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "computer_id": computer_id,
                "host_id": host_id,
                "state_id": state_id,
                "computer_status": computer_status,
                "allocation_state": allocation_state,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        computer_id = d.pop("computer_id")

        host_id = d.pop("host_id")

        state_id = UUID(d.pop("state_id"))

        computer_status = d.pop("computer_status")

        allocation_state = d.pop("allocation_state")

        fleet_release_running_computer_state = cls(
            computer_id=computer_id,
            host_id=host_id,
            state_id=state_id,
            computer_status=computer_status,
            allocation_state=allocation_state,
        )

        fleet_release_running_computer_state.additional_properties = d
        return fleet_release_running_computer_state

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

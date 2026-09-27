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


T = TypeVar("T", bound="SessionRequest")


@_attrs_define
class SessionRequest:
    """
    Attributes:
        state_id (str):
        inventory (Inventory):
        stream_protocol_version (int | Unset):  Default: 1.
        usage_running_heartbeat (bool | Unset):  Default: False.
    """

    state_id: str
    inventory: Inventory
    stream_protocol_version: int | Unset = 1
    usage_running_heartbeat: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.inventory import Inventory  # noqa: PLC0415

        state_id = self.state_id

        inventory = self.inventory.to_dict()

        stream_protocol_version = self.stream_protocol_version

        usage_running_heartbeat = self.usage_running_heartbeat

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "state_id": state_id,
                "inventory": inventory,
            }
        )
        if stream_protocol_version is not UNSET:
            field_dict["stream_protocol_version"] = stream_protocol_version
        if usage_running_heartbeat is not UNSET:
            field_dict["usage_running_heartbeat"] = usage_running_heartbeat

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory import Inventory  # noqa: PLC0415

        d = dict(src_dict)
        state_id = d.pop("state_id")

        inventory = Inventory.from_dict(d.pop("inventory"))

        stream_protocol_version = d.pop("stream_protocol_version", UNSET)

        usage_running_heartbeat = d.pop("usage_running_heartbeat", UNSET)

        session_request = cls(
            state_id=state_id,
            inventory=inventory,
            stream_protocol_version=stream_protocol_version,
            usage_running_heartbeat=usage_running_heartbeat,
        )

        session_request.additional_properties = d
        return session_request

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

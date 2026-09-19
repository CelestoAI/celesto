from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.sandbox_command_event_request import SandboxCommandEventRequest


T = TypeVar("T", bound="HostCommandEventsRequest")


@_attrs_define
class HostCommandEventsRequest:
    """
    Attributes:
        host_boot_id (None | str | Unset):
        events (list[SandboxCommandEventRequest] | Unset):
    """

    host_boot_id: None | str | Unset = UNSET
    events: list[SandboxCommandEventRequest] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.sandbox_command_event_request import SandboxCommandEventRequest  # noqa: PLC0415

        host_boot_id: None | str | Unset
        if isinstance(self.host_boot_id, Unset):
            host_boot_id = UNSET
        else:
            host_boot_id = self.host_boot_id

        events: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.events, Unset):
            events = []
            for events_item_data in self.events:
                events_item = events_item_data.to_dict()
                events.append(events_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if host_boot_id is not UNSET:
            field_dict["host_boot_id"] = host_boot_id
        if events is not UNSET:
            field_dict["events"] = events

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sandbox_command_event_request import SandboxCommandEventRequest  # noqa: PLC0415

        d = dict(src_dict)

        def _parse_host_boot_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        host_boot_id = _parse_host_boot_id(d.pop("host_boot_id", UNSET))

        _events = d.pop("events", UNSET)
        events: list[SandboxCommandEventRequest] | Unset = UNSET
        if _events is not UNSET:
            events = []
            for events_item_data in _events:
                events_item = SandboxCommandEventRequest.from_dict(events_item_data)

                events.append(events_item)

        host_command_events_request = cls(
            host_boot_id=host_boot_id,
            events=events,
        )

        host_command_events_request.additional_properties = d
        return host_command_events_request

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

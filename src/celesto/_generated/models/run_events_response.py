from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.run_event_item import RunEventItem


T = TypeVar("T", bound="RunEventsResponse")


@_attrs_define
class RunEventsResponse:
    """
    Attributes:
        data (list[RunEventItem]):
        events_version (str):
        has_more (bool | Unset):  Default: False.
        next_after_seq (int | None | Unset):
    """

    data: list[RunEventItem]
    events_version: str
    has_more: bool | Unset = False
    next_after_seq: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.run_event_item import RunEventItem  # noqa: PLC0415

        data = []
        for data_item_data in self.data:
            data_item = data_item_data.to_dict()
            data.append(data_item)

        events_version = self.events_version

        has_more = self.has_more

        next_after_seq: int | None | Unset
        if isinstance(self.next_after_seq, Unset):
            next_after_seq = UNSET
        else:
            next_after_seq = self.next_after_seq

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
                "events_version": events_version,
            }
        )
        if has_more is not UNSET:
            field_dict["has_more"] = has_more
        if next_after_seq is not UNSET:
            field_dict["next_after_seq"] = next_after_seq

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_event_item import RunEventItem  # noqa: PLC0415

        d = dict(src_dict)
        data = []
        _data = d.pop("data")
        for data_item_data in _data:
            data_item = RunEventItem.from_dict(data_item_data)

            data.append(data_item)

        events_version = d.pop("events_version")

        has_more = d.pop("has_more", UNSET)

        def _parse_next_after_seq(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        next_after_seq = _parse_next_after_seq(d.pop("next_after_seq", UNSET))

        run_events_response = cls(
            data=data,
            events_version=events_version,
            has_more=has_more,
            next_after_seq=next_after_seq,
        )

        run_events_response.additional_properties = d
        return run_events_response

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

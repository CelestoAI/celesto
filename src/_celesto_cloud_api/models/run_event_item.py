from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast

if TYPE_CHECKING:
    from ..models.run_event_item_data import RunEventItemData


T = TypeVar("T", bound="RunEventItem")


@_attrs_define
class RunEventItem:
    """
    Attributes:
        seq (int):
        event (str):
        data (RunEventItemData):
    """

    seq: int
    event: str
    data: RunEventItemData
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.run_event_item_data import RunEventItemData  # noqa: PLC0415

        seq = self.seq

        event = self.event

        data = self.data.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "seq": seq,
                "event": event,
                "data": data,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_event_item_data import RunEventItemData  # noqa: PLC0415

        d = dict(src_dict)
        seq = d.pop("seq")

        event = d.pop("event")

        data = RunEventItemData.from_dict(d.pop("data"))

        run_event_item = cls(
            seq=seq,
            event=event,
            data=data,
        )

        run_event_item.additional_properties = d
        return run_event_item

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast

if TYPE_CHECKING:
    from ..models.trace_ingest_payload_data_item import TraceIngestPayloadDataItem


T = TypeVar("T", bound="TraceIngestPayload")


@_attrs_define
class TraceIngestPayload:
    """Request body for trace ingestion endpoint.

    Accepts a list of items where each item has an 'object' field
    indicating whether it's a 'trace' or 'trace.span'.

        Attributes:
            data (list[TraceIngestPayloadDataItem]): List of trace/span items from SDK
    """

    data: list[TraceIngestPayloadDataItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.trace_ingest_payload_data_item import TraceIngestPayloadDataItem  # noqa: PLC0415

        data = []
        for data_item_data in self.data:
            data_item = data_item_data.to_dict()
            data.append(data_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trace_ingest_payload_data_item import TraceIngestPayloadDataItem  # noqa: PLC0415

        d = dict(src_dict)
        data = []
        _data = d.pop("data")
        for data_item_data in _data:
            data_item = TraceIngestPayloadDataItem.from_dict(data_item_data)

            data.append(data_item)

        trace_ingest_payload = cls(
            data=data,
        )

        trace_ingest_payload.additional_properties = d
        return trace_ingest_payload

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

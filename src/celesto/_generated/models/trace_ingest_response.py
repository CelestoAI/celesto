from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="TraceIngestResponse")


@_attrs_define
class TraceIngestResponse:
    """Response from trace ingestion endpoint.

    Attributes:
        accepted (int): Number of items accepted
        trace_ids (list[str] | Unset): Trace IDs that will be materialized
    """

    accepted: int
    trace_ids: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        accepted = self.accepted

        trace_ids: list[str] | Unset = UNSET
        if not isinstance(self.trace_ids, Unset):
            trace_ids = self.trace_ids

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "accepted": accepted,
            }
        )
        if trace_ids is not UNSET:
            field_dict["trace_ids"] = trace_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        accepted = d.pop("accepted")

        trace_ids = cast(list[str], d.pop("trace_ids", UNSET))

        trace_ingest_response = cls(
            accepted=accepted,
            trace_ids=trace_ids,
        )

        trace_ingest_response.additional_properties = d
        return trace_ingest_response

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

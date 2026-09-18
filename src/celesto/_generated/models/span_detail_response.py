from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.span_detail_response_error_type_0 import SpanDetailResponseErrorType0
    from ..models.span_detail_response_span_data import SpanDetailResponseSpanData


T = TypeVar("T", bound="SpanDetailResponse")


@_attrs_define
class SpanDetailResponse:
    """Raw span data for detailed inspection.

    Used when user expands "Full details" in the UI.

        Attributes:
            id (str): Span ID
            trace_id (str):
            parent_id (None | str | Unset):
            started_at (datetime.datetime | None | Unset):
            ended_at (datetime.datetime | None | Unset):
            span_data (SpanDetailResponseSpanData | Unset): Full span_data payload
            error (None | SpanDetailResponseErrorType0 | Unset):
    """

    id: str
    trace_id: str
    parent_id: None | str | Unset = UNSET
    started_at: datetime.datetime | None | Unset = UNSET
    ended_at: datetime.datetime | None | Unset = UNSET
    span_data: SpanDetailResponseSpanData | Unset = UNSET
    error: None | SpanDetailResponseErrorType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.span_detail_response_error_type_0 import (
            SpanDetailResponseErrorType0,
        )  # noqa: PLC0415
        from ..models.span_detail_response_span_data import SpanDetailResponseSpanData  # noqa: PLC0415

        id = self.id

        trace_id = self.trace_id

        parent_id: None | str | Unset
        if isinstance(self.parent_id, Unset):
            parent_id = UNSET
        else:
            parent_id = self.parent_id

        started_at: None | str | Unset
        if isinstance(self.started_at, Unset):
            started_at = UNSET
        elif isinstance(self.started_at, datetime.datetime):
            started_at = self.started_at.isoformat()
        else:
            started_at = self.started_at

        ended_at: None | str | Unset
        if isinstance(self.ended_at, Unset):
            ended_at = UNSET
        elif isinstance(self.ended_at, datetime.datetime):
            ended_at = self.ended_at.isoformat()
        else:
            ended_at = self.ended_at

        span_data: dict[str, Any] | Unset = UNSET
        if not isinstance(self.span_data, Unset):
            span_data = self.span_data.to_dict()

        error: dict[str, Any] | None | Unset
        if isinstance(self.error, Unset):
            error = UNSET
        elif isinstance(self.error, SpanDetailResponseErrorType0):
            error = self.error.to_dict()
        else:
            error = self.error

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "trace_id": trace_id,
            }
        )
        if parent_id is not UNSET:
            field_dict["parent_id"] = parent_id
        if started_at is not UNSET:
            field_dict["started_at"] = started_at
        if ended_at is not UNSET:
            field_dict["ended_at"] = ended_at
        if span_data is not UNSET:
            field_dict["span_data"] = span_data
        if error is not UNSET:
            field_dict["error"] = error

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.span_detail_response_error_type_0 import (
            SpanDetailResponseErrorType0,
        )  # noqa: PLC0415
        from ..models.span_detail_response_span_data import SpanDetailResponseSpanData  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        trace_id = d.pop("trace_id")

        def _parse_parent_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        parent_id = _parse_parent_id(d.pop("parent_id", UNSET))

        def _parse_started_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                started_at_type_0 = datetime.datetime.fromisoformat(data)

                return started_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        started_at = _parse_started_at(d.pop("started_at", UNSET))

        def _parse_ended_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                ended_at_type_0 = datetime.datetime.fromisoformat(data)

                return ended_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        ended_at = _parse_ended_at(d.pop("ended_at", UNSET))

        _span_data = d.pop("span_data", UNSET)
        span_data: SpanDetailResponseSpanData | Unset
        if isinstance(_span_data, Unset):
            span_data = UNSET
        else:
            span_data = SpanDetailResponseSpanData.from_dict(_span_data)

        def _parse_error(data: object) -> None | SpanDetailResponseErrorType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                error_type_0 = SpanDetailResponseErrorType0.from_dict(data)

                return error_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | SpanDetailResponseErrorType0 | Unset, data)

        error = _parse_error(d.pop("error", UNSET))

        span_detail_response = cls(
            id=id,
            trace_id=trace_id,
            parent_id=parent_id,
            started_at=started_at,
            ended_at=ended_at,
            span_data=span_data,
            error=error,
        )

        span_detail_response.additional_properties = d
        return span_detail_response

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

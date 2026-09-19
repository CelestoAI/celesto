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
    from ..models.trace_event_item import TraceEventItem


T = TypeVar("T", bound="TraceEventsResponse")


@_attrs_define
class TraceEventsResponse:
    """List of materialized events for a trace.

    Primary data source for tree + waterfall UI rendering.

        Attributes:
            trace_id (str):
            events (list[TraceEventItem]):
            trace_start (datetime.datetime | None | Unset): Absolute start time of the trace
            duration_ms (int | None | Unset): Total trace duration
    """

    trace_id: str
    events: list[TraceEventItem]
    trace_start: datetime.datetime | None | Unset = UNSET
    duration_ms: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.trace_event_item import TraceEventItem  # noqa: PLC0415

        trace_id = self.trace_id

        events = []
        for events_item_data in self.events:
            events_item = events_item_data.to_dict()
            events.append(events_item)

        trace_start: None | str | Unset
        if isinstance(self.trace_start, Unset):
            trace_start = UNSET
        elif isinstance(self.trace_start, datetime.datetime):
            trace_start = self.trace_start.isoformat()
        else:
            trace_start = self.trace_start

        duration_ms: int | None | Unset
        if isinstance(self.duration_ms, Unset):
            duration_ms = UNSET
        else:
            duration_ms = self.duration_ms

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "trace_id": trace_id,
                "events": events,
            }
        )
        if trace_start is not UNSET:
            field_dict["trace_start"] = trace_start
        if duration_ms is not UNSET:
            field_dict["duration_ms"] = duration_ms

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.trace_event_item import TraceEventItem  # noqa: PLC0415

        d = dict(src_dict)
        trace_id = d.pop("trace_id")

        events = []
        _events = d.pop("events")
        for events_item_data in _events:
            events_item = TraceEventItem.from_dict(events_item_data)

            events.append(events_item)

        def _parse_trace_start(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                trace_start_type_0 = datetime.datetime.fromisoformat(data)

                return trace_start_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        trace_start = _parse_trace_start(d.pop("trace_start", UNSET))

        def _parse_duration_ms(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        duration_ms = _parse_duration_ms(d.pop("duration_ms", UNSET))

        trace_events_response = cls(
            trace_id=trace_id,
            events=events,
            trace_start=trace_start,
            duration_ms=duration_ms,
        )

        trace_events_response.additional_properties = d
        return trace_events_response

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

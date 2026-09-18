from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.event_meta import EventMeta


T = TypeVar("T", bound="TraceEventItem")


@_attrs_define
class TraceEventItem:
    """A single materialized event for UI rendering.

    Attributes:
        span_id (str): Original span ID
        seq (int): DFS traversal order
        depth (int): Nesting depth
        kind (str): Event kind: agent, llm, tool, handoff, guardrail, custom
        label (str): Human-readable label
        start_ms (int): Start time in ms from trace start
        parent_id (None | str | Unset): Parent span ID
        dur_ms (int | None | Unset): Duration in ms
        status (str | Unset): ok or error Default: 'ok'.
        meta (EventMeta | None | Unset):
    """

    span_id: str
    seq: int
    depth: int
    kind: str
    label: str
    start_ms: int
    parent_id: None | str | Unset = UNSET
    dur_ms: int | None | Unset = UNSET
    status: str | Unset = "ok"
    meta: EventMeta | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.event_meta import EventMeta  # noqa: PLC0415

        span_id = self.span_id

        seq = self.seq

        depth = self.depth

        kind = self.kind

        label = self.label

        start_ms = self.start_ms

        parent_id: None | str | Unset
        if isinstance(self.parent_id, Unset):
            parent_id = UNSET
        else:
            parent_id = self.parent_id

        dur_ms: int | None | Unset
        if isinstance(self.dur_ms, Unset):
            dur_ms = UNSET
        else:
            dur_ms = self.dur_ms

        status = self.status

        meta: dict[str, Any] | None | Unset
        if isinstance(self.meta, Unset):
            meta = UNSET
        elif isinstance(self.meta, EventMeta):
            meta = self.meta.to_dict()
        else:
            meta = self.meta

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "span_id": span_id,
                "seq": seq,
                "depth": depth,
                "kind": kind,
                "label": label,
                "start_ms": start_ms,
            }
        )
        if parent_id is not UNSET:
            field_dict["parent_id"] = parent_id
        if dur_ms is not UNSET:
            field_dict["dur_ms"] = dur_ms
        if status is not UNSET:
            field_dict["status"] = status
        if meta is not UNSET:
            field_dict["meta"] = meta

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.event_meta import EventMeta  # noqa: PLC0415

        d = dict(src_dict)
        span_id = d.pop("span_id")

        seq = d.pop("seq")

        depth = d.pop("depth")

        kind = d.pop("kind")

        label = d.pop("label")

        start_ms = d.pop("start_ms")

        def _parse_parent_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        parent_id = _parse_parent_id(d.pop("parent_id", UNSET))

        def _parse_dur_ms(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        dur_ms = _parse_dur_ms(d.pop("dur_ms", UNSET))

        status = d.pop("status", UNSET)

        def _parse_meta(data: object) -> EventMeta | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                meta_type_0 = EventMeta.from_dict(data)

                return meta_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(EventMeta | None | Unset, data)

        meta = _parse_meta(d.pop("meta", UNSET))

        trace_event_item = cls(
            span_id=span_id,
            seq=seq,
            depth=depth,
            kind=kind,
            label=label,
            start_ms=start_ms,
            parent_id=parent_id,
            dur_ms=dur_ms,
            status=status,
            meta=meta,
        )

        trace_event_item.additional_properties = d
        return trace_event_item

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

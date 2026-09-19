from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
import datetime


T = TypeVar("T", bound="TraceListItem")


@_attrs_define
class TraceListItem:
    """Summary of a trace for list views.

    Attributes:
        id (str): Trace ID
        created_at (datetime.datetime):
        workflow_name (None | str | Unset): Name of the workflow/agent
        group_id (None | str | Unset): Conversation/session grouping ID
        user_id (None | str | Unset): User ID associated with the trace
        status (str | Unset): ok or error Default: 'ok'.
        span_count (int | Unset): Number of spans Default: 0.
        duration_ms (int | None | Unset): Total duration in ms
        started_at (datetime.datetime | None | Unset):
        ended_at (datetime.datetime | None | Unset):
        is_shared (bool | Unset): Whether trace has active share link Default: False.
    """

    id: str
    created_at: datetime.datetime
    workflow_name: None | str | Unset = UNSET
    group_id: None | str | Unset = UNSET
    user_id: None | str | Unset = UNSET
    status: str | Unset = "ok"
    span_count: int | Unset = 0
    duration_ms: int | None | Unset = UNSET
    started_at: datetime.datetime | None | Unset = UNSET
    ended_at: datetime.datetime | None | Unset = UNSET
    is_shared: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        created_at = self.created_at.isoformat()

        workflow_name: None | str | Unset
        if isinstance(self.workflow_name, Unset):
            workflow_name = UNSET
        else:
            workflow_name = self.workflow_name

        group_id: None | str | Unset
        if isinstance(self.group_id, Unset):
            group_id = UNSET
        else:
            group_id = self.group_id

        user_id: None | str | Unset
        if isinstance(self.user_id, Unset):
            user_id = UNSET
        else:
            user_id = self.user_id

        status = self.status

        span_count = self.span_count

        duration_ms: int | None | Unset
        if isinstance(self.duration_ms, Unset):
            duration_ms = UNSET
        else:
            duration_ms = self.duration_ms

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

        is_shared = self.is_shared

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "created_at": created_at,
            }
        )
        if workflow_name is not UNSET:
            field_dict["workflow_name"] = workflow_name
        if group_id is not UNSET:
            field_dict["group_id"] = group_id
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if status is not UNSET:
            field_dict["status"] = status
        if span_count is not UNSET:
            field_dict["span_count"] = span_count
        if duration_ms is not UNSET:
            field_dict["duration_ms"] = duration_ms
        if started_at is not UNSET:
            field_dict["started_at"] = started_at
        if ended_at is not UNSET:
            field_dict["ended_at"] = ended_at
        if is_shared is not UNSET:
            field_dict["is_shared"] = is_shared

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        def _parse_workflow_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        workflow_name = _parse_workflow_name(d.pop("workflow_name", UNSET))

        def _parse_group_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        group_id = _parse_group_id(d.pop("group_id", UNSET))

        def _parse_user_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        user_id = _parse_user_id(d.pop("user_id", UNSET))

        status = d.pop("status", UNSET)

        span_count = d.pop("span_count", UNSET)

        def _parse_duration_ms(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        duration_ms = _parse_duration_ms(d.pop("duration_ms", UNSET))

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

        is_shared = d.pop("is_shared", UNSET)

        trace_list_item = cls(
            id=id,
            created_at=created_at,
            workflow_name=workflow_name,
            group_id=group_id,
            user_id=user_id,
            status=status,
            span_count=span_count,
            duration_ms=duration_ms,
            started_at=started_at,
            ended_at=ended_at,
            is_shared=is_shared,
        )

        trace_list_item.additional_properties = d
        return trace_list_item

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

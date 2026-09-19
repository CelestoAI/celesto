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
    from ..models.active_share_info import ActiveShareInfo
    from ..models.trace_detail_response_trace_metadata_type_0 import (
        TraceDetailResponseTraceMetadataType0,
    )
    from ..models.trace_stats import TraceStats


T = TypeVar("T", bound="TraceDetailResponse")


@_attrs_define
class TraceDetailResponse:
    """Full trace metadata with aggregated stats.

    Attributes:
        id (str):
        organization_id (str):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        user_id (None | str | Unset):
        workflow_name (None | str | Unset):
        group_id (None | str | Unset):
        trace_metadata (None | TraceDetailResponseTraceMetadataType0 | Unset):
        span_count (int | Unset):  Default: 0.
        started_at (datetime.datetime | None | Unset):
        ended_at (datetime.datetime | None | Unset):
        duration_ms (int | None | Unset):
        has_error (bool | Unset):  Default: False.
        stats (None | TraceStats | Unset):
        share_info (ActiveShareInfo | None | Unset):
    """

    id: str
    organization_id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    user_id: None | str | Unset = UNSET
    workflow_name: None | str | Unset = UNSET
    group_id: None | str | Unset = UNSET
    trace_metadata: None | TraceDetailResponseTraceMetadataType0 | Unset = UNSET
    span_count: int | Unset = 0
    started_at: datetime.datetime | None | Unset = UNSET
    ended_at: datetime.datetime | None | Unset = UNSET
    duration_ms: int | None | Unset = UNSET
    has_error: bool | Unset = False
    stats: None | TraceStats | Unset = UNSET
    share_info: ActiveShareInfo | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.active_share_info import ActiveShareInfo  # noqa: PLC0415
        from ..models.trace_detail_response_trace_metadata_type_0 import (
            TraceDetailResponseTraceMetadataType0,
        )  # noqa: PLC0415
        from ..models.trace_stats import TraceStats  # noqa: PLC0415

        id = self.id

        organization_id = self.organization_id

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        user_id: None | str | Unset
        if isinstance(self.user_id, Unset):
            user_id = UNSET
        else:
            user_id = self.user_id

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

        trace_metadata: dict[str, Any] | None | Unset
        if isinstance(self.trace_metadata, Unset):
            trace_metadata = UNSET
        elif isinstance(self.trace_metadata, TraceDetailResponseTraceMetadataType0):
            trace_metadata = self.trace_metadata.to_dict()
        else:
            trace_metadata = self.trace_metadata

        span_count = self.span_count

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

        duration_ms: int | None | Unset
        if isinstance(self.duration_ms, Unset):
            duration_ms = UNSET
        else:
            duration_ms = self.duration_ms

        has_error = self.has_error

        stats: dict[str, Any] | None | Unset
        if isinstance(self.stats, Unset):
            stats = UNSET
        elif isinstance(self.stats, TraceStats):
            stats = self.stats.to_dict()
        else:
            stats = self.stats

        share_info: dict[str, Any] | None | Unset
        if isinstance(self.share_info, Unset):
            share_info = UNSET
        elif isinstance(self.share_info, ActiveShareInfo):
            share_info = self.share_info.to_dict()
        else:
            share_info = self.share_info

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "organization_id": organization_id,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if workflow_name is not UNSET:
            field_dict["workflow_name"] = workflow_name
        if group_id is not UNSET:
            field_dict["group_id"] = group_id
        if trace_metadata is not UNSET:
            field_dict["trace_metadata"] = trace_metadata
        if span_count is not UNSET:
            field_dict["span_count"] = span_count
        if started_at is not UNSET:
            field_dict["started_at"] = started_at
        if ended_at is not UNSET:
            field_dict["ended_at"] = ended_at
        if duration_ms is not UNSET:
            field_dict["duration_ms"] = duration_ms
        if has_error is not UNSET:
            field_dict["has_error"] = has_error
        if stats is not UNSET:
            field_dict["stats"] = stats
        if share_info is not UNSET:
            field_dict["share_info"] = share_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.active_share_info import ActiveShareInfo  # noqa: PLC0415
        from ..models.trace_detail_response_trace_metadata_type_0 import (
            TraceDetailResponseTraceMetadataType0,
        )  # noqa: PLC0415
        from ..models.trace_stats import TraceStats  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        organization_id = d.pop("organization_id")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        def _parse_user_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        user_id = _parse_user_id(d.pop("user_id", UNSET))

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

        def _parse_trace_metadata(
            data: object,
        ) -> None | TraceDetailResponseTraceMetadataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                trace_metadata_type_0 = TraceDetailResponseTraceMetadataType0.from_dict(
                    data
                )

                return trace_metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TraceDetailResponseTraceMetadataType0 | Unset, data)

        trace_metadata = _parse_trace_metadata(d.pop("trace_metadata", UNSET))

        span_count = d.pop("span_count", UNSET)

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

        def _parse_duration_ms(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        duration_ms = _parse_duration_ms(d.pop("duration_ms", UNSET))

        has_error = d.pop("has_error", UNSET)

        def _parse_stats(data: object) -> None | TraceStats | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                stats_type_0 = TraceStats.from_dict(data)

                return stats_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TraceStats | Unset, data)

        stats = _parse_stats(d.pop("stats", UNSET))

        def _parse_share_info(data: object) -> ActiveShareInfo | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                share_info_type_0 = ActiveShareInfo.from_dict(data)

                return share_info_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ActiveShareInfo | None | Unset, data)

        share_info = _parse_share_info(d.pop("share_info", UNSET))

        trace_detail_response = cls(
            id=id,
            organization_id=organization_id,
            created_at=created_at,
            updated_at=updated_at,
            user_id=user_id,
            workflow_name=workflow_name,
            group_id=group_id,
            trace_metadata=trace_metadata,
            span_count=span_count,
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=duration_ms,
            has_error=has_error,
            stats=stats,
            share_info=share_info,
        )

        trace_detail_response.additional_properties = d
        return trace_detail_response

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
import datetime


T = TypeVar("T", bound="CiMinutesBucket")


@_attrs_define
class CiMinutesBucket:
    """CI running minutes in one calendar-aligned UTC hour, day, or Monday-start week.

    Attributes:
        started_at (datetime.datetime):
        ended_at (datetime.datetime):
        ci_runtime_minutes (float | None):
        history_complete (bool):
        in_progress (bool):
    """

    started_at: datetime.datetime
    ended_at: datetime.datetime
    ci_runtime_minutes: float | None
    history_complete: bool
    in_progress: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        started_at = self.started_at.isoformat()

        ended_at = self.ended_at.isoformat()

        ci_runtime_minutes: float | None
        ci_runtime_minutes = self.ci_runtime_minutes

        history_complete = self.history_complete

        in_progress = self.in_progress

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "started_at": started_at,
                "ended_at": ended_at,
                "ci_runtime_minutes": ci_runtime_minutes,
                "history_complete": history_complete,
                "in_progress": in_progress,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        started_at = datetime.datetime.fromisoformat(d.pop("started_at"))

        ended_at = datetime.datetime.fromisoformat(d.pop("ended_at"))

        def _parse_ci_runtime_minutes(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        ci_runtime_minutes = _parse_ci_runtime_minutes(d.pop("ci_runtime_minutes"))

        history_complete = d.pop("history_complete")

        in_progress = d.pop("in_progress")

        ci_minutes_bucket = cls(
            started_at=started_at,
            ended_at=ended_at,
            ci_runtime_minutes=ci_runtime_minutes,
            history_complete=history_complete,
            in_progress=in_progress,
        )

        ci_minutes_bucket.additional_properties = d
        return ci_minutes_bucket

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

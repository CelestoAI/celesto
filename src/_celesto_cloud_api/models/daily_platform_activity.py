from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
import datetime


T = TypeVar("T", bound="DailyPlatformActivity")


@_attrs_define
class DailyPlatformActivity:
    """
    Attributes:
        started_at (datetime.datetime):
        ended_at (datetime.datetime):
        active_users (int | None):
        ci_runtime_minutes (float | None):
        sandbox_runtime_minutes (float | None):
        history_complete (bool):
    """

    started_at: datetime.datetime
    ended_at: datetime.datetime
    active_users: int | None
    ci_runtime_minutes: float | None
    sandbox_runtime_minutes: float | None
    history_complete: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        started_at = self.started_at.isoformat()

        ended_at = self.ended_at.isoformat()

        active_users: int | None
        active_users = self.active_users

        ci_runtime_minutes: float | None
        ci_runtime_minutes = self.ci_runtime_minutes

        sandbox_runtime_minutes: float | None
        sandbox_runtime_minutes = self.sandbox_runtime_minutes

        history_complete = self.history_complete

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "started_at": started_at,
                "ended_at": ended_at,
                "active_users": active_users,
                "ci_runtime_minutes": ci_runtime_minutes,
                "sandbox_runtime_minutes": sandbox_runtime_minutes,
                "history_complete": history_complete,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        started_at = datetime.datetime.fromisoformat(d.pop("started_at"))

        ended_at = datetime.datetime.fromisoformat(d.pop("ended_at"))

        def _parse_active_users(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        active_users = _parse_active_users(d.pop("active_users"))

        def _parse_ci_runtime_minutes(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        ci_runtime_minutes = _parse_ci_runtime_minutes(d.pop("ci_runtime_minutes"))

        def _parse_sandbox_runtime_minutes(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        sandbox_runtime_minutes = _parse_sandbox_runtime_minutes(
            d.pop("sandbox_runtime_minutes")
        )

        history_complete = d.pop("history_complete")

        daily_platform_activity = cls(
            started_at=started_at,
            ended_at=ended_at,
            active_users=active_users,
            ci_runtime_minutes=ci_runtime_minutes,
            sandbox_runtime_minutes=sandbox_runtime_minutes,
            history_complete=history_complete,
        )

        daily_platform_activity.additional_properties = d
        return daily_platform_activity

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

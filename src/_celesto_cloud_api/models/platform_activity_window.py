from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.platform_activity_window_days import PlatformActivityWindowDays
from typing import cast


T = TypeVar("T", bound="PlatformActivityWindow")


@_attrs_define
class PlatformActivityWindow:
    """
    Attributes:
        days (PlatformActivityWindowDays):
        new_users (int):
        daily_new_users (float):
        active_users (int):
        active_accounts (int):
        daily_active_users (float | None):
        ci_runtime_minutes (float):
        sandbox_runtime_minutes (float):
        unclassified_runtime_minutes (float):
        daily_ci_runtime_minutes (float | None):
        daily_sandbox_runtime_minutes (float | None):
        sandboxes_created (int):
        total_running_seconds (float):
        history_complete (bool):
    """

    days: PlatformActivityWindowDays
    new_users: int
    daily_new_users: float
    active_users: int
    active_accounts: int
    daily_active_users: float | None
    ci_runtime_minutes: float
    sandbox_runtime_minutes: float
    unclassified_runtime_minutes: float
    daily_ci_runtime_minutes: float | None
    daily_sandbox_runtime_minutes: float | None
    sandboxes_created: int
    total_running_seconds: float
    history_complete: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        days = self.days.value

        new_users = self.new_users

        daily_new_users = self.daily_new_users

        active_users = self.active_users

        active_accounts = self.active_accounts

        daily_active_users: float | None
        daily_active_users = self.daily_active_users

        ci_runtime_minutes = self.ci_runtime_minutes

        sandbox_runtime_minutes = self.sandbox_runtime_minutes

        unclassified_runtime_minutes = self.unclassified_runtime_minutes

        daily_ci_runtime_minutes: float | None
        daily_ci_runtime_minutes = self.daily_ci_runtime_minutes

        daily_sandbox_runtime_minutes: float | None
        daily_sandbox_runtime_minutes = self.daily_sandbox_runtime_minutes

        sandboxes_created = self.sandboxes_created

        total_running_seconds = self.total_running_seconds

        history_complete = self.history_complete

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "days": days,
                "new_users": new_users,
                "daily_new_users": daily_new_users,
                "active_users": active_users,
                "active_accounts": active_accounts,
                "daily_active_users": daily_active_users,
                "ci_runtime_minutes": ci_runtime_minutes,
                "sandbox_runtime_minutes": sandbox_runtime_minutes,
                "unclassified_runtime_minutes": unclassified_runtime_minutes,
                "daily_ci_runtime_minutes": daily_ci_runtime_minutes,
                "daily_sandbox_runtime_minutes": daily_sandbox_runtime_minutes,
                "sandboxes_created": sandboxes_created,
                "total_running_seconds": total_running_seconds,
                "history_complete": history_complete,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        days = PlatformActivityWindowDays(d.pop("days"))

        new_users = d.pop("new_users")

        daily_new_users = d.pop("daily_new_users")

        active_users = d.pop("active_users")

        active_accounts = d.pop("active_accounts")

        def _parse_daily_active_users(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        daily_active_users = _parse_daily_active_users(d.pop("daily_active_users"))

        ci_runtime_minutes = d.pop("ci_runtime_minutes")

        sandbox_runtime_minutes = d.pop("sandbox_runtime_minutes")

        unclassified_runtime_minutes = d.pop("unclassified_runtime_minutes")

        def _parse_daily_ci_runtime_minutes(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        daily_ci_runtime_minutes = _parse_daily_ci_runtime_minutes(
            d.pop("daily_ci_runtime_minutes")
        )

        def _parse_daily_sandbox_runtime_minutes(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        daily_sandbox_runtime_minutes = _parse_daily_sandbox_runtime_minutes(
            d.pop("daily_sandbox_runtime_minutes")
        )

        sandboxes_created = d.pop("sandboxes_created")

        total_running_seconds = d.pop("total_running_seconds")

        history_complete = d.pop("history_complete")

        platform_activity_window = cls(
            days=days,
            new_users=new_users,
            daily_new_users=daily_new_users,
            active_users=active_users,
            active_accounts=active_accounts,
            daily_active_users=daily_active_users,
            ci_runtime_minutes=ci_runtime_minutes,
            sandbox_runtime_minutes=sandbox_runtime_minutes,
            unclassified_runtime_minutes=unclassified_runtime_minutes,
            daily_ci_runtime_minutes=daily_ci_runtime_minutes,
            daily_sandbox_runtime_minutes=daily_sandbox_runtime_minutes,
            sandboxes_created=sandboxes_created,
            total_running_seconds=total_running_seconds,
            history_complete=history_complete,
        )

        platform_activity_window.additional_properties = d
        return platform_activity_window

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

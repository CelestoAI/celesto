from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.daily_platform_activity import DailyPlatformActivity
    from ..models.platform_activity_window import PlatformActivityWindow


T = TypeVar("T", bound="PlatformAnalytics")


@_attrs_define
class PlatformAnalytics:
    """
    Attributes:
        daily_activity (list[DailyPlatformActivity]):
        observed_at (datetime.datetime):
        runtime_coverage_started_at (datetime.datetime | None):
        registered_users (int):
        ci_installed_users (int):
        ci_installed_accounts (int):
        ci_installations (int):
        ci_executing_accounts (int):
        windows (list[PlatformActivityWindow]):
    """

    daily_activity: list[DailyPlatformActivity]
    observed_at: datetime.datetime
    runtime_coverage_started_at: datetime.datetime | None
    registered_users: int
    ci_installed_users: int
    ci_installed_accounts: int
    ci_installations: int
    ci_executing_accounts: int
    windows: list[PlatformActivityWindow]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.daily_platform_activity import DailyPlatformActivity  # noqa: PLC0415
        from ..models.platform_activity_window import PlatformActivityWindow  # noqa: PLC0415

        daily_activity = []
        for daily_activity_item_data in self.daily_activity:
            daily_activity_item = daily_activity_item_data.to_dict()
            daily_activity.append(daily_activity_item)

        observed_at = self.observed_at.isoformat()

        runtime_coverage_started_at: None | str
        if isinstance(self.runtime_coverage_started_at, datetime.datetime):
            runtime_coverage_started_at = self.runtime_coverage_started_at.isoformat()
        else:
            runtime_coverage_started_at = self.runtime_coverage_started_at

        registered_users = self.registered_users

        ci_installed_users = self.ci_installed_users

        ci_installed_accounts = self.ci_installed_accounts

        ci_installations = self.ci_installations

        ci_executing_accounts = self.ci_executing_accounts

        windows = []
        for windows_item_data in self.windows:
            windows_item = windows_item_data.to_dict()
            windows.append(windows_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "daily_activity": daily_activity,
                "observed_at": observed_at,
                "runtime_coverage_started_at": runtime_coverage_started_at,
                "registered_users": registered_users,
                "ci_installed_users": ci_installed_users,
                "ci_installed_accounts": ci_installed_accounts,
                "ci_installations": ci_installations,
                "ci_executing_accounts": ci_executing_accounts,
                "windows": windows,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.daily_platform_activity import DailyPlatformActivity  # noqa: PLC0415
        from ..models.platform_activity_window import PlatformActivityWindow  # noqa: PLC0415

        d = dict(src_dict)
        daily_activity = []
        _daily_activity = d.pop("daily_activity")
        for daily_activity_item_data in _daily_activity:
            daily_activity_item = DailyPlatformActivity.from_dict(
                daily_activity_item_data
            )

            daily_activity.append(daily_activity_item)

        observed_at = datetime.datetime.fromisoformat(d.pop("observed_at"))

        def _parse_runtime_coverage_started_at(
            data: object,
        ) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                runtime_coverage_started_at_type_0 = datetime.datetime.fromisoformat(
                    data
                )

                return runtime_coverage_started_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        runtime_coverage_started_at = _parse_runtime_coverage_started_at(
            d.pop("runtime_coverage_started_at")
        )

        registered_users = d.pop("registered_users")

        ci_installed_users = d.pop("ci_installed_users")

        ci_installed_accounts = d.pop("ci_installed_accounts")

        ci_installations = d.pop("ci_installations")

        ci_executing_accounts = d.pop("ci_executing_accounts")

        windows = []
        _windows = d.pop("windows")
        for windows_item_data in _windows:
            windows_item = PlatformActivityWindow.from_dict(windows_item_data)

            windows.append(windows_item)

        platform_analytics = cls(
            daily_activity=daily_activity,
            observed_at=observed_at,
            runtime_coverage_started_at=runtime_coverage_started_at,
            registered_users=registered_users,
            ci_installed_users=ci_installed_users,
            ci_installed_accounts=ci_installed_accounts,
            ci_installations=ci_installations,
            ci_executing_accounts=ci_executing_accounts,
            windows=windows,
        )

        platform_analytics.additional_properties = d
        return platform_analytics

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.customer_attribution import CustomerAttribution
    from ..models.customer_commands import CustomerCommands
    from ..models.customer_configuration import CustomerConfiguration
    from ..models.customer_organization_analytics_providers import (
        CustomerOrganizationAnalyticsProviders,
    )
    from ..models.customer_organization_analytics_statuses import (
        CustomerOrganizationAnalyticsStatuses,
    )


T = TypeVar("T", bound="CustomerOrganizationAnalytics")


@_attrs_define
class CustomerOrganizationAnalytics:
    """
    Attributes:
        organization_id (str):
        machines_created (int):
        statuses (CustomerOrganizationAnalyticsStatuses):
        first_created_at (datetime.datetime):
        last_created_at (datetime.datetime):
        configurations (list[CustomerConfiguration]):
        providers (CustomerOrganizationAnalyticsProviders):
        peak_concurrent_running (int):
        total_running_seconds (float):
        median_completed_session_seconds (float | None):
        longest_completed_session_seconds (float | None):
        completed_sessions (int):
        open_sessions (int):
        machines_without_runtime (int):
        commands (CustomerCommands):
        attribution (CustomerAttribution):
    """

    organization_id: str
    machines_created: int
    statuses: CustomerOrganizationAnalyticsStatuses
    first_created_at: datetime.datetime
    last_created_at: datetime.datetime
    configurations: list[CustomerConfiguration]
    providers: CustomerOrganizationAnalyticsProviders
    peak_concurrent_running: int
    total_running_seconds: float
    median_completed_session_seconds: float | None
    longest_completed_session_seconds: float | None
    completed_sessions: int
    open_sessions: int
    machines_without_runtime: int
    commands: CustomerCommands
    attribution: CustomerAttribution
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.customer_attribution import CustomerAttribution  # noqa: PLC0415
        from ..models.customer_commands import CustomerCommands  # noqa: PLC0415
        from ..models.customer_configuration import CustomerConfiguration  # noqa: PLC0415
        from ..models.customer_organization_analytics_providers import (
            CustomerOrganizationAnalyticsProviders,
        )  # noqa: PLC0415
        from ..models.customer_organization_analytics_statuses import (
            CustomerOrganizationAnalyticsStatuses,
        )  # noqa: PLC0415

        organization_id = self.organization_id

        machines_created = self.machines_created

        statuses = self.statuses.to_dict()

        first_created_at = self.first_created_at.isoformat()

        last_created_at = self.last_created_at.isoformat()

        configurations = []
        for configurations_item_data in self.configurations:
            configurations_item = configurations_item_data.to_dict()
            configurations.append(configurations_item)

        providers = self.providers.to_dict()

        peak_concurrent_running = self.peak_concurrent_running

        total_running_seconds = self.total_running_seconds

        median_completed_session_seconds: float | None
        median_completed_session_seconds = self.median_completed_session_seconds

        longest_completed_session_seconds: float | None
        longest_completed_session_seconds = self.longest_completed_session_seconds

        completed_sessions = self.completed_sessions

        open_sessions = self.open_sessions

        machines_without_runtime = self.machines_without_runtime

        commands = self.commands.to_dict()

        attribution = self.attribution.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "organization_id": organization_id,
                "machines_created": machines_created,
                "statuses": statuses,
                "first_created_at": first_created_at,
                "last_created_at": last_created_at,
                "configurations": configurations,
                "providers": providers,
                "peak_concurrent_running": peak_concurrent_running,
                "total_running_seconds": total_running_seconds,
                "median_completed_session_seconds": median_completed_session_seconds,
                "longest_completed_session_seconds": longest_completed_session_seconds,
                "completed_sessions": completed_sessions,
                "open_sessions": open_sessions,
                "machines_without_runtime": machines_without_runtime,
                "commands": commands,
                "attribution": attribution,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.customer_attribution import CustomerAttribution  # noqa: PLC0415
        from ..models.customer_commands import CustomerCommands  # noqa: PLC0415
        from ..models.customer_configuration import CustomerConfiguration  # noqa: PLC0415
        from ..models.customer_organization_analytics_providers import (
            CustomerOrganizationAnalyticsProviders,
        )  # noqa: PLC0415
        from ..models.customer_organization_analytics_statuses import (
            CustomerOrganizationAnalyticsStatuses,
        )  # noqa: PLC0415

        d = dict(src_dict)
        organization_id = d.pop("organization_id")

        machines_created = d.pop("machines_created")

        statuses = CustomerOrganizationAnalyticsStatuses.from_dict(d.pop("statuses"))

        first_created_at = datetime.datetime.fromisoformat(d.pop("first_created_at"))

        last_created_at = datetime.datetime.fromisoformat(d.pop("last_created_at"))

        configurations = []
        _configurations = d.pop("configurations")
        for configurations_item_data in _configurations:
            configurations_item = CustomerConfiguration.from_dict(
                configurations_item_data
            )

            configurations.append(configurations_item)

        providers = CustomerOrganizationAnalyticsProviders.from_dict(d.pop("providers"))

        peak_concurrent_running = d.pop("peak_concurrent_running")

        total_running_seconds = d.pop("total_running_seconds")

        def _parse_median_completed_session_seconds(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        median_completed_session_seconds = _parse_median_completed_session_seconds(
            d.pop("median_completed_session_seconds")
        )

        def _parse_longest_completed_session_seconds(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        longest_completed_session_seconds = _parse_longest_completed_session_seconds(
            d.pop("longest_completed_session_seconds")
        )

        completed_sessions = d.pop("completed_sessions")

        open_sessions = d.pop("open_sessions")

        machines_without_runtime = d.pop("machines_without_runtime")

        commands = CustomerCommands.from_dict(d.pop("commands"))

        attribution = CustomerAttribution.from_dict(d.pop("attribution"))

        customer_organization_analytics = cls(
            organization_id=organization_id,
            machines_created=machines_created,
            statuses=statuses,
            first_created_at=first_created_at,
            last_created_at=last_created_at,
            configurations=configurations,
            providers=providers,
            peak_concurrent_running=peak_concurrent_running,
            total_running_seconds=total_running_seconds,
            median_completed_session_seconds=median_completed_session_seconds,
            longest_completed_session_seconds=longest_completed_session_seconds,
            completed_sessions=completed_sessions,
            open_sessions=open_sessions,
            machines_without_runtime=machines_without_runtime,
            commands=commands,
            attribution=attribution,
        )

        customer_organization_analytics.additional_properties = d
        return customer_organization_analytics

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

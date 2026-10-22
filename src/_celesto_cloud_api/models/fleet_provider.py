from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast

if TYPE_CHECKING:
    from ..models.computer_counts import ComputerCounts
    from ..models.fleet_capacity import FleetCapacity


T = TypeVar("T", bound="FleetProvider")


@_attrs_define
class FleetProvider:
    """
    Attributes:
        provider (str):
        host_count (int):
        active_hosts (int):
        draining_hosts (int):
        offline_hosts (int):
        eligible_hosts (int):
        unavailable_hosts (int):
        eligible_available_vcpus (int):
        eligible_available_ram_mb (int):
        disk_reporting_hosts (int):
        computers (ComputerCounts):
        capacity (FleetCapacity):
    """

    provider: str
    host_count: int
    active_hosts: int
    draining_hosts: int
    offline_hosts: int
    eligible_hosts: int
    unavailable_hosts: int
    eligible_available_vcpus: int
    eligible_available_ram_mb: int
    disk_reporting_hosts: int
    computers: ComputerCounts
    capacity: FleetCapacity
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.computer_counts import ComputerCounts  # noqa: PLC0415
        from ..models.fleet_capacity import FleetCapacity  # noqa: PLC0415

        provider = self.provider

        host_count = self.host_count

        active_hosts = self.active_hosts

        draining_hosts = self.draining_hosts

        offline_hosts = self.offline_hosts

        eligible_hosts = self.eligible_hosts

        unavailable_hosts = self.unavailable_hosts

        eligible_available_vcpus = self.eligible_available_vcpus

        eligible_available_ram_mb = self.eligible_available_ram_mb

        disk_reporting_hosts = self.disk_reporting_hosts

        computers = self.computers.to_dict()

        capacity = self.capacity.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "provider": provider,
                "host_count": host_count,
                "active_hosts": active_hosts,
                "draining_hosts": draining_hosts,
                "offline_hosts": offline_hosts,
                "eligible_hosts": eligible_hosts,
                "unavailable_hosts": unavailable_hosts,
                "eligible_available_vcpus": eligible_available_vcpus,
                "eligible_available_ram_mb": eligible_available_ram_mb,
                "disk_reporting_hosts": disk_reporting_hosts,
                "computers": computers,
                "capacity": capacity,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.computer_counts import ComputerCounts  # noqa: PLC0415
        from ..models.fleet_capacity import FleetCapacity  # noqa: PLC0415

        d = dict(src_dict)
        provider = d.pop("provider")

        host_count = d.pop("host_count")

        active_hosts = d.pop("active_hosts")

        draining_hosts = d.pop("draining_hosts")

        offline_hosts = d.pop("offline_hosts")

        eligible_hosts = d.pop("eligible_hosts")

        unavailable_hosts = d.pop("unavailable_hosts")

        eligible_available_vcpus = d.pop("eligible_available_vcpus")

        eligible_available_ram_mb = d.pop("eligible_available_ram_mb")

        disk_reporting_hosts = d.pop("disk_reporting_hosts")

        computers = ComputerCounts.from_dict(d.pop("computers"))

        capacity = FleetCapacity.from_dict(d.pop("capacity"))

        fleet_provider = cls(
            provider=provider,
            host_count=host_count,
            active_hosts=active_hosts,
            draining_hosts=draining_hosts,
            offline_hosts=offline_hosts,
            eligible_hosts=eligible_hosts,
            unavailable_hosts=unavailable_hosts,
            eligible_available_vcpus=eligible_available_vcpus,
            eligible_available_ram_mb=eligible_available_ram_mb,
            disk_reporting_hosts=disk_reporting_hosts,
            computers=computers,
            capacity=capacity,
        )

        fleet_provider.additional_properties = d
        return fleet_provider

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast


T = TypeVar("T", bound="FleetCapacity")


@_attrs_define
class FleetCapacity:
    """
    Attributes:
        total_vcpus (int):
        allocated_vcpus (int):
        available_vcpus (int):
        total_ram_mb (int):
        allocated_ram_mb (int):
        available_ram_mb (int):
        total_disk_mb (int | None):
        reserved_disk_mb (int):
        disk_headroom_mb (int):
        available_disk_mb (int | None):
        reported_free_disk_mb (int | None):
        overcommitted (bool):
    """

    total_vcpus: int
    allocated_vcpus: int
    available_vcpus: int
    total_ram_mb: int
    allocated_ram_mb: int
    available_ram_mb: int
    total_disk_mb: int | None
    reserved_disk_mb: int
    disk_headroom_mb: int
    available_disk_mb: int | None
    reported_free_disk_mb: int | None
    overcommitted: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total_vcpus = self.total_vcpus

        allocated_vcpus = self.allocated_vcpus

        available_vcpus = self.available_vcpus

        total_ram_mb = self.total_ram_mb

        allocated_ram_mb = self.allocated_ram_mb

        available_ram_mb = self.available_ram_mb

        total_disk_mb: int | None
        total_disk_mb = self.total_disk_mb

        reserved_disk_mb = self.reserved_disk_mb

        disk_headroom_mb = self.disk_headroom_mb

        available_disk_mb: int | None
        available_disk_mb = self.available_disk_mb

        reported_free_disk_mb: int | None
        reported_free_disk_mb = self.reported_free_disk_mb

        overcommitted = self.overcommitted

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total_vcpus": total_vcpus,
                "allocated_vcpus": allocated_vcpus,
                "available_vcpus": available_vcpus,
                "total_ram_mb": total_ram_mb,
                "allocated_ram_mb": allocated_ram_mb,
                "available_ram_mb": available_ram_mb,
                "total_disk_mb": total_disk_mb,
                "reserved_disk_mb": reserved_disk_mb,
                "disk_headroom_mb": disk_headroom_mb,
                "available_disk_mb": available_disk_mb,
                "reported_free_disk_mb": reported_free_disk_mb,
                "overcommitted": overcommitted,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        total_vcpus = d.pop("total_vcpus")

        allocated_vcpus = d.pop("allocated_vcpus")

        available_vcpus = d.pop("available_vcpus")

        total_ram_mb = d.pop("total_ram_mb")

        allocated_ram_mb = d.pop("allocated_ram_mb")

        available_ram_mb = d.pop("available_ram_mb")

        def _parse_total_disk_mb(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        total_disk_mb = _parse_total_disk_mb(d.pop("total_disk_mb"))

        reserved_disk_mb = d.pop("reserved_disk_mb")

        disk_headroom_mb = d.pop("disk_headroom_mb")

        def _parse_available_disk_mb(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        available_disk_mb = _parse_available_disk_mb(d.pop("available_disk_mb"))

        def _parse_reported_free_disk_mb(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        reported_free_disk_mb = _parse_reported_free_disk_mb(
            d.pop("reported_free_disk_mb")
        )

        overcommitted = d.pop("overcommitted")

        fleet_capacity = cls(
            total_vcpus=total_vcpus,
            allocated_vcpus=allocated_vcpus,
            available_vcpus=available_vcpus,
            total_ram_mb=total_ram_mb,
            allocated_ram_mb=allocated_ram_mb,
            available_ram_mb=available_ram_mb,
            total_disk_mb=total_disk_mb,
            reserved_disk_mb=reserved_disk_mb,
            disk_headroom_mb=disk_headroom_mb,
            available_disk_mb=available_disk_mb,
            reported_free_disk_mb=reported_free_disk_mb,
            overcommitted=overcommitted,
        )

        fleet_capacity.additional_properties = d
        return fleet_capacity

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

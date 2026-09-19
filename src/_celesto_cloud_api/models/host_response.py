from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="HostResponse")


@_attrs_define
class HostResponse:
    """Response for a host record.

    Attributes:
        id (str):
        address (str):
        total_vcpus (int):
        total_ram_mb (int):
        available_vcpus (int):
        available_ram_mb (int):
        status (str):
        created_at (str):
        agent_version (None | str | Unset):
        last_heartbeat (None | str | Unset):
        disk_used_mb (int | None | Unset):
        disk_total_mb (int | None | Unset):
        disk_percent (float | None | Unset):
    """

    id: str
    address: str
    total_vcpus: int
    total_ram_mb: int
    available_vcpus: int
    available_ram_mb: int
    status: str
    created_at: str
    agent_version: None | str | Unset = UNSET
    last_heartbeat: None | str | Unset = UNSET
    disk_used_mb: int | None | Unset = UNSET
    disk_total_mb: int | None | Unset = UNSET
    disk_percent: float | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        address = self.address

        total_vcpus = self.total_vcpus

        total_ram_mb = self.total_ram_mb

        available_vcpus = self.available_vcpus

        available_ram_mb = self.available_ram_mb

        status = self.status

        created_at = self.created_at

        agent_version: None | str | Unset
        if isinstance(self.agent_version, Unset):
            agent_version = UNSET
        else:
            agent_version = self.agent_version

        last_heartbeat: None | str | Unset
        if isinstance(self.last_heartbeat, Unset):
            last_heartbeat = UNSET
        else:
            last_heartbeat = self.last_heartbeat

        disk_used_mb: int | None | Unset
        if isinstance(self.disk_used_mb, Unset):
            disk_used_mb = UNSET
        else:
            disk_used_mb = self.disk_used_mb

        disk_total_mb: int | None | Unset
        if isinstance(self.disk_total_mb, Unset):
            disk_total_mb = UNSET
        else:
            disk_total_mb = self.disk_total_mb

        disk_percent: float | None | Unset
        if isinstance(self.disk_percent, Unset):
            disk_percent = UNSET
        else:
            disk_percent = self.disk_percent

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "address": address,
                "total_vcpus": total_vcpus,
                "total_ram_mb": total_ram_mb,
                "available_vcpus": available_vcpus,
                "available_ram_mb": available_ram_mb,
                "status": status,
                "created_at": created_at,
            }
        )
        if agent_version is not UNSET:
            field_dict["agent_version"] = agent_version
        if last_heartbeat is not UNSET:
            field_dict["last_heartbeat"] = last_heartbeat
        if disk_used_mb is not UNSET:
            field_dict["disk_used_mb"] = disk_used_mb
        if disk_total_mb is not UNSET:
            field_dict["disk_total_mb"] = disk_total_mb
        if disk_percent is not UNSET:
            field_dict["disk_percent"] = disk_percent

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        address = d.pop("address")

        total_vcpus = d.pop("total_vcpus")

        total_ram_mb = d.pop("total_ram_mb")

        available_vcpus = d.pop("available_vcpus")

        available_ram_mb = d.pop("available_ram_mb")

        status = d.pop("status")

        created_at = d.pop("created_at")

        def _parse_agent_version(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        agent_version = _parse_agent_version(d.pop("agent_version", UNSET))

        def _parse_last_heartbeat(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        last_heartbeat = _parse_last_heartbeat(d.pop("last_heartbeat", UNSET))

        def _parse_disk_used_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        disk_used_mb = _parse_disk_used_mb(d.pop("disk_used_mb", UNSET))

        def _parse_disk_total_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        disk_total_mb = _parse_disk_total_mb(d.pop("disk_total_mb", UNSET))

        def _parse_disk_percent(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        disk_percent = _parse_disk_percent(d.pop("disk_percent", UNSET))

        host_response = cls(
            id=id,
            address=address,
            total_vcpus=total_vcpus,
            total_ram_mb=total_ram_mb,
            available_vcpus=available_vcpus,
            available_ram_mb=available_ram_mb,
            status=status,
            created_at=created_at,
            agent_version=agent_version,
            last_heartbeat=last_heartbeat,
            disk_used_mb=disk_used_mb,
            disk_total_mb=disk_total_mb,
            disk_percent=disk_percent,
        )

        host_response.additional_properties = d
        return host_response

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

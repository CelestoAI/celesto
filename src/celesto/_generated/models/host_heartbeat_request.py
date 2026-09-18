from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.host_heartbeat_request_metadata_type_0 import (
        HostHeartbeatRequestMetadataType0,
    )


T = TypeVar("T", bound="HostHeartbeatRequest")


@_attrs_define
class HostHeartbeatRequest:
    """Heartbeat from a host agent with current utilization.

    Attributes:
        available_vcpus (int):
        available_ram_mb (int):
        running_vms (int):
        agent_version (None | str | Unset):
        boot_id (None | str | Unset):
        disk_used_mb (int | None | Unset):
        disk_total_mb (int | None | Unset):
        disk_percent (float | None | Unset):
        metadata (HostHeartbeatRequestMetadataType0 | None | Unset):
    """

    available_vcpus: int
    available_ram_mb: int
    running_vms: int
    agent_version: None | str | Unset = UNSET
    boot_id: None | str | Unset = UNSET
    disk_used_mb: int | None | Unset = UNSET
    disk_total_mb: int | None | Unset = UNSET
    disk_percent: float | None | Unset = UNSET
    metadata: HostHeartbeatRequestMetadataType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.host_heartbeat_request_metadata_type_0 import (
            HostHeartbeatRequestMetadataType0,
        )  # noqa: PLC0415

        available_vcpus = self.available_vcpus

        available_ram_mb = self.available_ram_mb

        running_vms = self.running_vms

        agent_version: None | str | Unset
        if isinstance(self.agent_version, Unset):
            agent_version = UNSET
        else:
            agent_version = self.agent_version

        boot_id: None | str | Unset
        if isinstance(self.boot_id, Unset):
            boot_id = UNSET
        else:
            boot_id = self.boot_id

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

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, HostHeartbeatRequestMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "available_vcpus": available_vcpus,
                "available_ram_mb": available_ram_mb,
                "running_vms": running_vms,
            }
        )
        if agent_version is not UNSET:
            field_dict["agent_version"] = agent_version
        if boot_id is not UNSET:
            field_dict["boot_id"] = boot_id
        if disk_used_mb is not UNSET:
            field_dict["disk_used_mb"] = disk_used_mb
        if disk_total_mb is not UNSET:
            field_dict["disk_total_mb"] = disk_total_mb
        if disk_percent is not UNSET:
            field_dict["disk_percent"] = disk_percent
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.host_heartbeat_request_metadata_type_0 import (
            HostHeartbeatRequestMetadataType0,
        )  # noqa: PLC0415

        d = dict(src_dict)
        available_vcpus = d.pop("available_vcpus")

        available_ram_mb = d.pop("available_ram_mb")

        running_vms = d.pop("running_vms")

        def _parse_agent_version(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        agent_version = _parse_agent_version(d.pop("agent_version", UNSET))

        def _parse_boot_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        boot_id = _parse_boot_id(d.pop("boot_id", UNSET))

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

        def _parse_metadata(
            data: object,
        ) -> HostHeartbeatRequestMetadataType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = HostHeartbeatRequestMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(HostHeartbeatRequestMetadataType0 | None | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        host_heartbeat_request = cls(
            available_vcpus=available_vcpus,
            available_ram_mb=available_ram_mb,
            running_vms=running_vms,
            agent_version=agent_version,
            boot_id=boot_id,
            disk_used_mb=disk_used_mb,
            disk_total_mb=disk_total_mb,
            disk_percent=disk_percent,
            metadata=metadata,
        )

        host_heartbeat_request.additional_properties = d
        return host_heartbeat_request

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

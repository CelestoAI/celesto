from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.host_register_request_metadata_type_0 import (
        HostRegisterRequestMetadataType0,
    )


T = TypeVar("T", bound="HostRegisterRequest")


@_attrs_define
class HostRegisterRequest:
    """Request from a host agent to register itself.

    Attributes:
        address (str):
        total_vcpus (int):
        total_ram_mb (int):
        agent_version (None | str | Unset):
        boot_id (None | str | Unset):
        metadata (HostRegisterRequestMetadataType0 | None | Unset):
    """

    address: str
    total_vcpus: int
    total_ram_mb: int
    agent_version: None | str | Unset = UNSET
    boot_id: None | str | Unset = UNSET
    metadata: HostRegisterRequestMetadataType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.host_register_request_metadata_type_0 import (
            HostRegisterRequestMetadataType0,
        )  # noqa: PLC0415

        address = self.address

        total_vcpus = self.total_vcpus

        total_ram_mb = self.total_ram_mb

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

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, HostRegisterRequestMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "address": address,
                "total_vcpus": total_vcpus,
                "total_ram_mb": total_ram_mb,
            }
        )
        if agent_version is not UNSET:
            field_dict["agent_version"] = agent_version
        if boot_id is not UNSET:
            field_dict["boot_id"] = boot_id
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.host_register_request_metadata_type_0 import (
            HostRegisterRequestMetadataType0,
        )  # noqa: PLC0415

        d = dict(src_dict)
        address = d.pop("address")

        total_vcpus = d.pop("total_vcpus")

        total_ram_mb = d.pop("total_ram_mb")

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

        def _parse_metadata(
            data: object,
        ) -> HostRegisterRequestMetadataType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = HostRegisterRequestMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(HostRegisterRequestMetadataType0 | None | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        host_register_request = cls(
            address=address,
            total_vcpus=total_vcpus,
            total_ram_mb=total_ram_mb,
            agent_version=agent_version,
            boot_id=boot_id,
            metadata=metadata,
        )

        host_register_request.additional_properties = d
        return host_register_request

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

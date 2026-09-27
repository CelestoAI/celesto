from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset


T = TypeVar("T", bound="SandboxSizeResponse")


@_attrs_define
class SandboxSizeResponse:
    """A fixed sandbox shape with its hourly price.

    Attributes:
        id (str):
        vcpus (int):
        ram_mb (int):
        root_disk_mb (int):
        hourly_rate_usd (str):
    """

    id: str
    vcpus: int
    ram_mb: int
    root_disk_mb: int
    hourly_rate_usd: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        vcpus = self.vcpus

        ram_mb = self.ram_mb

        root_disk_mb = self.root_disk_mb

        hourly_rate_usd = self.hourly_rate_usd

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "vcpus": vcpus,
                "ram_mb": ram_mb,
                "root_disk_mb": root_disk_mb,
                "hourly_rate_usd": hourly_rate_usd,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        vcpus = d.pop("vcpus")

        ram_mb = d.pop("ram_mb")

        root_disk_mb = d.pop("root_disk_mb")

        hourly_rate_usd = d.pop("hourly_rate_usd")

        sandbox_size_response = cls(
            id=id,
            vcpus=vcpus,
            ram_mb=ram_mb,
            root_disk_mb=root_disk_mb,
            hourly_rate_usd=hourly_rate_usd,
        )

        sandbox_size_response.additional_properties = d
        return sandbox_size_response

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

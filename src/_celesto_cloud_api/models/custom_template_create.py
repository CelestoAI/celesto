from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="CustomTemplateCreate")


@_attrs_define
class CustomTemplateCreate:
    """Create a template from a built-in base and a build script.

    Without a default size the base template's defaults are used.

        Attributes:
            name (str):
            build_script (str):
            default_vcpus (int | None | Unset):
            default_ram_mb (int | None | Unset):
            default_disk_size_mb (int | None | Unset):
            base_template_id (str | Unset):  Default: 'coding-agent'.
    """

    name: str
    build_script: str
    default_vcpus: int | None | Unset = UNSET
    default_ram_mb: int | None | Unset = UNSET
    default_disk_size_mb: int | None | Unset = UNSET
    base_template_id: str | Unset = "coding-agent"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        build_script = self.build_script

        default_vcpus: int | None | Unset
        if isinstance(self.default_vcpus, Unset):
            default_vcpus = UNSET
        else:
            default_vcpus = self.default_vcpus

        default_ram_mb: int | None | Unset
        if isinstance(self.default_ram_mb, Unset):
            default_ram_mb = UNSET
        else:
            default_ram_mb = self.default_ram_mb

        default_disk_size_mb: int | None | Unset
        if isinstance(self.default_disk_size_mb, Unset):
            default_disk_size_mb = UNSET
        else:
            default_disk_size_mb = self.default_disk_size_mb

        base_template_id = self.base_template_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "build_script": build_script,
            }
        )
        if default_vcpus is not UNSET:
            field_dict["default_vcpus"] = default_vcpus
        if default_ram_mb is not UNSET:
            field_dict["default_ram_mb"] = default_ram_mb
        if default_disk_size_mb is not UNSET:
            field_dict["default_disk_size_mb"] = default_disk_size_mb
        if base_template_id is not UNSET:
            field_dict["base_template_id"] = base_template_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        build_script = d.pop("build_script")

        def _parse_default_vcpus(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        default_vcpus = _parse_default_vcpus(d.pop("default_vcpus", UNSET))

        def _parse_default_ram_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        default_ram_mb = _parse_default_ram_mb(d.pop("default_ram_mb", UNSET))

        def _parse_default_disk_size_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        default_disk_size_mb = _parse_default_disk_size_mb(
            d.pop("default_disk_size_mb", UNSET)
        )

        base_template_id = d.pop("base_template_id", UNSET)

        custom_template_create = cls(
            name=name,
            build_script=build_script,
            default_vcpus=default_vcpus,
            default_ram_mb=default_ram_mb,
            default_disk_size_mb=default_disk_size_mb,
            base_template_id=base_template_id,
        )

        custom_template_create.additional_properties = d
        return custom_template_create

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

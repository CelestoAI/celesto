from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="CustomTemplateUpdate")


@_attrs_define
class CustomTemplateUpdate:
    """Edit a template's name, script or default size. A script change takes effect on the next rebuild.

    Attributes:
        default_vcpus (int | None | Unset):
        default_ram_mb (int | None | Unset):
        default_disk_size_mb (int | None | Unset):
        name (None | str | Unset):
        build_script (None | str | Unset):
    """

    default_vcpus: int | None | Unset = UNSET
    default_ram_mb: int | None | Unset = UNSET
    default_disk_size_mb: int | None | Unset = UNSET
    name: None | str | Unset = UNSET
    build_script: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
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

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        build_script: None | str | Unset
        if isinstance(self.build_script, Unset):
            build_script = UNSET
        else:
            build_script = self.build_script

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if default_vcpus is not UNSET:
            field_dict["default_vcpus"] = default_vcpus
        if default_ram_mb is not UNSET:
            field_dict["default_ram_mb"] = default_ram_mb
        if default_disk_size_mb is not UNSET:
            field_dict["default_disk_size_mb"] = default_disk_size_mb
        if name is not UNSET:
            field_dict["name"] = name
        if build_script is not UNSET:
            field_dict["build_script"] = build_script

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

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

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_build_script(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        build_script = _parse_build_script(d.pop("build_script", UNSET))

        custom_template_update = cls(
            default_vcpus=default_vcpus,
            default_ram_mb=default_ram_mb,
            default_disk_size_mb=default_disk_size_mb,
            name=name,
            build_script=build_script,
        )

        custom_template_update.additional_properties = d
        return custom_template_update

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

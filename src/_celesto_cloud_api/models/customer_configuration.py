from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast


T = TypeVar("T", bound="CustomerConfiguration")


@_attrs_define
class CustomerConfiguration:
    """
    Attributes:
        size_id (None | str):
        vcpus (int):
        ram_mb (int):
        template_id (str):
        count (int):
    """

    size_id: None | str
    vcpus: int
    ram_mb: int
    template_id: str
    count: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        size_id: None | str
        size_id = self.size_id

        vcpus = self.vcpus

        ram_mb = self.ram_mb

        template_id = self.template_id

        count = self.count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "size_id": size_id,
                "vcpus": vcpus,
                "ram_mb": ram_mb,
                "template_id": template_id,
                "count": count,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_size_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        size_id = _parse_size_id(d.pop("size_id"))

        vcpus = d.pop("vcpus")

        ram_mb = d.pop("ram_mb")

        template_id = d.pop("template_id")

        count = d.pop("count")

        customer_configuration = cls(
            size_id=size_id,
            vcpus=vcpus,
            ram_mb=ram_mb,
            template_id=template_id,
            count=count,
        )

        customer_configuration.additional_properties = d
        return customer_configuration

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

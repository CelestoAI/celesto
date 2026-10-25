from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
import datetime


T = TypeVar("T", bound="CustomerMachine")


@_attrs_define
class CustomerMachine:
    """
    Attributes:
        id (str):
        name (str):
        status (str):
        provider (str):
        origin (None | str):
        size_id (None | str):
        vcpus (int):
        ram_mb (int):
        disk_size_mb (int):
        template_id (str):
        image (str):
        created_at (datetime.datetime):
        deleted_at (datetime.datetime | None):
    """

    id: str
    name: str
    status: str
    provider: str
    origin: None | str
    size_id: None | str
    vcpus: int
    ram_mb: int
    disk_size_mb: int
    template_id: str
    image: str
    created_at: datetime.datetime
    deleted_at: datetime.datetime | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        status = self.status

        provider = self.provider

        origin: None | str
        origin = self.origin

        size_id: None | str
        size_id = self.size_id

        vcpus = self.vcpus

        ram_mb = self.ram_mb

        disk_size_mb = self.disk_size_mb

        template_id = self.template_id

        image = self.image

        created_at = self.created_at.isoformat()

        deleted_at: None | str
        if isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "status": status,
                "provider": provider,
                "origin": origin,
                "size_id": size_id,
                "vcpus": vcpus,
                "ram_mb": ram_mb,
                "disk_size_mb": disk_size_mb,
                "template_id": template_id,
                "image": image,
                "created_at": created_at,
                "deleted_at": deleted_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        status = d.pop("status")

        provider = d.pop("provider")

        def _parse_origin(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        origin = _parse_origin(d.pop("origin"))

        def _parse_size_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        size_id = _parse_size_id(d.pop("size_id"))

        vcpus = d.pop("vcpus")

        ram_mb = d.pop("ram_mb")

        disk_size_mb = d.pop("disk_size_mb")

        template_id = d.pop("template_id")

        image = d.pop("image")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        def _parse_deleted_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = datetime.datetime.fromisoformat(data)

                return deleted_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at"))

        customer_machine = cls(
            id=id,
            name=name,
            status=status,
            provider=provider,
            origin=origin,
            size_id=size_id,
            vcpus=vcpus,
            ram_mb=ram_mb,
            disk_size_mb=disk_size_mb,
            template_id=template_id,
            image=image,
            created_at=created_at,
            deleted_at=deleted_at,
        )

        customer_machine.additional_properties = d
        return customer_machine

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

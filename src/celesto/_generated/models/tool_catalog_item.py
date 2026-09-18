from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.tool_catalog_item_metadata_type_0 import ToolCatalogItemMetadataType0


T = TypeVar("T", bound="ToolCatalogItem")


@_attrs_define
class ToolCatalogItem:
    """
    Attributes:
        id (str):
        tool_key (str):
        name (str):
        auth_types (list[str]):
        is_active (bool):
        description (None | str | Unset):
        metadata (None | ToolCatalogItemMetadataType0 | Unset):
    """

    id: str
    tool_key: str
    name: str
    auth_types: list[str]
    is_active: bool
    description: None | str | Unset = UNSET
    metadata: None | ToolCatalogItemMetadataType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.tool_catalog_item_metadata_type_0 import (
            ToolCatalogItemMetadataType0,
        )  # noqa: PLC0415

        id = self.id

        tool_key = self.tool_key

        name = self.name

        auth_types = self.auth_types

        is_active = self.is_active

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, ToolCatalogItemMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "tool_key": tool_key,
                "name": name,
                "auth_types": auth_types,
                "is_active": is_active,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.tool_catalog_item_metadata_type_0 import (
            ToolCatalogItemMetadataType0,
        )  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        tool_key = d.pop("tool_key")

        name = d.pop("name")

        auth_types = cast(list[str], d.pop("auth_types"))

        is_active = d.pop("is_active")

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_metadata(
            data: object,
        ) -> None | ToolCatalogItemMetadataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = ToolCatalogItemMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ToolCatalogItemMetadataType0 | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        tool_catalog_item = cls(
            id=id,
            tool_key=tool_key,
            name=name,
            auth_types=auth_types,
            is_active=is_active,
            description=description,
            metadata=metadata,
        )

        tool_catalog_item.additional_properties = d
        return tool_catalog_item

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

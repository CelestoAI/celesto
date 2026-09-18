from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="SecretUpdateRequest")


@_attrs_define
class SecretUpdateRequest:
    """Request schema for updating an existing secret

    Attributes:
        name (None | str | Unset): Human-friendly display name
        key_value (None | str | Unset): New secret value (max 1KB)
        description (None | str | Unset): Secret description
        encrypt (bool | None | Unset): Whether to encrypt the secret value (if updating key_value)
        tags (list[str] | None | Unset): Tags for organization (max 20 tags)
    """

    name: None | str | Unset = UNSET
    key_value: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    encrypt: bool | None | Unset = UNSET
    tags: list[str] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        key_value: None | str | Unset
        if isinstance(self.key_value, Unset):
            key_value = UNSET
        else:
            key_value = self.key_value

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        encrypt: bool | None | Unset
        if isinstance(self.encrypt, Unset):
            encrypt = UNSET
        else:
            encrypt = self.encrypt

        tags: list[str] | None | Unset
        if isinstance(self.tags, Unset):
            tags = UNSET
        elif isinstance(self.tags, list):
            tags = self.tags

        else:
            tags = self.tags

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if key_value is not UNSET:
            field_dict["key_value"] = key_value
        if description is not UNSET:
            field_dict["description"] = description
        if encrypt is not UNSET:
            field_dict["encrypt"] = encrypt
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_key_value(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        key_value = _parse_key_value(d.pop("key_value", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_encrypt(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        encrypt = _parse_encrypt(d.pop("encrypt", UNSET))

        def _parse_tags(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tags_type_0 = cast(list[str], data)

                return tags_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        tags = _parse_tags(d.pop("tags", UNSET))

        secret_update_request = cls(
            name=name,
            key_value=key_value,
            description=description,
            encrypt=encrypt,
            tags=tags,
        )

        secret_update_request.additional_properties = d
        return secret_update_request

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

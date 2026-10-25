from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
import datetime


T = TypeVar("T", bound="ApiKeyCreated")


@_attrs_define
class ApiKeyCreated:
    """
    Attributes:
        id (str):
        name (str):
        key_prefix (None | str):
        scopes (list[str] | None):
        created_at (datetime.datetime):
        last_used_at (datetime.datetime | None):
        expires_at (datetime.datetime | None):
        is_active (bool):
        key (str):
    """

    id: str
    name: str
    key_prefix: None | str
    scopes: list[str] | None
    created_at: datetime.datetime
    last_used_at: datetime.datetime | None
    expires_at: datetime.datetime | None
    is_active: bool
    key: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        key_prefix: None | str
        key_prefix = self.key_prefix

        scopes: list[str] | None
        if isinstance(self.scopes, list):
            scopes = self.scopes

        else:
            scopes = self.scopes

        created_at = self.created_at.isoformat()

        last_used_at: None | str
        if isinstance(self.last_used_at, datetime.datetime):
            last_used_at = self.last_used_at.isoformat()
        else:
            last_used_at = self.last_used_at

        expires_at: None | str
        if isinstance(self.expires_at, datetime.datetime):
            expires_at = self.expires_at.isoformat()
        else:
            expires_at = self.expires_at

        is_active = self.is_active

        key = self.key

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "key_prefix": key_prefix,
                "scopes": scopes,
                "created_at": created_at,
                "last_used_at": last_used_at,
                "expires_at": expires_at,
                "is_active": is_active,
                "key": key,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        def _parse_key_prefix(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        key_prefix = _parse_key_prefix(d.pop("key_prefix"))

        def _parse_scopes(data: object) -> list[str] | None:
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                scopes_type_0 = cast(list[str], data)

                return scopes_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None, data)

        scopes = _parse_scopes(d.pop("scopes"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        def _parse_last_used_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_used_at_type_0 = datetime.datetime.fromisoformat(data)

                return last_used_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        last_used_at = _parse_last_used_at(d.pop("last_used_at"))

        def _parse_expires_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                expires_at_type_0 = datetime.datetime.fromisoformat(data)

                return expires_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        expires_at = _parse_expires_at(d.pop("expires_at"))

        is_active = d.pop("is_active")

        key = d.pop("key")

        api_key_created = cls(
            id=id,
            name=name,
            key_prefix=key_prefix,
            scopes=scopes,
            created_at=created_at,
            last_used_at=last_used_at,
            expires_at=expires_at,
            is_active=is_active,
            key=key,
        )

        api_key_created.additional_properties = d
        return api_key_created

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

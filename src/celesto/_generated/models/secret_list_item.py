from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.secret_scope_type import SecretScopeType
from ..types import UNSET, Unset
from typing import cast
import datetime


T = TypeVar("T", bound="SecretListItem")


@_attrs_define
class SecretListItem:
    """Simplified secret response for list endpoints

    Attributes:
        id (str):
        key_name (str):
        name (str):
        scope_type (SecretScopeType): Scope of secret access - organization or project
        created_at (datetime.datetime):
        key_value (str):
        is_encrypted (bool):
        organization_id (None | str | Unset):
        project_id (None | str | Unset):
        last_used_at (datetime.datetime | None | Unset):
    """

    id: str
    key_name: str
    name: str
    scope_type: SecretScopeType
    created_at: datetime.datetime
    key_value: str
    is_encrypted: bool
    organization_id: None | str | Unset = UNSET
    project_id: None | str | Unset = UNSET
    last_used_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        key_name = self.key_name

        name = self.name

        scope_type = self.scope_type.value

        created_at = self.created_at.isoformat()

        key_value = self.key_value

        is_encrypted = self.is_encrypted

        organization_id: None | str | Unset
        if isinstance(self.organization_id, Unset):
            organization_id = UNSET
        else:
            organization_id = self.organization_id

        project_id: None | str | Unset
        if isinstance(self.project_id, Unset):
            project_id = UNSET
        else:
            project_id = self.project_id

        last_used_at: None | str | Unset
        if isinstance(self.last_used_at, Unset):
            last_used_at = UNSET
        elif isinstance(self.last_used_at, datetime.datetime):
            last_used_at = self.last_used_at.isoformat()
        else:
            last_used_at = self.last_used_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "key_name": key_name,
                "name": name,
                "scope_type": scope_type,
                "created_at": created_at,
                "key_value": key_value,
                "is_encrypted": is_encrypted,
            }
        )
        if organization_id is not UNSET:
            field_dict["organization_id"] = organization_id
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if last_used_at is not UNSET:
            field_dict["last_used_at"] = last_used_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        key_name = d.pop("key_name")

        name = d.pop("name")

        scope_type = SecretScopeType(d.pop("scope_type"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        key_value = d.pop("key_value")

        is_encrypted = d.pop("is_encrypted")

        def _parse_organization_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        organization_id = _parse_organization_id(d.pop("organization_id", UNSET))

        def _parse_project_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        project_id = _parse_project_id(d.pop("project_id", UNSET))

        def _parse_last_used_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_used_at_type_0 = datetime.datetime.fromisoformat(data)

                return last_used_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        last_used_at = _parse_last_used_at(d.pop("last_used_at", UNSET))

        secret_list_item = cls(
            id=id,
            key_name=key_name,
            name=name,
            scope_type=scope_type,
            created_at=created_at,
            key_value=key_value,
            is_encrypted=is_encrypted,
            organization_id=organization_id,
            project_id=project_id,
            last_used_at=last_used_at,
        )

        secret_list_item.additional_properties = d
        return secret_list_item

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

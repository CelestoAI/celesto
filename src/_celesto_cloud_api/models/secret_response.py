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


T = TypeVar("T", bound="SecretResponse")


@_attrs_define
class SecretResponse:
    """Response schema for secret (with masked value)

    Attributes:
        id (str):
        key_name (str):
        name (str):
        scope_type (SecretScopeType): Scope of secret access - organization or project
        created_at (datetime.datetime):
        key_value (str):
        is_encrypted (bool):
        created_by (str):
        updated_at (datetime.datetime):
        organization_id (None | str | Unset):
        project_id (None | str | Unset):
        last_used_at (datetime.datetime | None | Unset):
        description (None | str | Unset):
        user_id (None | str | Unset):
        updated_by (None | str | Unset):
        tags (list[str] | None | Unset):
    """

    id: str
    key_name: str
    name: str
    scope_type: SecretScopeType
    created_at: datetime.datetime
    key_value: str
    is_encrypted: bool
    created_by: str
    updated_at: datetime.datetime
    organization_id: None | str | Unset = UNSET
    project_id: None | str | Unset = UNSET
    last_used_at: datetime.datetime | None | Unset = UNSET
    description: None | str | Unset = UNSET
    user_id: None | str | Unset = UNSET
    updated_by: None | str | Unset = UNSET
    tags: list[str] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        key_name = self.key_name

        name = self.name

        scope_type = self.scope_type.value

        created_at = self.created_at.isoformat()

        key_value = self.key_value

        is_encrypted = self.is_encrypted

        created_by = self.created_by

        updated_at = self.updated_at.isoformat()

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

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        user_id: None | str | Unset
        if isinstance(self.user_id, Unset):
            user_id = UNSET
        else:
            user_id = self.user_id

        updated_by: None | str | Unset
        if isinstance(self.updated_by, Unset):
            updated_by = UNSET
        else:
            updated_by = self.updated_by

        tags: list[str] | None | Unset
        if isinstance(self.tags, Unset):
            tags = UNSET
        elif isinstance(self.tags, list):
            tags = self.tags

        else:
            tags = self.tags

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
                "created_by": created_by,
                "updated_at": updated_at,
            }
        )
        if organization_id is not UNSET:
            field_dict["organization_id"] = organization_id
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if last_used_at is not UNSET:
            field_dict["last_used_at"] = last_used_at
        if description is not UNSET:
            field_dict["description"] = description
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if updated_by is not UNSET:
            field_dict["updated_by"] = updated_by
        if tags is not UNSET:
            field_dict["tags"] = tags

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

        created_by = d.pop("created_by")

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

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

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_user_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        user_id = _parse_user_id(d.pop("user_id", UNSET))

        def _parse_updated_by(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        updated_by = _parse_updated_by(d.pop("updated_by", UNSET))

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

        secret_response = cls(
            id=id,
            key_name=key_name,
            name=name,
            scope_type=scope_type,
            created_at=created_at,
            key_value=key_value,
            is_encrypted=is_encrypted,
            created_by=created_by,
            updated_at=updated_at,
            organization_id=organization_id,
            project_id=project_id,
            last_used_at=last_used_at,
            description=description,
            user_id=user_id,
            updated_by=updated_by,
            tags=tags,
        )

        secret_response.additional_properties = d
        return secret_response

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

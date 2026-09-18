from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.secret_scope_type import SecretScopeType
from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="SecretCreateRequest")


@_attrs_define
class SecretCreateRequest:
    """Request schema for creating a new secret

    Attributes:
        key_name (str): Environment variable name (e.g., OPENAI_API_KEY)
        name (str): Human-friendly display name
        key_value (str): The actual secret value (max 1KB)
        scope_type (SecretScopeType): Scope of secret access - organization or project
        description (None | str | Unset): Optional description of the secret
        encrypt (bool | Unset): Whether to encrypt the secret value Default: False.
        organization_id (None | str | Unset): Required for organization or project scope
        project_id (None | str | Unset): Required if scope_type is 'project'
        tags (list[str] | None | Unset): Optional tags for organization (max 20 tags)
    """

    key_name: str
    name: str
    key_value: str
    scope_type: SecretScopeType
    description: None | str | Unset = UNSET
    encrypt: bool | Unset = False
    organization_id: None | str | Unset = UNSET
    project_id: None | str | Unset = UNSET
    tags: list[str] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        key_name = self.key_name

        name = self.name

        key_value = self.key_value

        scope_type = self.scope_type.value

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        encrypt = self.encrypt

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
                "key_name": key_name,
                "name": name,
                "key_value": key_value,
                "scope_type": scope_type,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if encrypt is not UNSET:
            field_dict["encrypt"] = encrypt
        if organization_id is not UNSET:
            field_dict["organization_id"] = organization_id
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        key_name = d.pop("key_name")

        name = d.pop("name")

        key_value = d.pop("key_value")

        scope_type = SecretScopeType(d.pop("scope_type"))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        encrypt = d.pop("encrypt", UNSET)

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

        secret_create_request = cls(
            key_name=key_name,
            name=name,
            key_value=key_value,
            scope_type=scope_type,
            description=description,
            encrypt=encrypt,
            organization_id=organization_id,
            project_id=project_id,
            tags=tags,
        )

        secret_create_request.additional_properties = d
        return secret_create_request

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

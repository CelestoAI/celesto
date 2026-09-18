from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.project_response_settings_type_0 import ProjectResponseSettingsType0


T = TypeVar("T", bound="ProjectResponse")


@_attrs_define
class ProjectResponse:
    """Schema for Project response

    Attributes:
        name (str): Project display name
        id (str): Project ID
        organization_id (str): Organization this project belongs to
        slug (str): URL-friendly identifier
        is_default (bool): Whether this is the default project
        created_by (str): User who created this project
        created_at (datetime.datetime): When the project was created
        updated_at (datetime.datetime): When the project was last updated
        description (None | str | Unset): Project description
        settings (None | ProjectResponseSettingsType0 | Unset): Project-specific settings
    """

    name: str
    id: str
    organization_id: str
    slug: str
    is_default: bool
    created_by: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    description: None | str | Unset = UNSET
    settings: None | ProjectResponseSettingsType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.project_response_settings_type_0 import (
            ProjectResponseSettingsType0,
        )  # noqa: PLC0415

        name = self.name

        id = self.id

        organization_id = self.organization_id

        slug = self.slug

        is_default = self.is_default

        created_by = self.created_by

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        settings: dict[str, Any] | None | Unset
        if isinstance(self.settings, Unset):
            settings = UNSET
        elif isinstance(self.settings, ProjectResponseSettingsType0):
            settings = self.settings.to_dict()
        else:
            settings = self.settings

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "id": id,
                "organization_id": organization_id,
                "slug": slug,
                "is_default": is_default,
                "created_by": created_by,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if settings is not UNSET:
            field_dict["settings"] = settings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.project_response_settings_type_0 import (
            ProjectResponseSettingsType0,
        )  # noqa: PLC0415

        d = dict(src_dict)
        name = d.pop("name")

        id = d.pop("id")

        organization_id = d.pop("organization_id")

        slug = d.pop("slug")

        is_default = d.pop("is_default")

        created_by = d.pop("created_by")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_settings(
            data: object,
        ) -> None | ProjectResponseSettingsType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                settings_type_0 = ProjectResponseSettingsType0.from_dict(data)

                return settings_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ProjectResponseSettingsType0 | Unset, data)

        settings = _parse_settings(d.pop("settings", UNSET))

        project_response = cls(
            name=name,
            id=id,
            organization_id=organization_id,
            slug=slug,
            is_default=is_default,
            created_by=created_by,
            created_at=created_at,
            updated_at=updated_at,
            description=description,
            settings=settings,
        )

        project_response.additional_properties = d
        return project_response

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

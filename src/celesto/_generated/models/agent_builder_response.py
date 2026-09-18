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
    from ..models.agent_builder_response_config_data import (
        AgentBuilderResponseConfigData,
    )


T = TypeVar("T", bound="AgentBuilderResponse")


@_attrs_define
class AgentBuilderResponse:
    """Response schema for a single agent config

    Attributes:
        id (str):
        name (str):
        config_data (AgentBuilderResponseConfigData):
        organization_id (str):
        project_id (str):
        created_by (str):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        description (None | str | Unset):
        user_id (None | str | Unset):
    """

    id: str
    name: str
    config_data: AgentBuilderResponseConfigData
    organization_id: str
    project_id: str
    created_by: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    description: None | str | Unset = UNSET
    user_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.agent_builder_response_config_data import (
            AgentBuilderResponseConfigData,
        )  # noqa: PLC0415

        id = self.id

        name = self.name

        config_data = self.config_data.to_dict()

        organization_id = self.organization_id

        project_id = self.project_id

        created_by = self.created_by

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

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

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "config_data": config_data,
                "organization_id": organization_id,
                "project_id": project_id,
                "created_by": created_by,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if user_id is not UNSET:
            field_dict["user_id"] = user_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_builder_response_config_data import (
            AgentBuilderResponseConfigData,
        )  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        config_data = AgentBuilderResponseConfigData.from_dict(d.pop("config_data"))

        organization_id = d.pop("organization_id")

        project_id = d.pop("project_id")

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

        def _parse_user_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        user_id = _parse_user_id(d.pop("user_id", UNSET))

        agent_builder_response = cls(
            id=id,
            name=name,
            config_data=config_data,
            organization_id=organization_id,
            project_id=project_id,
            created_by=created_by,
            created_at=created_at,
            updated_at=updated_at,
            description=description,
            user_id=user_id,
        )

        agent_builder_response.additional_properties = d
        return agent_builder_response

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

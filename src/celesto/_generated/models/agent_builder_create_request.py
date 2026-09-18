from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.agent_builder_create_request_config_data import (
        AgentBuilderCreateRequestConfigData,
    )


T = TypeVar("T", bound="AgentBuilderCreateRequest")


@_attrs_define
class AgentBuilderCreateRequest:
    """Request schema for creating a new agent builder

    Attributes:
        name (str): Unique name for the config within an organization
        organization_id (str): Owning organization ID
        project_id (str): Project ID this agent belongs to
        description (None | str | Unset): Optional description
        config_data (AgentBuilderCreateRequestConfigData | Unset): Agent configuration as nested JSON
    """

    name: str
    organization_id: str
    project_id: str
    description: None | str | Unset = UNSET
    config_data: AgentBuilderCreateRequestConfigData | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.agent_builder_create_request_config_data import (
            AgentBuilderCreateRequestConfigData,
        )  # noqa: PLC0415

        name = self.name

        organization_id = self.organization_id

        project_id = self.project_id

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        config_data: dict[str, Any] | Unset = UNSET
        if not isinstance(self.config_data, Unset):
            config_data = self.config_data.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "organization_id": organization_id,
                "project_id": project_id,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if config_data is not UNSET:
            field_dict["config_data"] = config_data

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_builder_create_request_config_data import (
            AgentBuilderCreateRequestConfigData,
        )  # noqa: PLC0415

        d = dict(src_dict)
        name = d.pop("name")

        organization_id = d.pop("organization_id")

        project_id = d.pop("project_id")

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        _config_data = d.pop("config_data", UNSET)
        config_data: AgentBuilderCreateRequestConfigData | Unset
        if isinstance(_config_data, Unset):
            config_data = UNSET
        else:
            config_data = AgentBuilderCreateRequestConfigData.from_dict(_config_data)

        agent_builder_create_request = cls(
            name=name,
            organization_id=organization_id,
            project_id=project_id,
            description=description,
            config_data=config_data,
        )

        agent_builder_create_request.additional_properties = d
        return agent_builder_create_request

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

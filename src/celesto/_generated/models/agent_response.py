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
    from ..models.agent_response_config_type_0 import AgentResponseConfigType0


T = TypeVar("T", bound="AgentResponse")


@_attrs_define
class AgentResponse:
    """
    Attributes:
        id (str):
        name (str):
        model (str):
        version (int):
        current_version_id (str):
        project_id (str):
        organization_id (str):
        status (str):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        object_ (str | Unset):  Default: 'agent'.
        description (None | str | Unset):
        instructions (None | str | Unset):
        config (AgentResponseConfigType0 | None | Unset):
        tools (list[str] | None | Unset):
        mcp_servers (list[str] | None | Unset):
    """

    id: str
    name: str
    model: str
    version: int
    current_version_id: str
    project_id: str
    organization_id: str
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    object_: str | Unset = "agent"
    description: None | str | Unset = UNSET
    instructions: None | str | Unset = UNSET
    config: AgentResponseConfigType0 | None | Unset = UNSET
    tools: list[str] | None | Unset = UNSET
    mcp_servers: list[str] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.agent_response_config_type_0 import AgentResponseConfigType0  # noqa: PLC0415

        id = self.id

        name = self.name

        model = self.model

        version = self.version

        current_version_id = self.current_version_id

        project_id = self.project_id

        organization_id = self.organization_id

        status = self.status

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        object_ = self.object_

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        instructions: None | str | Unset
        if isinstance(self.instructions, Unset):
            instructions = UNSET
        else:
            instructions = self.instructions

        config: dict[str, Any] | None | Unset
        if isinstance(self.config, Unset):
            config = UNSET
        elif isinstance(self.config, AgentResponseConfigType0):
            config = self.config.to_dict()
        else:
            config = self.config

        tools: list[str] | None | Unset
        if isinstance(self.tools, Unset):
            tools = UNSET
        elif isinstance(self.tools, list):
            tools = self.tools

        else:
            tools = self.tools

        mcp_servers: list[str] | None | Unset
        if isinstance(self.mcp_servers, Unset):
            mcp_servers = UNSET
        elif isinstance(self.mcp_servers, list):
            mcp_servers = self.mcp_servers

        else:
            mcp_servers = self.mcp_servers

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "model": model,
                "version": version,
                "current_version_id": current_version_id,
                "project_id": project_id,
                "organization_id": organization_id,
                "status": status,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if object_ is not UNSET:
            field_dict["object"] = object_
        if description is not UNSET:
            field_dict["description"] = description
        if instructions is not UNSET:
            field_dict["instructions"] = instructions
        if config is not UNSET:
            field_dict["config"] = config
        if tools is not UNSET:
            field_dict["tools"] = tools
        if mcp_servers is not UNSET:
            field_dict["mcp_servers"] = mcp_servers

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_response_config_type_0 import AgentResponseConfigType0  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        model = d.pop("model")

        version = d.pop("version")

        current_version_id = d.pop("current_version_id")

        project_id = d.pop("project_id")

        organization_id = d.pop("organization_id")

        status = d.pop("status")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        object_ = d.pop("object", UNSET)

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_instructions(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        instructions = _parse_instructions(d.pop("instructions", UNSET))

        def _parse_config(data: object) -> AgentResponseConfigType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                config_type_0 = AgentResponseConfigType0.from_dict(data)

                return config_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AgentResponseConfigType0 | None | Unset, data)

        config = _parse_config(d.pop("config", UNSET))

        def _parse_tools(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tools_type_0 = cast(list[str], data)

                return tools_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        tools = _parse_tools(d.pop("tools", UNSET))

        def _parse_mcp_servers(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                mcp_servers_type_0 = cast(list[str], data)

                return mcp_servers_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        mcp_servers = _parse_mcp_servers(d.pop("mcp_servers", UNSET))

        agent_response = cls(
            id=id,
            name=name,
            model=model,
            version=version,
            current_version_id=current_version_id,
            project_id=project_id,
            organization_id=organization_id,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            object_=object_,
            description=description,
            instructions=instructions,
            config=config,
            tools=tools,
            mcp_servers=mcp_servers,
        )

        agent_response.additional_properties = d
        return agent_response

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

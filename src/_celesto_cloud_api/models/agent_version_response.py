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
    from ..models.agent_version_response_config_type_0 import (
        AgentVersionResponseConfigType0,
    )
    from ..models.agent_version_response_definition import (
        AgentVersionResponseDefinition,
    )


T = TypeVar("T", bound="AgentVersionResponse")


@_attrs_define
class AgentVersionResponse:
    """
    Attributes:
        id (str):
        agent_id (str):
        version (int):
        name (str):
        model (str):
        definition (AgentVersionResponseDefinition):
        created_at (datetime.datetime):
        object_ (str | Unset):  Default: 'agent_version'.
        description (None | str | Unset):
        instructions (None | str | Unset):
        config (AgentVersionResponseConfigType0 | None | Unset):
        tools (list[str] | None | Unset):
        mcp_servers (list[str] | None | Unset):
    """

    id: str
    agent_id: str
    version: int
    name: str
    model: str
    definition: AgentVersionResponseDefinition
    created_at: datetime.datetime
    object_: str | Unset = "agent_version"
    description: None | str | Unset = UNSET
    instructions: None | str | Unset = UNSET
    config: AgentVersionResponseConfigType0 | None | Unset = UNSET
    tools: list[str] | None | Unset = UNSET
    mcp_servers: list[str] | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.agent_version_response_config_type_0 import (
            AgentVersionResponseConfigType0,
        )  # noqa: PLC0415
        from ..models.agent_version_response_definition import (
            AgentVersionResponseDefinition,
        )  # noqa: PLC0415

        id = self.id

        agent_id = self.agent_id

        version = self.version

        name = self.name

        model = self.model

        definition = self.definition.to_dict()

        created_at = self.created_at.isoformat()

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
        elif isinstance(self.config, AgentVersionResponseConfigType0):
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
                "agent_id": agent_id,
                "version": version,
                "name": name,
                "model": model,
                "definition": definition,
                "created_at": created_at,
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
        from ..models.agent_version_response_config_type_0 import (
            AgentVersionResponseConfigType0,
        )  # noqa: PLC0415
        from ..models.agent_version_response_definition import (
            AgentVersionResponseDefinition,
        )  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        agent_id = d.pop("agent_id")

        version = d.pop("version")

        name = d.pop("name")

        model = d.pop("model")

        definition = AgentVersionResponseDefinition.from_dict(d.pop("definition"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

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

        def _parse_config(
            data: object,
        ) -> AgentVersionResponseConfigType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                config_type_0 = AgentVersionResponseConfigType0.from_dict(data)

                return config_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AgentVersionResponseConfigType0 | None | Unset, data)

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

        agent_version_response = cls(
            id=id,
            agent_id=agent_id,
            version=version,
            name=name,
            model=model,
            definition=definition,
            created_at=created_at,
            object_=object_,
            description=description,
            instructions=instructions,
            config=config,
            tools=tools,
            mcp_servers=mcp_servers,
        )

        agent_version_response.additional_properties = d
        return agent_version_response

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="TelegramBotCreateRequest")


@_attrs_define
class TelegramBotCreateRequest:
    """Register a bot created with Telegram's @BotFather.

    Supply `project_id`, or `organization_id` to use that organization's
    default project.

        Attributes:
            bot_token (str): Token from @BotFather. Stored encrypted and never returned.
            agent_id (None | str | Unset): Agent that answers this bot's chats
            project_id (None | str | Unset): Project to create the bot in
            organization_id (None | str | Unset): Organization; resolves to its default project
            name (None | str | Unset): Display name; defaults to the bot's Telegram name
    """

    bot_token: str
    agent_id: None | str | Unset = UNSET
    project_id: None | str | Unset = UNSET
    organization_id: None | str | Unset = UNSET
    name: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        bot_token = self.bot_token

        agent_id: None | str | Unset
        if isinstance(self.agent_id, Unset):
            agent_id = UNSET
        else:
            agent_id = self.agent_id

        project_id: None | str | Unset
        if isinstance(self.project_id, Unset):
            project_id = UNSET
        else:
            project_id = self.project_id

        organization_id: None | str | Unset
        if isinstance(self.organization_id, Unset):
            organization_id = UNSET
        else:
            organization_id = self.organization_id

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "bot_token": bot_token,
            }
        )
        if agent_id is not UNSET:
            field_dict["agent_id"] = agent_id
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if organization_id is not UNSET:
            field_dict["organization_id"] = organization_id
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        bot_token = d.pop("bot_token")

        def _parse_agent_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        agent_id = _parse_agent_id(d.pop("agent_id", UNSET))

        def _parse_project_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        project_id = _parse_project_id(d.pop("project_id", UNSET))

        def _parse_organization_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        organization_id = _parse_organization_id(d.pop("organization_id", UNSET))

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        telegram_bot_create_request = cls(
            bot_token=bot_token,
            agent_id=agent_id,
            project_id=project_id,
            organization_id=organization_id,
            name=name,
        )

        telegram_bot_create_request.additional_properties = d
        return telegram_bot_create_request

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

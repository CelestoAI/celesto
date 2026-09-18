from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.telegram_bot_status import TelegramBotStatus
from typing import cast
import datetime


T = TypeVar("T", bound="TelegramBotResponse")


@_attrs_define
class TelegramBotResponse:
    """
    Attributes:
        id (str):
        organization_id (str):
        project_id (str):
        agent_id (None | str):
        name (str):
        telegram_bot_id (str):
        telegram_username (None | str):
        status (TelegramBotStatus): Lifecycle status of a bot registration.

            DISABLED keeps the row and its history but stops the webhook from running
            agents, so a noisy bot can be silenced without losing its chats.
        webhook_id (str):
        webhook_registered_at (datetime.datetime | None):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
    """

    id: str
    organization_id: str
    project_id: str
    agent_id: None | str
    name: str
    telegram_bot_id: str
    telegram_username: None | str
    status: TelegramBotStatus
    webhook_id: str
    webhook_registered_at: datetime.datetime | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        organization_id = self.organization_id

        project_id = self.project_id

        agent_id: None | str
        agent_id = self.agent_id

        name = self.name

        telegram_bot_id = self.telegram_bot_id

        telegram_username: None | str
        telegram_username = self.telegram_username

        status = self.status.value

        webhook_id = self.webhook_id

        webhook_registered_at: None | str
        if isinstance(self.webhook_registered_at, datetime.datetime):
            webhook_registered_at = self.webhook_registered_at.isoformat()
        else:
            webhook_registered_at = self.webhook_registered_at

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "organization_id": organization_id,
                "project_id": project_id,
                "agent_id": agent_id,
                "name": name,
                "telegram_bot_id": telegram_bot_id,
                "telegram_username": telegram_username,
                "status": status,
                "webhook_id": webhook_id,
                "webhook_registered_at": webhook_registered_at,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        organization_id = d.pop("organization_id")

        project_id = d.pop("project_id")

        def _parse_agent_id(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        agent_id = _parse_agent_id(d.pop("agent_id"))

        name = d.pop("name")

        telegram_bot_id = d.pop("telegram_bot_id")

        def _parse_telegram_username(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        telegram_username = _parse_telegram_username(d.pop("telegram_username"))

        status = TelegramBotStatus(d.pop("status"))

        webhook_id = d.pop("webhook_id")

        def _parse_webhook_registered_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                webhook_registered_at_type_0 = datetime.datetime.fromisoformat(data)

                return webhook_registered_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        webhook_registered_at = _parse_webhook_registered_at(
            d.pop("webhook_registered_at")
        )

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        telegram_bot_response = cls(
            id=id,
            organization_id=organization_id,
            project_id=project_id,
            agent_id=agent_id,
            name=name,
            telegram_bot_id=telegram_bot_id,
            telegram_username=telegram_username,
            status=status,
            webhook_id=webhook_id,
            webhook_registered_at=webhook_registered_at,
            created_at=created_at,
            updated_at=updated_at,
        )

        telegram_bot_response.additional_properties = d
        return telegram_bot_response

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

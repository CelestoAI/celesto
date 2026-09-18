from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
import datetime


T = TypeVar("T", bound="TelegramChatResponse")


@_attrs_define
class TelegramChatResponse:
    """
    Attributes:
        id (str):
        chat_id (str):
        chat_type (None | str):
        thread_id (str):
        last_update_id (int | None):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
    """

    id: str
    chat_id: str
    chat_type: None | str
    thread_id: str
    last_update_id: int | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        chat_id = self.chat_id

        chat_type: None | str
        chat_type = self.chat_type

        thread_id = self.thread_id

        last_update_id: int | None
        last_update_id = self.last_update_id

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "chat_id": chat_id,
                "chat_type": chat_type,
                "thread_id": thread_id,
                "last_update_id": last_update_id,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        chat_id = d.pop("chat_id")

        def _parse_chat_type(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        chat_type = _parse_chat_type(d.pop("chat_type"))

        thread_id = d.pop("thread_id")

        def _parse_last_update_id(data: object) -> int | None:
            if data is None:
                return data
            return cast(int | None, data)

        last_update_id = _parse_last_update_id(d.pop("last_update_id"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        telegram_chat_response = cls(
            id=id,
            chat_id=chat_id,
            chat_type=chat_type,
            thread_id=thread_id,
            last_update_id=last_update_id,
            created_at=created_at,
            updated_at=updated_at,
        )

        telegram_chat_response.additional_properties = d
        return telegram_chat_response

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

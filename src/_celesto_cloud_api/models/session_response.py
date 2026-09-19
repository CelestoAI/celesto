from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
import datetime


T = TypeVar("T", bound="SessionResponse")


@_attrs_define
class SessionResponse:
    """
    Attributes:
        id (str):
        end_user_id (str):
        status (str):
        message_count (int):
        created_at (datetime.datetime):
        object_ (str | Unset):  Default: 'session'.
        agent_id (None | str | Unset):
        last_message_at (datetime.datetime | None | Unset):
    """

    id: str
    end_user_id: str
    status: str
    message_count: int
    created_at: datetime.datetime
    object_: str | Unset = "session"
    agent_id: None | str | Unset = UNSET
    last_message_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        end_user_id = self.end_user_id

        status = self.status

        message_count = self.message_count

        created_at = self.created_at.isoformat()

        object_ = self.object_

        agent_id: None | str | Unset
        if isinstance(self.agent_id, Unset):
            agent_id = UNSET
        else:
            agent_id = self.agent_id

        last_message_at: None | str | Unset
        if isinstance(self.last_message_at, Unset):
            last_message_at = UNSET
        elif isinstance(self.last_message_at, datetime.datetime):
            last_message_at = self.last_message_at.isoformat()
        else:
            last_message_at = self.last_message_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "end_user_id": end_user_id,
                "status": status,
                "message_count": message_count,
                "created_at": created_at,
            }
        )
        if object_ is not UNSET:
            field_dict["object"] = object_
        if agent_id is not UNSET:
            field_dict["agent_id"] = agent_id
        if last_message_at is not UNSET:
            field_dict["last_message_at"] = last_message_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        end_user_id = d.pop("end_user_id")

        status = d.pop("status")

        message_count = d.pop("message_count")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        object_ = d.pop("object", UNSET)

        def _parse_agent_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        agent_id = _parse_agent_id(d.pop("agent_id", UNSET))

        def _parse_last_message_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_message_at_type_0 = datetime.datetime.fromisoformat(data)

                return last_message_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        last_message_at = _parse_last_message_at(d.pop("last_message_at", UNSET))

        session_response = cls(
            id=id,
            end_user_id=end_user_id,
            status=status,
            message_count=message_count,
            created_at=created_at,
            object_=object_,
            agent_id=agent_id,
            last_message_at=last_message_at,
        )

        session_response.additional_properties = d
        return session_response

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

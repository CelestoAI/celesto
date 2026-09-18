from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.session_message_item import SessionMessageItem
    from ..models.session_response import SessionResponse


T = TypeVar("T", bound="SessionMessagesResponse")


@_attrs_define
class SessionMessagesResponse:
    """
    Attributes:
        session (SessionResponse):
        messages (list[SessionMessageItem]):
        has_more (bool | Unset):  Default: False.
    """

    session: SessionResponse
    messages: list[SessionMessageItem]
    has_more: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.session_message_item import SessionMessageItem  # noqa: PLC0415
        from ..models.session_response import SessionResponse  # noqa: PLC0415

        session = self.session.to_dict()

        messages = []
        for messages_item_data in self.messages:
            messages_item = messages_item_data.to_dict()
            messages.append(messages_item)

        has_more = self.has_more

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "session": session,
                "messages": messages,
            }
        )
        if has_more is not UNSET:
            field_dict["has_more"] = has_more

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.session_message_item import SessionMessageItem  # noqa: PLC0415
        from ..models.session_response import SessionResponse  # noqa: PLC0415

        d = dict(src_dict)
        session = SessionResponse.from_dict(d.pop("session"))

        messages = []
        _messages = d.pop("messages")
        for messages_item_data in _messages:
            messages_item = SessionMessageItem.from_dict(messages_item_data)

            messages.append(messages_item)

        has_more = d.pop("has_more", UNSET)

        session_messages_response = cls(
            session=session,
            messages=messages,
            has_more=has_more,
        )

        session_messages_response.additional_properties = d
        return session_messages_response

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

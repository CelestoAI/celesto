from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="ContactEmailRequest")


@_attrs_define
class ContactEmailRequest:
    """
    Attributes:
        to (str):
        reply_to (str):
        subject (str):
        text (None | str | Unset):
        html (None | str | Unset):
    """

    to: str
    reply_to: str
    subject: str
    text: None | str | Unset = UNSET
    html: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        to = self.to

        reply_to = self.reply_to

        subject = self.subject

        text: None | str | Unset
        if isinstance(self.text, Unset):
            text = UNSET
        else:
            text = self.text

        html: None | str | Unset
        if isinstance(self.html, Unset):
            html = UNSET
        else:
            html = self.html

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "to": to,
                "reply_to": reply_to,
                "subject": subject,
            }
        )
        if text is not UNSET:
            field_dict["text"] = text
        if html is not UNSET:
            field_dict["html"] = html

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        to = d.pop("to")

        reply_to = d.pop("reply_to")

        subject = d.pop("subject")

        def _parse_text(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        text = _parse_text(d.pop("text", UNSET))

        def _parse_html(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        html = _parse_html(d.pop("html", UNSET))

        contact_email_request = cls(
            to=to,
            reply_to=reply_to,
            subject=subject,
            text=text,
            html=html,
        )

        contact_email_request.additional_properties = d
        return contact_email_request

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="SendEmailRequest")


@_attrs_define
class SendEmailRequest:
    """Request schema for sending an email

    Example:
        {'bcc': ['bcc@example.com'], 'body': 'Thank you for the meeting today...', 'cc': ['cc@example.com'],
            'html_body': '<p>Thank you for the meeting today...</p>', 'reply_to': 'sender@example.com', 'subject': 'Meeting
            Follow-up', 'to_email': 'recipient@example.com'}

    Attributes:
        to_email (list[str] | str): Recipient email address(es)
        subject (str): Email subject
        body (str): Plain text body of the email
        html_body (None | str | Unset): Optional HTML body of the email
        cc (list[str] | None | Unset): CC recipients
        bcc (list[str] | None | Unset): BCC recipients
        reply_to (None | str | Unset): Reply-to email address
    """

    to_email: list[str] | str
    subject: str
    body: str
    html_body: None | str | Unset = UNSET
    cc: list[str] | None | Unset = UNSET
    bcc: list[str] | None | Unset = UNSET
    reply_to: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        to_email: list[str] | str
        if isinstance(self.to_email, list):
            to_email = self.to_email

        else:
            to_email = self.to_email

        subject = self.subject

        body = self.body

        html_body: None | str | Unset
        if isinstance(self.html_body, Unset):
            html_body = UNSET
        else:
            html_body = self.html_body

        cc: list[str] | None | Unset
        if isinstance(self.cc, Unset):
            cc = UNSET
        elif isinstance(self.cc, list):
            cc = self.cc

        else:
            cc = self.cc

        bcc: list[str] | None | Unset
        if isinstance(self.bcc, Unset):
            bcc = UNSET
        elif isinstance(self.bcc, list):
            bcc = self.bcc

        else:
            bcc = self.bcc

        reply_to: None | str | Unset
        if isinstance(self.reply_to, Unset):
            reply_to = UNSET
        else:
            reply_to = self.reply_to

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "to_email": to_email,
                "subject": subject,
                "body": body,
            }
        )
        if html_body is not UNSET:
            field_dict["html_body"] = html_body
        if cc is not UNSET:
            field_dict["cc"] = cc
        if bcc is not UNSET:
            field_dict["bcc"] = bcc
        if reply_to is not UNSET:
            field_dict["reply_to"] = reply_to

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_to_email(data: object) -> list[str] | str:
            try:
                if not isinstance(data, list):
                    raise TypeError()
                to_email_type_1 = cast(list[str], data)

                return to_email_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | str, data)

        to_email = _parse_to_email(d.pop("to_email"))

        subject = d.pop("subject")

        body = d.pop("body")

        def _parse_html_body(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        html_body = _parse_html_body(d.pop("html_body", UNSET))

        def _parse_cc(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                cc_type_0 = cast(list[str], data)

                return cc_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        cc = _parse_cc(d.pop("cc", UNSET))

        def _parse_bcc(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                bcc_type_0 = cast(list[str], data)

                return bcc_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        bcc = _parse_bcc(d.pop("bcc", UNSET))

        def _parse_reply_to(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        reply_to = _parse_reply_to(d.pop("reply_to", UNSET))

        send_email_request = cls(
            to_email=to_email,
            subject=subject,
            body=body,
            html_body=html_body,
            cc=cc,
            bcc=bcc,
            reply_to=reply_to,
        )

        send_email_request.additional_properties = d
        return send_email_request

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

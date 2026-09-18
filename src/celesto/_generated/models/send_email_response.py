from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="SendEmailResponse")


@_attrs_define
class SendEmailResponse:
    """Response schema for email sending result

    Example:
        {'from_email': 'user@gmail.com', 'message_id': '18df5a2c8e9b5d4f', 'success': True}

    Attributes:
        success (bool): Whether the email was sent successfully
        message_id (None | str | Unset): Gmail message ID if successful
        error (None | str | Unset): Error message if failed
        from_email (None | str | Unset): Email address used to send the email
    """

    success: bool
    message_id: None | str | Unset = UNSET
    error: None | str | Unset = UNSET
    from_email: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        success = self.success

        message_id: None | str | Unset
        if isinstance(self.message_id, Unset):
            message_id = UNSET
        else:
            message_id = self.message_id

        error: None | str | Unset
        if isinstance(self.error, Unset):
            error = UNSET
        else:
            error = self.error

        from_email: None | str | Unset
        if isinstance(self.from_email, Unset):
            from_email = UNSET
        else:
            from_email = self.from_email

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "success": success,
            }
        )
        if message_id is not UNSET:
            field_dict["message_id"] = message_id
        if error is not UNSET:
            field_dict["error"] = error
        if from_email is not UNSET:
            field_dict["from_email"] = from_email

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        success = d.pop("success")

        def _parse_message_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        message_id = _parse_message_id(d.pop("message_id", UNSET))

        def _parse_error(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error = _parse_error(d.pop("error", UNSET))

        def _parse_from_email(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        from_email = _parse_from_email(d.pop("from_email", UNSET))

        send_email_response = cls(
            success=success,
            message_id=message_id,
            error=error,
            from_email=from_email,
        )

        send_email_response.additional_properties = d
        return send_email_response

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

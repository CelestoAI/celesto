from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset


T = TypeVar("T", bound="ComputerBrowserConnectionResponse")


@_attrs_define
class ComputerBrowserConnectionResponse:
    """Short-lived connection info for browser automation over CDP.

    Attributes:
        gateway_url (str):
        token (str):
        expires_at (str):
    """

    gateway_url: str
    token: str
    expires_at: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        gateway_url = self.gateway_url

        token = self.token

        expires_at = self.expires_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "gateway_url": gateway_url,
                "token": token,
                "expires_at": expires_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        gateway_url = d.pop("gateway_url")

        token = d.pop("token")

        expires_at = d.pop("expires_at")

        computer_browser_connection_response = cls(
            gateway_url=gateway_url,
            token=token,
            expires_at=expires_at,
        )

        computer_browser_connection_response.additional_properties = d
        return computer_browser_connection_response

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

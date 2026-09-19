from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.computer_display_connection_response_mode import (
    ComputerDisplayConnectionResponseMode,
)


T = TypeVar("T", bound="ComputerDisplayConnectionResponse")


@_attrs_define
class ComputerDisplayConnectionResponse:
    """Short-lived connection info for attaching to a computer display.

    A display connection has no durable row or separate id. The token is
    scoped directly to the computer and carries the authorization on its own.

        Attributes:
            gateway_url (str):
            token (str):
            expires_at (str):
            mode (ComputerDisplayConnectionResponseMode):
    """

    gateway_url: str
    token: str
    expires_at: str
    mode: ComputerDisplayConnectionResponseMode
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        gateway_url = self.gateway_url

        token = self.token

        expires_at = self.expires_at

        mode = self.mode.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "gateway_url": gateway_url,
                "token": token,
                "expires_at": expires_at,
                "mode": mode,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        gateway_url = d.pop("gateway_url")

        token = d.pop("token")

        expires_at = d.pop("expires_at")

        mode = ComputerDisplayConnectionResponseMode(d.pop("mode"))

        computer_display_connection_response = cls(
            gateway_url=gateway_url,
            token=token,
            expires_at=expires_at,
            mode=mode,
        )

        computer_display_connection_response.additional_properties = d
        return computer_display_connection_response

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

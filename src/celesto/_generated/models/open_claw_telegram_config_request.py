from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset


T = TypeVar("T", bound="OpenClawTelegramConfigRequest")


@_attrs_define
class OpenClawTelegramConfigRequest:
    """
    Attributes:
        telegram_bot_token (str):
    """

    telegram_bot_token: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        telegram_bot_token = self.telegram_bot_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "telegram_bot_token": telegram_bot_token,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        telegram_bot_token = d.pop("telegram_bot_token")

        open_claw_telegram_config_request = cls(
            telegram_bot_token=telegram_bot_token,
        )

        open_claw_telegram_config_request.additional_properties = d
        return open_claw_telegram_config_request

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

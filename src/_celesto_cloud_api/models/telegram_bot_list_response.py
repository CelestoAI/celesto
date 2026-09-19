from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast

if TYPE_CHECKING:
    from ..models.telegram_bot_response import TelegramBotResponse


T = TypeVar("T", bound="TelegramBotListResponse")


@_attrs_define
class TelegramBotListResponse:
    """
    Attributes:
        data (list[TelegramBotResponse]):
        total (int):
        limit (int):
        offset (int):
    """

    data: list[TelegramBotResponse]
    total: int
    limit: int
    offset: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.telegram_bot_response import TelegramBotResponse  # noqa: PLC0415

        data = []
        for data_item_data in self.data:
            data_item = data_item_data.to_dict()
            data.append(data_item)

        total = self.total

        limit = self.limit

        offset = self.offset

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
                "total": total,
                "limit": limit,
                "offset": offset,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.telegram_bot_response import TelegramBotResponse  # noqa: PLC0415

        d = dict(src_dict)
        data = []
        _data = d.pop("data")
        for data_item_data in _data:
            data_item = TelegramBotResponse.from_dict(data_item_data)

            data.append(data_item)

        total = d.pop("total")

        limit = d.pop("limit")

        offset = d.pop("offset")

        telegram_bot_list_response = cls(
            data=data,
            total=total,
            limit=limit,
            offset=offset,
        )

        telegram_bot_list_response.additional_properties = d
        return telegram_bot_list_response

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset


T = TypeVar("T", bound="UsageRewardResponse")


@_attrs_define
class UsageRewardResponse:
    """Confirmed Autumn runtime credit grant.

    Attributes:
        reward_id (str):
        credit_added_usd (str):
    """

    reward_id: str
    credit_added_usd: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        reward_id = self.reward_id

        credit_added_usd = self.credit_added_usd

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "reward_id": reward_id,
                "credit_added_usd": credit_added_usd,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        reward_id = d.pop("reward_id")

        credit_added_usd = d.pop("credit_added_usd")

        usage_reward_response = cls(
            reward_id=reward_id,
            credit_added_usd=credit_added_usd,
        )

        usage_reward_response.additional_properties = d
        return usage_reward_response

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

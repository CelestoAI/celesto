from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset


T = TypeVar("T", bound="RunUsage")


@_attrs_define
class RunUsage:
    """
    Attributes:
        input_tokens (int):
        output_tokens (int):
        total_tokens (int):
        cost_usd (str):
    """

    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        input_tokens = self.input_tokens

        output_tokens = self.output_tokens

        total_tokens = self.total_tokens

        cost_usd = self.cost_usd

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "cost_usd": cost_usd,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        input_tokens = d.pop("input_tokens")

        output_tokens = d.pop("output_tokens")

        total_tokens = d.pop("total_tokens")

        cost_usd = d.pop("cost_usd")

        run_usage = cls(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
        )

        run_usage.additional_properties = d
        return run_usage

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

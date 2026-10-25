from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset


T = TypeVar("T", bound="UsageBySizeResponse")


@_attrs_define
class UsageBySizeResponse:
    """Locally checkpointed runtime, which is an estimate until Autumn invoices it.

    Attributes:
        size_id (str):
        checkpointed_seconds (int):
        estimated_cost_usd (str):
    """

    size_id: str
    checkpointed_seconds: int
    estimated_cost_usd: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        size_id = self.size_id

        checkpointed_seconds = self.checkpointed_seconds

        estimated_cost_usd = self.estimated_cost_usd

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "size_id": size_id,
                "checkpointed_seconds": checkpointed_seconds,
                "estimated_cost_usd": estimated_cost_usd,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        size_id = d.pop("size_id")

        checkpointed_seconds = d.pop("checkpointed_seconds")

        estimated_cost_usd = d.pop("estimated_cost_usd")

        usage_by_size_response = cls(
            size_id=size_id,
            checkpointed_seconds=checkpointed_seconds,
            estimated_cost_usd=estimated_cost_usd,
        )

        usage_by_size_response.additional_properties = d
        return usage_by_size_response

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

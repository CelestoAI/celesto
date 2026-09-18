from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
import datetime


T = TypeVar("T", bound="MetricsSpendDay")


@_attrs_define
class MetricsSpendDay:
    """
    Attributes:
        date (datetime.date):
        cost_usd (str):
    """

    date: datetime.date
    cost_usd: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        date = self.date.isoformat()

        cost_usd = self.cost_usd

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "date": date,
                "cost_usd": cost_usd,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        date = datetime.date.fromisoformat(d.pop("date"))

        cost_usd = d.pop("cost_usd")

        metrics_spend_day = cls(
            date=date,
            cost_usd=cost_usd,
        )

        metrics_spend_day.additional_properties = d
        return metrics_spend_day

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

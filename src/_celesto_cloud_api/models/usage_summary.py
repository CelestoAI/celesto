from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
import datetime


T = TypeVar("T", bound="UsageSummary")


@_attrs_define
class UsageSummary:
    """Usage summary for a single billing unit.

    Attributes:
        included (int): Included units for the period (-1 = unlimited)
        used (int): Units used in the period
        overage_used (int): Overage units used in the period
        remaining (int): Remaining included units (-1 = unlimited)
        period_start (datetime.datetime): Billing period start
        period_end (datetime.datetime): Billing period end
        is_unlimited (bool): Whether the unit is unlimited
    """

    included: int
    used: int
    overage_used: int
    remaining: int
    period_start: datetime.datetime
    period_end: datetime.datetime
    is_unlimited: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        included = self.included

        used = self.used

        overage_used = self.overage_used

        remaining = self.remaining

        period_start = self.period_start.isoformat()

        period_end = self.period_end.isoformat()

        is_unlimited = self.is_unlimited

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "included": included,
                "used": used,
                "overage_used": overage_used,
                "remaining": remaining,
                "period_start": period_start,
                "period_end": period_end,
                "is_unlimited": is_unlimited,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        included = d.pop("included")

        used = d.pop("used")

        overage_used = d.pop("overage_used")

        remaining = d.pop("remaining")

        period_start = datetime.datetime.fromisoformat(d.pop("period_start"))

        period_end = datetime.datetime.fromisoformat(d.pop("period_end"))

        is_unlimited = d.pop("is_unlimited")

        usage_summary = cls(
            included=included,
            used=used,
            overage_used=overage_used,
            remaining=remaining,
            period_start=period_start,
            period_end=period_end,
            is_unlimited=is_unlimited,
        )

        usage_summary.additional_properties = d
        return usage_summary

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

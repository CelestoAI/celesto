from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
import datetime


T = TypeVar("T", bound="SandboxHoursUsageBucket")


@_attrs_define
class SandboxHoursUsageBucket:
    """Sandbox hours consumed within one time bin.

    Attributes:
        period (datetime.datetime): Start of the time bin (UTC)
        hours (str): Standard sandbox-hours consumed in this bin
    """

    period: datetime.datetime
    hours: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        period = self.period.isoformat()

        hours = self.hours

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "period": period,
                "hours": hours,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        period = datetime.datetime.fromisoformat(d.pop("period"))

        hours = d.pop("hours")

        sandbox_hours_usage_bucket = cls(
            period=period,
            hours=hours,
        )

        sandbox_hours_usage_bucket.additional_properties = d
        return sandbox_hours_usage_bucket

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

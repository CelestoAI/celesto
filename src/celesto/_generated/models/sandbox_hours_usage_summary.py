from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
import datetime


T = TypeVar("T", bound="SandboxHoursUsageSummary")


@_attrs_define
class SandboxHoursUsageSummary:
    """Current standard sandbox-hour usage reported by Autumn.

    Attributes:
        included (str): Standard sandbox-hours included by the plan
        used (str): Standard sandbox-hours used in the current period
        overage_used (str): Standard sandbox-hours used beyond the granted balance
        remaining (str): Standard sandbox-hours remaining (-1 = unlimited)
        is_unlimited (bool): Whether sandbox-hour usage is unlimited
        overage_allowed (bool): Whether usage can continue as billable overage
        resets_at (datetime.datetime | None | Unset): When the Autumn balance resets
    """

    included: str
    used: str
    overage_used: str
    remaining: str
    is_unlimited: bool
    overage_allowed: bool
    resets_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        included = self.included

        used = self.used

        overage_used = self.overage_used

        remaining = self.remaining

        is_unlimited = self.is_unlimited

        overage_allowed = self.overage_allowed

        resets_at: None | str | Unset
        if isinstance(self.resets_at, Unset):
            resets_at = UNSET
        elif isinstance(self.resets_at, datetime.datetime):
            resets_at = self.resets_at.isoformat()
        else:
            resets_at = self.resets_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "included": included,
                "used": used,
                "overage_used": overage_used,
                "remaining": remaining,
                "is_unlimited": is_unlimited,
                "overage_allowed": overage_allowed,
            }
        )
        if resets_at is not UNSET:
            field_dict["resets_at"] = resets_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        included = d.pop("included")

        used = d.pop("used")

        overage_used = d.pop("overage_used")

        remaining = d.pop("remaining")

        is_unlimited = d.pop("is_unlimited")

        overage_allowed = d.pop("overage_allowed")

        def _parse_resets_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                resets_at_type_0 = datetime.datetime.fromisoformat(data)

                return resets_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        resets_at = _parse_resets_at(d.pop("resets_at", UNSET))

        sandbox_hours_usage_summary = cls(
            included=included,
            used=used,
            overage_used=overage_used,
            remaining=remaining,
            is_unlimited=is_unlimited,
            overage_allowed=overage_allowed,
            resets_at=resets_at,
        )

        sandbox_hours_usage_summary.additional_properties = d
        return sandbox_hours_usage_summary

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

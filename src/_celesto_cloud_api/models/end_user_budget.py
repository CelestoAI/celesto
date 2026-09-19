from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
import datetime


T = TypeVar("T", bound="EndUserBudget")


@_attrs_define
class EndUserBudget:
    """
    Attributes:
        source (str):
        window_start (datetime.datetime):
        window_resets_at (datetime.datetime):
        spent_usd (str):
        cap_usd (None | str | Unset):
        remaining_usd (None | str | Unset):
    """

    source: str
    window_start: datetime.datetime
    window_resets_at: datetime.datetime
    spent_usd: str
    cap_usd: None | str | Unset = UNSET
    remaining_usd: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        source = self.source

        window_start = self.window_start.isoformat()

        window_resets_at = self.window_resets_at.isoformat()

        spent_usd = self.spent_usd

        cap_usd: None | str | Unset
        if isinstance(self.cap_usd, Unset):
            cap_usd = UNSET
        else:
            cap_usd = self.cap_usd

        remaining_usd: None | str | Unset
        if isinstance(self.remaining_usd, Unset):
            remaining_usd = UNSET
        else:
            remaining_usd = self.remaining_usd

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "source": source,
                "window_start": window_start,
                "window_resets_at": window_resets_at,
                "spent_usd": spent_usd,
            }
        )
        if cap_usd is not UNSET:
            field_dict["cap_usd"] = cap_usd
        if remaining_usd is not UNSET:
            field_dict["remaining_usd"] = remaining_usd

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        source = d.pop("source")

        window_start = datetime.datetime.fromisoformat(d.pop("window_start"))

        window_resets_at = datetime.datetime.fromisoformat(d.pop("window_resets_at"))

        spent_usd = d.pop("spent_usd")

        def _parse_cap_usd(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        cap_usd = _parse_cap_usd(d.pop("cap_usd", UNSET))

        def _parse_remaining_usd(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        remaining_usd = _parse_remaining_usd(d.pop("remaining_usd", UNSET))

        end_user_budget = cls(
            source=source,
            window_start=window_start,
            window_resets_at=window_resets_at,
            spent_usd=spent_usd,
            cap_usd=cap_usd,
            remaining_usd=remaining_usd,
        )

        end_user_budget.additional_properties = d
        return end_user_budget

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

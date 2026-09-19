from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="RuntimeMetricsTotals")


@_attrs_define
class RuntimeMetricsTotals:
    """
    Attributes:
        runs (int):
        active_end_users (int):
        cost_usd (str):
        success_rate (float | None | Unset):
    """

    runs: int
    active_end_users: int
    cost_usd: str
    success_rate: float | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        runs = self.runs

        active_end_users = self.active_end_users

        cost_usd = self.cost_usd

        success_rate: float | None | Unset
        if isinstance(self.success_rate, Unset):
            success_rate = UNSET
        else:
            success_rate = self.success_rate

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "runs": runs,
                "active_end_users": active_end_users,
                "cost_usd": cost_usd,
            }
        )
        if success_rate is not UNSET:
            field_dict["success_rate"] = success_rate

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        runs = d.pop("runs")

        active_end_users = d.pop("active_end_users")

        cost_usd = d.pop("cost_usd")

        def _parse_success_rate(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        success_rate = _parse_success_rate(d.pop("success_rate", UNSET))

        runtime_metrics_totals = cls(
            runs=runs,
            active_end_users=active_end_users,
            cost_usd=cost_usd,
            success_rate=success_rate,
        )

        runtime_metrics_totals.additional_properties = d
        return runtime_metrics_totals

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

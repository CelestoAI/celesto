from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast


T = TypeVar("T", bound="AutoTopupRequest")


@_attrs_define
class AutoTopupRequest:
    """An owner's auto top-up settings: below the threshold, charge the saved card the amount, within the monthly limit.

    Attributes:
        enabled (bool):
        threshold_usd (float | str):
        amount_usd (float | str):
        monthly_limit_usd (float | str):
    """

    enabled: bool
    threshold_usd: float | str
    amount_usd: float | str
    monthly_limit_usd: float | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        enabled = self.enabled

        threshold_usd: float | str
        threshold_usd = self.threshold_usd

        amount_usd: float | str
        amount_usd = self.amount_usd

        monthly_limit_usd: float | str
        monthly_limit_usd = self.monthly_limit_usd

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "enabled": enabled,
                "threshold_usd": threshold_usd,
                "amount_usd": amount_usd,
                "monthly_limit_usd": monthly_limit_usd,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        enabled = d.pop("enabled")

        def _parse_threshold_usd(data: object) -> float | str:
            return cast(float | str, data)

        threshold_usd = _parse_threshold_usd(d.pop("threshold_usd"))

        def _parse_amount_usd(data: object) -> float | str:
            return cast(float | str, data)

        amount_usd = _parse_amount_usd(d.pop("amount_usd"))

        def _parse_monthly_limit_usd(data: object) -> float | str:
            return cast(float | str, data)

        monthly_limit_usd = _parse_monthly_limit_usd(d.pop("monthly_limit_usd"))

        auto_topup_request = cls(
            enabled=enabled,
            threshold_usd=threshold_usd,
            amount_usd=amount_usd,
            monthly_limit_usd=monthly_limit_usd,
        )

        auto_topup_request.additional_properties = d
        return auto_topup_request

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

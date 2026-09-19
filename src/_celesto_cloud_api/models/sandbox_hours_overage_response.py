from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset


T = TypeVar("T", bound="SandboxHoursOverageResponse")


@_attrs_define
class SandboxHoursOverageResponse:
    """Usage-based price for active sandbox hours beyond the included amount.

    Attributes:
        amount_usd (str): Price charged per billing-unit block
        billing_units (str): Sandbox hours represented by one priced block
        billing_method (str): Autumn billing method
        billing_interval (str): Reset interval for the usage price
    """

    amount_usd: str
    billing_units: str
    billing_method: str
    billing_interval: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        amount_usd = self.amount_usd

        billing_units = self.billing_units

        billing_method = self.billing_method

        billing_interval = self.billing_interval

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "amount_usd": amount_usd,
                "billing_units": billing_units,
                "billing_method": billing_method,
                "billing_interval": billing_interval,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        amount_usd = d.pop("amount_usd")

        billing_units = d.pop("billing_units")

        billing_method = d.pop("billing_method")

        billing_interval = d.pop("billing_interval")

        sandbox_hours_overage_response = cls(
            amount_usd=amount_usd,
            billing_units=billing_units,
            billing_method=billing_method,
            billing_interval=billing_interval,
        )

        sandbox_hours_overage_response.additional_properties = d
        return sandbox_hours_overage_response

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

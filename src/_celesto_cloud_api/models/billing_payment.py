from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
import datetime


T = TypeVar("T", bound="BillingPayment")


@_attrs_define
class BillingPayment:
    """
    Attributes:
        id (str):
        paid_at (datetime.datetime):
        collected_usd (str):
        refunded_usd (str):
        disputed (bool):
    """

    id: str
    paid_at: datetime.datetime
    collected_usd: str
    refunded_usd: str
    disputed: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        paid_at = self.paid_at.isoformat()

        collected_usd = self.collected_usd

        refunded_usd = self.refunded_usd

        disputed = self.disputed

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "paid_at": paid_at,
                "collected_usd": collected_usd,
                "refunded_usd": refunded_usd,
                "disputed": disputed,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        paid_at = datetime.datetime.fromisoformat(d.pop("paid_at"))

        collected_usd = d.pop("collected_usd")

        refunded_usd = d.pop("refunded_usd")

        disputed = d.pop("disputed")

        billing_payment = cls(
            id=id,
            paid_at=paid_at,
            collected_usd=collected_usd,
            refunded_usd=refunded_usd,
            disputed=disputed,
        )

        billing_payment.additional_properties = d
        return billing_payment

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

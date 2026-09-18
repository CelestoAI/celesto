from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.billing_plan_entitlements_response import (
        BillingPlanEntitlementsResponse,
    )


T = TypeVar("T", bound="SubscriptionPlanResponse")


@_attrs_define
class SubscriptionPlanResponse:
    """Response schema for a public subscription plan.

    Attributes:
        id (str): Subscription plan ID
        name (str): Human-readable plan name
        price_usd (str): Monthly price in USD
        billing_interval (str): Billing interval
        is_purchasable (bool): Whether the plan can be purchased through checkout
        entitlements (BillingPlanEntitlementsResponse): Plan entitlements exposed by the billing plans endpoint.
        tagline (None | str | Unset): Short plan description
    """

    id: str
    name: str
    price_usd: str
    billing_interval: str
    is_purchasable: bool
    entitlements: BillingPlanEntitlementsResponse
    tagline: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.billing_plan_entitlements_response import (
            BillingPlanEntitlementsResponse,
        )  # noqa: PLC0415

        id = self.id

        name = self.name

        price_usd = self.price_usd

        billing_interval = self.billing_interval

        is_purchasable = self.is_purchasable

        entitlements = self.entitlements.to_dict()

        tagline: None | str | Unset
        if isinstance(self.tagline, Unset):
            tagline = UNSET
        else:
            tagline = self.tagline

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "price_usd": price_usd,
                "billing_interval": billing_interval,
                "is_purchasable": is_purchasable,
                "entitlements": entitlements,
            }
        )
        if tagline is not UNSET:
            field_dict["tagline"] = tagline

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.billing_plan_entitlements_response import (
            BillingPlanEntitlementsResponse,
        )  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        price_usd = d.pop("price_usd")

        billing_interval = d.pop("billing_interval")

        is_purchasable = d.pop("is_purchasable")

        entitlements = BillingPlanEntitlementsResponse.from_dict(d.pop("entitlements"))

        def _parse_tagline(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tagline = _parse_tagline(d.pop("tagline", UNSET))

        subscription_plan_response = cls(
            id=id,
            name=name,
            price_usd=price_usd,
            billing_interval=billing_interval,
            is_purchasable=is_purchasable,
            entitlements=entitlements,
            tagline=tagline,
        )

        subscription_plan_response.additional_properties = d
        return subscription_plan_response

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

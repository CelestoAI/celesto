from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.customer_organization_analytics import CustomerOrganizationAnalytics


T = TypeVar("T", bound="CustomerAnalytics")


@_attrs_define
class CustomerAnalytics:
    """
    Attributes:
        observed_at (datetime.datetime):
        user_id (str):
        email (str):
        organizations (list[CustomerOrganizationAnalytics]):
    """

    observed_at: datetime.datetime
    user_id: str
    email: str
    organizations: list[CustomerOrganizationAnalytics]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.customer_organization_analytics import (
            CustomerOrganizationAnalytics,
        )  # noqa: PLC0415

        observed_at = self.observed_at.isoformat()

        user_id = self.user_id

        email = self.email

        organizations = []
        for organizations_item_data in self.organizations:
            organizations_item = organizations_item_data.to_dict()
            organizations.append(organizations_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "observed_at": observed_at,
                "user_id": user_id,
                "email": email,
                "organizations": organizations,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.customer_organization_analytics import (
            CustomerOrganizationAnalytics,
        )  # noqa: PLC0415

        d = dict(src_dict)
        observed_at = datetime.datetime.fromisoformat(d.pop("observed_at"))

        user_id = d.pop("user_id")

        email = d.pop("email")

        organizations = []
        _organizations = d.pop("organizations")
        for organizations_item_data in _organizations:
            organizations_item = CustomerOrganizationAnalytics.from_dict(
                organizations_item_data
            )

            organizations.append(organizations_item)

        customer_analytics = cls(
            observed_at=observed_at,
            user_id=user_id,
            email=email,
            organizations=organizations,
        )

        customer_analytics.additional_properties = d
        return customer_analytics

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

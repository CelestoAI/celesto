from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="UpgradeResponse")


@_attrs_define
class UpgradeResponse:
    """Response schema for subscription upgrade.

    Attributes:
        status (str): Upgrade status
        checkout_url (None | str | Unset): Autumn checkout or confirmation URL when payment confirmation is required
        plan_id (None | str | Unset): Target plan ID
    """

    status: str
    checkout_url: None | str | Unset = UNSET
    plan_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        checkout_url: None | str | Unset
        if isinstance(self.checkout_url, Unset):
            checkout_url = UNSET
        else:
            checkout_url = self.checkout_url

        plan_id: None | str | Unset
        if isinstance(self.plan_id, Unset):
            plan_id = UNSET
        else:
            plan_id = self.plan_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "status": status,
            }
        )
        if checkout_url is not UNSET:
            field_dict["checkout_url"] = checkout_url
        if plan_id is not UNSET:
            field_dict["plan_id"] = plan_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        status = d.pop("status")

        def _parse_checkout_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        checkout_url = _parse_checkout_url(d.pop("checkout_url", UNSET))

        def _parse_plan_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        plan_id = _parse_plan_id(d.pop("plan_id", UNSET))

        upgrade_response = cls(
            status=status,
            checkout_url=checkout_url,
            plan_id=plan_id,
        )

        upgrade_response.additional_properties = d
        return upgrade_response

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="RuntimeSettingsResponse")


@_attrs_define
class RuntimeSettingsResponse:
    """
    Attributes:
        organization_id (str):
        default_end_user_budget_usd (None | str | Unset):
    """

    organization_id: str
    default_end_user_budget_usd: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        organization_id = self.organization_id

        default_end_user_budget_usd: None | str | Unset
        if isinstance(self.default_end_user_budget_usd, Unset):
            default_end_user_budget_usd = UNSET
        else:
            default_end_user_budget_usd = self.default_end_user_budget_usd

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "organization_id": organization_id,
            }
        )
        if default_end_user_budget_usd is not UNSET:
            field_dict["default_end_user_budget_usd"] = default_end_user_budget_usd

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        organization_id = d.pop("organization_id")

        def _parse_default_end_user_budget_usd(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        default_end_user_budget_usd = _parse_default_end_user_budget_usd(
            d.pop("default_end_user_budget_usd", UNSET)
        )

        runtime_settings_response = cls(
            organization_id=organization_id,
            default_end_user_budget_usd=default_end_user_budget_usd,
        )

        runtime_settings_response.additional_properties = d
        return runtime_settings_response

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

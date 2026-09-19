from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.sandbox_hours_overage_response import SandboxHoursOverageResponse


T = TypeVar("T", bound="SandboxHoursEntitlementResponse")


@_attrs_define
class SandboxHoursEntitlementResponse:
    """Included active sandbox hours and optional overage pricing.

    Attributes:
        included (str): Included sandbox hours (-1 = unlimited)
        unlimited (bool): Whether active sandbox hours are unlimited
        overage (None | SandboxHoursOverageResponse | Unset): Price after included hours are exhausted
    """

    included: str
    unlimited: bool
    overage: None | SandboxHoursOverageResponse | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.sandbox_hours_overage_response import SandboxHoursOverageResponse  # noqa: PLC0415

        included = self.included

        unlimited = self.unlimited

        overage: dict[str, Any] | None | Unset
        if isinstance(self.overage, Unset):
            overage = UNSET
        elif isinstance(self.overage, SandboxHoursOverageResponse):
            overage = self.overage.to_dict()
        else:
            overage = self.overage

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "included": included,
                "unlimited": unlimited,
            }
        )
        if overage is not UNSET:
            field_dict["overage"] = overage

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sandbox_hours_overage_response import SandboxHoursOverageResponse  # noqa: PLC0415

        d = dict(src_dict)
        included = d.pop("included")

        unlimited = d.pop("unlimited")

        def _parse_overage(data: object) -> None | SandboxHoursOverageResponse | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                overage_type_0 = SandboxHoursOverageResponse.from_dict(data)

                return overage_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | SandboxHoursOverageResponse | Unset, data)

        overage = _parse_overage(d.pop("overage", UNSET))

        sandbox_hours_entitlement_response = cls(
            included=included,
            unlimited=unlimited,
            overage=overage,
        )

        sandbox_hours_entitlement_response.additional_properties = d
        return sandbox_hours_entitlement_response

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

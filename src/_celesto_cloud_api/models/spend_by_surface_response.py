from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.spend_by_surface_response_surface import SpendBySurfaceResponseSurface


T = TypeVar("T", bound="SpendBySurfaceResponse")


@_attrs_define
class SpendBySurfaceResponse:
    """
    Attributes:
        surface (SpendBySurfaceResponseSurface):
        seconds (int):
        estimated_cost_usd (str):
    """

    surface: SpendBySurfaceResponseSurface
    seconds: int
    estimated_cost_usd: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        surface = self.surface.value

        seconds = self.seconds

        estimated_cost_usd = self.estimated_cost_usd

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "surface": surface,
                "seconds": seconds,
                "estimated_cost_usd": estimated_cost_usd,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        surface = SpendBySurfaceResponseSurface(d.pop("surface"))

        seconds = d.pop("seconds")

        estimated_cost_usd = d.pop("estimated_cost_usd")

        spend_by_surface_response = cls(
            surface=surface,
            seconds=seconds,
            estimated_cost_usd=estimated_cost_usd,
        )

        spend_by_surface_response.additional_properties = d
        return spend_by_surface_response

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

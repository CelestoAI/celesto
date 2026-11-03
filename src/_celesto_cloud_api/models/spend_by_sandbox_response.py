from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.spend_by_sandbox_response_surface import SpendBySandboxResponseSurface
from typing import cast
import datetime


T = TypeVar("T", bound="SpendBySandboxResponse")


@_attrs_define
class SpendBySandboxResponse:
    """
    Attributes:
        computer_id (str):
        name (str):
        surface (SpendBySandboxResponseSurface):
        seconds (int):
        estimated_cost_usd (str):
        last_day (datetime.date): Last UTC day in the range this sandbox ran
        deleted (bool):
    """

    computer_id: str
    name: str
    surface: SpendBySandboxResponseSurface
    seconds: int
    estimated_cost_usd: str
    last_day: datetime.date
    deleted: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        computer_id = self.computer_id

        name = self.name

        surface = self.surface.value

        seconds = self.seconds

        estimated_cost_usd = self.estimated_cost_usd

        last_day = self.last_day.isoformat()

        deleted = self.deleted

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "computer_id": computer_id,
                "name": name,
                "surface": surface,
                "seconds": seconds,
                "estimated_cost_usd": estimated_cost_usd,
                "last_day": last_day,
                "deleted": deleted,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        computer_id = d.pop("computer_id")

        name = d.pop("name")

        surface = SpendBySandboxResponseSurface(d.pop("surface"))

        seconds = d.pop("seconds")

        estimated_cost_usd = d.pop("estimated_cost_usd")

        last_day = datetime.date.fromisoformat(d.pop("last_day"))

        deleted = d.pop("deleted")

        spend_by_sandbox_response = cls(
            computer_id=computer_id,
            name=name,
            surface=surface,
            seconds=seconds,
            estimated_cost_usd=estimated_cost_usd,
            last_day=last_day,
            deleted=deleted,
        )

        spend_by_sandbox_response.additional_properties = d
        return spend_by_sandbox_response

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

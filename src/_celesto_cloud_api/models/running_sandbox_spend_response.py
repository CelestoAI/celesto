from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.running_sandbox_spend_response_surface import (
    RunningSandboxSpendResponseSurface,
)
from typing import cast
import datetime


T = TypeVar("T", bound="RunningSandboxSpendResponse")


@_attrs_define
class RunningSandboxSpendResponse:
    """A sandbox charging right now: its rate and its spend since it last started.

    Informational only: never add it to the period totals. Its checkpointed
    seconds are already in them, and the totals (cached) and this (live) are
    read at different moments, so no sum of the two is exact.

        Attributes:
            computer_id (str):
            name (str):
            surface (RunningSandboxSpendResponseSurface):
            size_id (str):
            started_at (datetime.datetime):
            hourly_cost_usd (str):
            accrued_cost_usd (str):
    """

    computer_id: str
    name: str
    surface: RunningSandboxSpendResponseSurface
    size_id: str
    started_at: datetime.datetime
    hourly_cost_usd: str
    accrued_cost_usd: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        computer_id = self.computer_id

        name = self.name

        surface = self.surface.value

        size_id = self.size_id

        started_at = self.started_at.isoformat()

        hourly_cost_usd = self.hourly_cost_usd

        accrued_cost_usd = self.accrued_cost_usd

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "computer_id": computer_id,
                "name": name,
                "surface": surface,
                "size_id": size_id,
                "started_at": started_at,
                "hourly_cost_usd": hourly_cost_usd,
                "accrued_cost_usd": accrued_cost_usd,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        computer_id = d.pop("computer_id")

        name = d.pop("name")

        surface = RunningSandboxSpendResponseSurface(d.pop("surface"))

        size_id = d.pop("size_id")

        started_at = datetime.datetime.fromisoformat(d.pop("started_at"))

        hourly_cost_usd = d.pop("hourly_cost_usd")

        accrued_cost_usd = d.pop("accrued_cost_usd")

        running_sandbox_spend_response = cls(
            computer_id=computer_id,
            name=name,
            surface=surface,
            size_id=size_id,
            started_at=started_at,
            hourly_cost_usd=hourly_cost_usd,
            accrued_cost_usd=accrued_cost_usd,
        )

        running_sandbox_spend_response.additional_properties = d
        return running_sandbox_spend_response

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.sandbox_activity_window_days import SandboxActivityWindowDays


T = TypeVar("T", bound="SandboxActivityWindow")


@_attrs_define
class SandboxActivityWindow:
    """
    Attributes:
        days (SandboxActivityWindowDays):
        sandboxes_created (int):
        total_running_seconds (float):
    """

    days: SandboxActivityWindowDays
    sandboxes_created: int
    total_running_seconds: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        days = self.days.value

        sandboxes_created = self.sandboxes_created

        total_running_seconds = self.total_running_seconds

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "days": days,
                "sandboxes_created": sandboxes_created,
                "total_running_seconds": total_running_seconds,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        days = SandboxActivityWindowDays(d.pop("days"))

        sandboxes_created = d.pop("sandboxes_created")

        total_running_seconds = d.pop("total_running_seconds")

        sandbox_activity_window = cls(
            days=days,
            sandboxes_created=sandboxes_created,
            total_running_seconds=total_running_seconds,
        )

        sandbox_activity_window.additional_properties = d
        return sandbox_activity_window

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

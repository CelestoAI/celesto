from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset


T = TypeVar("T", bound="ComputerCounts")


@_attrs_define
class ComputerCounts:
    """
    Attributes:
        running (int | Unset):  Default: 0.
        stopped (int | Unset):  Default: 0.
        transitioning (int | Unset):  Default: 0.
        lost (int | Unset):  Default: 0.
    """

    running: int | Unset = 0
    stopped: int | Unset = 0
    transitioning: int | Unset = 0
    lost: int | Unset = 0
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        running = self.running

        stopped = self.stopped

        transitioning = self.transitioning

        lost = self.lost

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if running is not UNSET:
            field_dict["running"] = running
        if stopped is not UNSET:
            field_dict["stopped"] = stopped
        if transitioning is not UNSET:
            field_dict["transitioning"] = transitioning
        if lost is not UNSET:
            field_dict["lost"] = lost

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        running = d.pop("running", UNSET)

        stopped = d.pop("stopped", UNSET)

        transitioning = d.pop("transitioning", UNSET)

        lost = d.pop("lost", UNSET)

        computer_counts = cls(
            running=running,
            stopped=stopped,
            transitioning=transitioning,
            lost=lost,
        )

        computer_counts.additional_properties = d
        return computer_counts

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.sandbox_activity_window import SandboxActivityWindow


T = TypeVar("T", bound="SandboxActivity")


@_attrs_define
class SandboxActivity:
    """
    Attributes:
        observed_at (datetime.datetime):
        windows (list[SandboxActivityWindow]):
    """

    observed_at: datetime.datetime
    windows: list[SandboxActivityWindow]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.sandbox_activity_window import SandboxActivityWindow  # noqa: PLC0415

        observed_at = self.observed_at.isoformat()

        windows = []
        for windows_item_data in self.windows:
            windows_item = windows_item_data.to_dict()
            windows.append(windows_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "observed_at": observed_at,
                "windows": windows,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sandbox_activity_window import SandboxActivityWindow  # noqa: PLC0415

        d = dict(src_dict)
        observed_at = datetime.datetime.fromisoformat(d.pop("observed_at"))

        windows = []
        _windows = d.pop("windows")
        for windows_item_data in _windows:
            windows_item = SandboxActivityWindow.from_dict(windows_item_data)

            windows.append(windows_item)

        sandbox_activity = cls(
            observed_at=observed_at,
            windows=windows,
        )

        sandbox_activity.additional_properties = d
        return sandbox_activity

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.attribution_touch import AttributionTouch


T = TypeVar("T", bound="AttributionUpdate")


@_attrs_define
class AttributionUpdate:
    """
    Attributes:
        first_touch (AttributionTouch | None | Unset):
        latest_touch (AttributionTouch | None | Unset):
    """

    first_touch: AttributionTouch | None | Unset = UNSET
    latest_touch: AttributionTouch | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.attribution_touch import AttributionTouch  # noqa: PLC0415

        first_touch: dict[str, Any] | None | Unset
        if isinstance(self.first_touch, Unset):
            first_touch = UNSET
        elif isinstance(self.first_touch, AttributionTouch):
            first_touch = self.first_touch.to_dict()
        else:
            first_touch = self.first_touch

        latest_touch: dict[str, Any] | None | Unset
        if isinstance(self.latest_touch, Unset):
            latest_touch = UNSET
        elif isinstance(self.latest_touch, AttributionTouch):
            latest_touch = self.latest_touch.to_dict()
        else:
            latest_touch = self.latest_touch

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if first_touch is not UNSET:
            field_dict["first_touch"] = first_touch
        if latest_touch is not UNSET:
            field_dict["latest_touch"] = latest_touch

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.attribution_touch import AttributionTouch  # noqa: PLC0415

        d = dict(src_dict)

        def _parse_first_touch(data: object) -> AttributionTouch | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                first_touch_type_0 = AttributionTouch.from_dict(data)

                return first_touch_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AttributionTouch | None | Unset, data)

        first_touch = _parse_first_touch(d.pop("first_touch", UNSET))

        def _parse_latest_touch(data: object) -> AttributionTouch | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                latest_touch_type_0 = AttributionTouch.from_dict(data)

                return latest_touch_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AttributionTouch | None | Unset, data)

        latest_touch = _parse_latest_touch(d.pop("latest_touch", UNSET))

        attribution_update = cls(
            first_touch=first_touch,
            latest_touch=latest_touch,
        )

        return attribution_update

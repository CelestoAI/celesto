from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from uuid import UUID


T = TypeVar("T", bound="HostPlacement")


@_attrs_define
class HostPlacement:
    """
    Attributes:
        host_id (UUID):
        state_id (UUID):
    """

    host_id: UUID
    state_id: UUID

    def to_dict(self) -> dict[str, Any]:
        host_id = str(self.host_id)

        state_id = str(self.state_id)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "host_id": host_id,
                "state_id": state_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        host_id = UUID(d.pop("host_id"))

        state_id = UUID(d.pop("state_id"))

        host_placement = cls(
            host_id=host_id,
            state_id=state_id,
        )

        return host_placement

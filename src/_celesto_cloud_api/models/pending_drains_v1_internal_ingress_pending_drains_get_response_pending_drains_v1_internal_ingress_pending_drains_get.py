from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset


T = TypeVar(
    "T",
    bound="PendingDrainsV1InternalIngressPendingDrainsGetResponsePendingDrainsV1InternalIngressPendingDrainsGet",
)


@_attrs_define
class PendingDrainsV1InternalIngressPendingDrainsGetResponsePendingDrainsV1InternalIngressPendingDrainsGet:
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        pending_drains_v1_internal_ingress_pending_drains_get_response_pending_drains_v1_internal_ingress_pending_drains_get = cls()

        pending_drains_v1_internal_ingress_pending_drains_get_response_pending_drains_v1_internal_ingress_pending_drains_get.additional_properties = d
        return pending_drains_v1_internal_ingress_pending_drains_get_response_pending_drains_v1_internal_ingress_pending_drains_get

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

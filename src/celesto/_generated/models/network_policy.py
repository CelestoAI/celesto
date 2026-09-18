from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.network_policy_mode import NetworkPolicyMode
from ..types import UNSET, Unset


T = TypeVar("T", bound="NetworkPolicy")


@_attrs_define
class NetworkPolicy:
    """Outbound internet access, fixed for the lifetime of a computer.

    Attributes:
        mode (NetworkPolicyMode | Unset):  Default: NetworkPolicyMode.OPEN.
    """

    mode: NetworkPolicyMode | Unset = NetworkPolicyMode.OPEN

    def to_dict(self) -> dict[str, Any]:
        mode: str | Unset = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if mode is not UNSET:
            field_dict["mode"] = mode

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _mode = d.pop("mode", UNSET)
        mode: NetworkPolicyMode | Unset
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = NetworkPolicyMode(_mode)

        network_policy = cls(
            mode=mode,
        )

        return network_policy

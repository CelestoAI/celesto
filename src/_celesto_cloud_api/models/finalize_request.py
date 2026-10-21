from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset


T = TypeVar("T", bound="FinalizeRequest")


@_attrs_define
class FinalizeRequest:
    """
    Attributes:
        key (str | Unset):  Default: ''.
        version (str | Unset):  Default: ''.
        size_bytes (int | Unset):  Default: 0.
    """

    key: str | Unset = ""
    version: str | Unset = ""
    size_bytes: int | Unset = 0
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        key = self.key

        version = self.version

        size_bytes = self.size_bytes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if key is not UNSET:
            field_dict["key"] = key
        if version is not UNSET:
            field_dict["version"] = version
        if size_bytes is not UNSET:
            field_dict["size_bytes"] = size_bytes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        key = d.pop("key", UNSET)

        version = d.pop("version", UNSET)

        size_bytes = d.pop("size_bytes", UNSET)

        finalize_request = cls(
            key=key,
            version=version,
            size_bytes=size_bytes,
        )

        finalize_request.additional_properties = d
        return finalize_request

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

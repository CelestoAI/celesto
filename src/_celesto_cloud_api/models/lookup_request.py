from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="LookupRequest")


@_attrs_define
class LookupRequest:
    """
    Attributes:
        key (str | Unset):  Default: ''.
        version (str | Unset):  Default: ''.
        restore_keys (list[str] | Unset):
    """

    key: str | Unset = ""
    version: str | Unset = ""
    restore_keys: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        key = self.key

        version = self.version

        restore_keys: list[str] | Unset = UNSET
        if not isinstance(self.restore_keys, Unset):
            restore_keys = self.restore_keys

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if key is not UNSET:
            field_dict["key"] = key
        if version is not UNSET:
            field_dict["version"] = version
        if restore_keys is not UNSET:
            field_dict["restore_keys"] = restore_keys

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        key = d.pop("key", UNSET)

        version = d.pop("version", UNSET)

        restore_keys = cast(list[str], d.pop("restore_keys", UNSET))

        lookup_request = cls(
            key=key,
            version=version,
            restore_keys=restore_keys,
        )

        lookup_request.additional_properties = d
        return lookup_request

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

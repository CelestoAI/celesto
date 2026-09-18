from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="DriveAccessRulesResponse")


@_attrs_define
class DriveAccessRulesResponse:
    """Response for access rules.

    Attributes:
        unrestricted (bool): True if no rules configured (full access to all files)
        version (str | Unset):  Default: '1'.
        allowed_folders (list[str] | Unset):
        allowed_files (list[str] | Unset):
    """

    unrestricted: bool
    version: str | Unset = "1"
    allowed_folders: list[str] | Unset = UNSET
    allowed_files: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        unrestricted = self.unrestricted

        version = self.version

        allowed_folders: list[str] | Unset = UNSET
        if not isinstance(self.allowed_folders, Unset):
            allowed_folders = self.allowed_folders

        allowed_files: list[str] | Unset = UNSET
        if not isinstance(self.allowed_files, Unset):
            allowed_files = self.allowed_files

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "unrestricted": unrestricted,
            }
        )
        if version is not UNSET:
            field_dict["version"] = version
        if allowed_folders is not UNSET:
            field_dict["allowed_folders"] = allowed_folders
        if allowed_files is not UNSET:
            field_dict["allowed_files"] = allowed_files

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        unrestricted = d.pop("unrestricted")

        version = d.pop("version", UNSET)

        allowed_folders = cast(list[str], d.pop("allowed_folders", UNSET))

        allowed_files = cast(list[str], d.pop("allowed_files", UNSET))

        drive_access_rules_response = cls(
            unrestricted=unrestricted,
            version=version,
            allowed_folders=allowed_folders,
            allowed_files=allowed_files,
        )

        drive_access_rules_response.additional_properties = d
        return drive_access_rules_response

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset


T = TypeVar("T", bound="GitHubRepositoryPermissions")


@_attrs_define
class GitHubRepositoryPermissions:
    """
    Attributes:
        pull (bool | Unset):  Default: False.
        push (bool | Unset):  Default: False.
        admin (bool | Unset):  Default: False.
    """

    pull: bool | Unset = False
    push: bool | Unset = False
    admin: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        pull = self.pull

        push = self.push

        admin = self.admin

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if pull is not UNSET:
            field_dict["pull"] = pull
        if push is not UNSET:
            field_dict["push"] = push
        if admin is not UNSET:
            field_dict["admin"] = admin

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        pull = d.pop("pull", UNSET)

        push = d.pop("push", UNSET)

        admin = d.pop("admin", UNSET)

        git_hub_repository_permissions = cls(
            pull=pull,
            push=push,
            admin=admin,
        )

        git_hub_repository_permissions.additional_properties = d
        return git_hub_repository_permissions

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

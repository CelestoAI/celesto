from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.git_hub_repository_permissions import GitHubRepositoryPermissions


T = TypeVar("T", bound="GitHubRepositoryResponse")


@_attrs_define
class GitHubRepositoryResponse:
    """
    Attributes:
        id (int):
        name (str):
        full_name (str):
        private (bool):
        html_url (str):
        default_branch (None | str | Unset):
        updated_at (None | str | Unset):
        permissions (GitHubRepositoryPermissions | Unset):
    """

    id: int
    name: str
    full_name: str
    private: bool
    html_url: str
    default_branch: None | str | Unset = UNSET
    updated_at: None | str | Unset = UNSET
    permissions: GitHubRepositoryPermissions | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.git_hub_repository_permissions import GitHubRepositoryPermissions  # noqa: PLC0415

        id = self.id

        name = self.name

        full_name = self.full_name

        private = self.private

        html_url = self.html_url

        default_branch: None | str | Unset
        if isinstance(self.default_branch, Unset):
            default_branch = UNSET
        else:
            default_branch = self.default_branch

        updated_at: None | str | Unset
        if isinstance(self.updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = self.updated_at

        permissions: dict[str, Any] | Unset = UNSET
        if not isinstance(self.permissions, Unset):
            permissions = self.permissions.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "full_name": full_name,
                "private": private,
                "html_url": html_url,
            }
        )
        if default_branch is not UNSET:
            field_dict["default_branch"] = default_branch
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if permissions is not UNSET:
            field_dict["permissions"] = permissions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.git_hub_repository_permissions import GitHubRepositoryPermissions  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        full_name = d.pop("full_name")

        private = d.pop("private")

        html_url = d.pop("html_url")

        def _parse_default_branch(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        default_branch = _parse_default_branch(d.pop("default_branch", UNSET))

        def _parse_updated_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        updated_at = _parse_updated_at(d.pop("updated_at", UNSET))

        _permissions = d.pop("permissions", UNSET)
        permissions: GitHubRepositoryPermissions | Unset
        if isinstance(_permissions, Unset):
            permissions = UNSET
        else:
            permissions = GitHubRepositoryPermissions.from_dict(_permissions)

        git_hub_repository_response = cls(
            id=id,
            name=name,
            full_name=full_name,
            private=private,
            html_url=html_url,
            default_branch=default_branch,
            updated_at=updated_at,
            permissions=permissions,
        )

        git_hub_repository_response.additional_properties = d
        return git_hub_repository_response

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

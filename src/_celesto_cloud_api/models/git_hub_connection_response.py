from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="GitHubConnectionResponse")


@_attrs_define
class GitHubConnectionResponse:
    """
    Attributes:
        id (str):
        github_user_id (str):
        github_login (str):
        connected_at (str):
        updated_at (str):
        scopes (list[str] | Unset):
        last_used_at (None | str | Unset):
    """

    id: str
    github_user_id: str
    github_login: str
    connected_at: str
    updated_at: str
    scopes: list[str] | Unset = UNSET
    last_used_at: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        github_user_id = self.github_user_id

        github_login = self.github_login

        connected_at = self.connected_at

        updated_at = self.updated_at

        scopes: list[str] | Unset = UNSET
        if not isinstance(self.scopes, Unset):
            scopes = self.scopes

        last_used_at: None | str | Unset
        if isinstance(self.last_used_at, Unset):
            last_used_at = UNSET
        else:
            last_used_at = self.last_used_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "github_user_id": github_user_id,
                "github_login": github_login,
                "connected_at": connected_at,
                "updated_at": updated_at,
            }
        )
        if scopes is not UNSET:
            field_dict["scopes"] = scopes
        if last_used_at is not UNSET:
            field_dict["last_used_at"] = last_used_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        github_user_id = d.pop("github_user_id")

        github_login = d.pop("github_login")

        connected_at = d.pop("connected_at")

        updated_at = d.pop("updated_at")

        scopes = cast(list[str], d.pop("scopes", UNSET))

        def _parse_last_used_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        last_used_at = _parse_last_used_at(d.pop("last_used_at", UNSET))

        git_hub_connection_response = cls(
            id=id,
            github_user_id=github_user_id,
            github_login=github_login,
            connected_at=connected_at,
            updated_at=updated_at,
            scopes=scopes,
            last_used_at=last_used_at,
        )

        git_hub_connection_response.additional_properties = d
        return git_hub_connection_response

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

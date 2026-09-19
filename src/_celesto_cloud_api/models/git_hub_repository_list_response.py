from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.git_hub_repository_response import GitHubRepositoryResponse


T = TypeVar("T", bound="GitHubRepositoryListResponse")


@_attrs_define
class GitHubRepositoryListResponse:
    """
    Attributes:
        repositories (list[GitHubRepositoryResponse]):
        page (int):
        per_page (int):
        has_next (bool | Unset):  Default: False.
    """

    repositories: list[GitHubRepositoryResponse]
    page: int
    per_page: int
    has_next: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.git_hub_repository_response import GitHubRepositoryResponse  # noqa: PLC0415

        repositories = []
        for repositories_item_data in self.repositories:
            repositories_item = repositories_item_data.to_dict()
            repositories.append(repositories_item)

        page = self.page

        per_page = self.per_page

        has_next = self.has_next

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "repositories": repositories,
                "page": page,
                "per_page": per_page,
            }
        )
        if has_next is not UNSET:
            field_dict["has_next"] = has_next

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.git_hub_repository_response import GitHubRepositoryResponse  # noqa: PLC0415

        d = dict(src_dict)
        repositories = []
        _repositories = d.pop("repositories")
        for repositories_item_data in _repositories:
            repositories_item = GitHubRepositoryResponse.from_dict(
                repositories_item_data
            )

            repositories.append(repositories_item)

        page = d.pop("page")

        per_page = d.pop("per_page")

        has_next = d.pop("has_next", UNSET)

        git_hub_repository_list_response = cls(
            repositories=repositories,
            page=page,
            per_page=per_page,
            has_next=has_next,
        )

        git_hub_repository_list_response.additional_properties = d
        return git_hub_repository_list_response

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

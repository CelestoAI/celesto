from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset


T = TypeVar(
    "T",
    bound="CommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPostResponseCommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPost",
)


@_attrs_define
class CommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPostResponseCommitBlocksV1IntegrationsGithubActionsCacheCelestoCommitBlocksPost:
    additional_properties: dict[str, bool] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        commit_blocks_v1_integrations_github_actions_cache_celesto_commit_blocks_post_response_commit_blocks_v1_integrations_github_actions_cache_celesto_commit_blocks_post = cls()

        commit_blocks_v1_integrations_github_actions_cache_celesto_commit_blocks_post_response_commit_blocks_v1_integrations_github_actions_cache_celesto_commit_blocks_post.additional_properties = d
        return commit_blocks_v1_integrations_github_actions_cache_celesto_commit_blocks_post_response_commit_blocks_v1_integrations_github_actions_cache_celesto_commit_blocks_post

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> bool:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: bool) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties

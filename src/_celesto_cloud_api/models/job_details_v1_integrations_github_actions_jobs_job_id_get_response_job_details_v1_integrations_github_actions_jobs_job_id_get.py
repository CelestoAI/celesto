from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset


T = TypeVar(
    "T",
    bound="JobDetailsV1IntegrationsGithubActionsJobsJobIdGetResponseJobDetailsV1IntegrationsGithubActionsJobsJobIdGet",
)


@_attrs_define
class JobDetailsV1IntegrationsGithubActionsJobsJobIdGetResponseJobDetailsV1IntegrationsGithubActionsJobsJobIdGet:
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        job_details_v1_integrations_github_actions_jobs_job_id_get_response_job_details_v1_integrations_github_actions_jobs_job_id_get = cls()

        job_details_v1_integrations_github_actions_jobs_job_id_get_response_job_details_v1_integrations_github_actions_jobs_job_id_get.additional_properties = d
        return job_details_v1_integrations_github_actions_jobs_job_id_get_response_job_details_v1_integrations_github_actions_jobs_job_id_get

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

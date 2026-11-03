from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset


T = TypeVar(
    "T",
    bound="JobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGetResponseJobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGet",
)


@_attrs_define
class JobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGetResponseJobStepLogV1IntegrationsGithubActionsJobsJobIdStepsNumberLogGet:
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        job_step_log_v1_integrations_github_actions_jobs_job_id_steps_number_log_get_response_job_step_log_v1_integrations_github_actions_jobs_job_id_steps_number_log_get = cls()

        job_step_log_v1_integrations_github_actions_jobs_job_id_steps_number_log_get_response_job_step_log_v1_integrations_github_actions_jobs_job_id_steps_number_log_get.additional_properties = d
        return job_step_log_v1_integrations_github_actions_jobs_job_id_steps_number_log_get_response_job_step_log_v1_integrations_github_actions_jobs_job_id_steps_number_log_get

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.host_git_hub_runtime_config_response_github_integration_type_0 import (
        HostGitHubRuntimeConfigResponseGithubIntegrationType0,
    )


T = TypeVar("T", bound="HostGitHubRuntimeConfigResponse")


@_attrs_define
class HostGitHubRuntimeConfigResponse:
    """Same payload shape the push handoff sends; null when no active connection.

    Attributes:
        github_integration (HostGitHubRuntimeConfigResponseGithubIntegrationType0 | None | Unset):
    """

    github_integration: (
        HostGitHubRuntimeConfigResponseGithubIntegrationType0 | None | Unset
    ) = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.host_git_hub_runtime_config_response_github_integration_type_0 import (
            HostGitHubRuntimeConfigResponseGithubIntegrationType0,
        )  # noqa: PLC0415

        github_integration: dict[str, Any] | None | Unset
        if isinstance(self.github_integration, Unset):
            github_integration = UNSET
        elif isinstance(
            self.github_integration,
            HostGitHubRuntimeConfigResponseGithubIntegrationType0,
        ):
            github_integration = self.github_integration.to_dict()
        else:
            github_integration = self.github_integration

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if github_integration is not UNSET:
            field_dict["github_integration"] = github_integration

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.host_git_hub_runtime_config_response_github_integration_type_0 import (
            HostGitHubRuntimeConfigResponseGithubIntegrationType0,
        )  # noqa: PLC0415

        d = dict(src_dict)

        def _parse_github_integration(
            data: object,
        ) -> HostGitHubRuntimeConfigResponseGithubIntegrationType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                github_integration_type_0 = (
                    HostGitHubRuntimeConfigResponseGithubIntegrationType0.from_dict(
                        data
                    )
                )

                return github_integration_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                HostGitHubRuntimeConfigResponseGithubIntegrationType0 | None | Unset,
                data,
            )

        github_integration = _parse_github_integration(
            d.pop("github_integration", UNSET)
        )

        host_git_hub_runtime_config_response = cls(
            github_integration=github_integration,
        )

        host_git_hub_runtime_config_response.additional_properties = d
        return host_git_hub_runtime_config_response

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

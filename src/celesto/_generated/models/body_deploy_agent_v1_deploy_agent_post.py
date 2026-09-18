from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field
import json
from .. import types

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="BodyDeployAgentV1DeployAgentPost")


@_attrs_define
class BodyDeployAgentV1DeployAgentPost:
    """
    Attributes:
        code_bundle (str): Tar or zip archive containing the app source code
        name (str): Human-friendly application name
        project_id (str): Project ID to associate deployment with
        description (None | str | Unset): Optional description for the deployment
        config (None | str | Unset): Optional JSON string with deployment configuration (env vars, ports)
    """

    code_bundle: str
    name: str
    project_id: str
    description: None | str | Unset = UNSET
    config: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        code_bundle = self.code_bundle

        name = self.name

        project_id = self.project_id

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        config: None | str | Unset
        if isinstance(self.config, Unset):
            config = UNSET
        else:
            config = self.config

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "code_bundle": code_bundle,
                "name": name,
                "project_id": project_id,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if config is not UNSET:
            field_dict["config"] = config

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(
            ("code_bundle", (None, str(self.code_bundle).encode(), "text/plain"))
        )

        files.append(("name", (None, str(self.name).encode(), "text/plain")))

        files.append(
            ("project_id", (None, str(self.project_id).encode(), "text/plain"))
        )

        if not isinstance(self.description, Unset):
            if isinstance(self.description, str):
                files.append(
                    (
                        "description",
                        (None, str(self.description).encode(), "text/plain"),
                    )
                )
            else:
                files.append(
                    (
                        "description",
                        (None, str(self.description).encode(), "text/plain"),
                    )
                )

        if not isinstance(self.config, Unset):
            if isinstance(self.config, str):
                files.append(
                    ("config", (None, str(self.config).encode(), "text/plain"))
                )
            else:
                files.append(
                    ("config", (None, str(self.config).encode(), "text/plain"))
                )

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        code_bundle = d.pop("code_bundle")

        name = d.pop("name")

        project_id = d.pop("project_id")

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_config(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        config = _parse_config(d.pop("config", UNSET))

        body_deploy_agent_v1_deploy_agent_post = cls(
            code_bundle=code_bundle,
            name=name,
            project_id=project_id,
            description=description,
            config=config,
        )

        body_deploy_agent_v1_deploy_agent_post.additional_properties = d
        return body_deploy_agent_v1_deploy_agent_post

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

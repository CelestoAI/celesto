from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="HostGitHubRuntimeConfigRequest")


@_attrs_define
class HostGitHubRuntimeConfigRequest:
    """Host agent asks for a fresh github_integration config for one of its VMs.

    Attributes:
        host_boot_id (None | str | Unset):
    """

    host_boot_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        host_boot_id: None | str | Unset
        if isinstance(self.host_boot_id, Unset):
            host_boot_id = UNSET
        else:
            host_boot_id = self.host_boot_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if host_boot_id is not UNSET:
            field_dict["host_boot_id"] = host_boot_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_host_boot_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        host_boot_id = _parse_host_boot_id(d.pop("host_boot_id", UNSET))

        host_git_hub_runtime_config_request = cls(
            host_boot_id=host_boot_id,
        )

        host_git_hub_runtime_config_request.additional_properties = d
        return host_git_hub_runtime_config_request

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

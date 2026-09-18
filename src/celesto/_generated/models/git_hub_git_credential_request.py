from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset


T = TypeVar("T", bound="GitHubGitCredentialRequest")


@_attrs_define
class GitHubGitCredentialRequest:
    """
    Attributes:
        protocol (str | Unset):  Default: 'https'.
        host (str | Unset):  Default: 'github.com'.
    """

    protocol: str | Unset = "https"
    host: str | Unset = "github.com"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        protocol = self.protocol

        host = self.host

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if protocol is not UNSET:
            field_dict["protocol"] = protocol
        if host is not UNSET:
            field_dict["host"] = host

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        protocol = d.pop("protocol", UNSET)

        host = d.pop("host", UNSET)

        git_hub_git_credential_request = cls(
            protocol=protocol,
            host=host,
        )

        git_hub_git_credential_request.additional_properties = d
        return git_hub_git_credential_request

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

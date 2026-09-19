from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="McpServerUpsertRequest")


@_attrs_define
class McpServerUpsertRequest:
    """Register or replace one of the tenant's own MCP servers.

    ``credential_provider`` names a provider in the credential store rather
    than carrying a secret, so the same server can authenticate as a different
    end user on every run. Leave it null for a server that needs no credential.

        Attributes:
            url (str):
            description (None | str | Unset):
            credential_provider (None | str | Unset):
            auth_header (str | Unset):  Default: 'Authorization'.
            auth_prefix (str | Unset):  Default: 'Bearer '.
    """

    url: str
    description: None | str | Unset = UNSET
    credential_provider: None | str | Unset = UNSET
    auth_header: str | Unset = "Authorization"
    auth_prefix: str | Unset = "Bearer "
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        url = self.url

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        credential_provider: None | str | Unset
        if isinstance(self.credential_provider, Unset):
            credential_provider = UNSET
        else:
            credential_provider = self.credential_provider

        auth_header = self.auth_header

        auth_prefix = self.auth_prefix

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "url": url,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if credential_provider is not UNSET:
            field_dict["credential_provider"] = credential_provider
        if auth_header is not UNSET:
            field_dict["auth_header"] = auth_header
        if auth_prefix is not UNSET:
            field_dict["auth_prefix"] = auth_prefix

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        url = d.pop("url")

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_credential_provider(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        credential_provider = _parse_credential_provider(
            d.pop("credential_provider", UNSET)
        )

        auth_header = d.pop("auth_header", UNSET)

        auth_prefix = d.pop("auth_prefix", UNSET)

        mcp_server_upsert_request = cls(
            url=url,
            description=description,
            credential_provider=credential_provider,
            auth_header=auth_header,
            auth_prefix=auth_prefix,
        )

        mcp_server_upsert_request.additional_properties = d
        return mcp_server_upsert_request

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

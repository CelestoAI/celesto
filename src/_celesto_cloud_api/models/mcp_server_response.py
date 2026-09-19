from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
import datetime


T = TypeVar("T", bound="McpServerResponse")


@_attrs_define
class McpServerResponse:
    """
    Attributes:
        id (str):
        slug (str):
        url (str):
        auth_header (str):
        auth_prefix (str):
        status (str):
        organization_id (str):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        object_ (str | Unset):  Default: 'mcp_server'.
        description (None | str | Unset):
        credential_provider (None | str | Unset):
    """

    id: str
    slug: str
    url: str
    auth_header: str
    auth_prefix: str
    status: str
    organization_id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    object_: str | Unset = "mcp_server"
    description: None | str | Unset = UNSET
    credential_provider: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        slug = self.slug

        url = self.url

        auth_header = self.auth_header

        auth_prefix = self.auth_prefix

        status = self.status

        organization_id = self.organization_id

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        object_ = self.object_

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

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "slug": slug,
                "url": url,
                "auth_header": auth_header,
                "auth_prefix": auth_prefix,
                "status": status,
                "organization_id": organization_id,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if object_ is not UNSET:
            field_dict["object"] = object_
        if description is not UNSET:
            field_dict["description"] = description
        if credential_provider is not UNSET:
            field_dict["credential_provider"] = credential_provider

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        slug = d.pop("slug")

        url = d.pop("url")

        auth_header = d.pop("auth_header")

        auth_prefix = d.pop("auth_prefix")

        status = d.pop("status")

        organization_id = d.pop("organization_id")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        object_ = d.pop("object", UNSET)

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

        mcp_server_response = cls(
            id=id,
            slug=slug,
            url=url,
            auth_header=auth_header,
            auth_prefix=auth_prefix,
            status=status,
            organization_id=organization_id,
            created_at=created_at,
            updated_at=updated_at,
            object_=object_,
            description=description,
            credential_provider=credential_provider,
        )

        mcp_server_response.additional_properties = d
        return mcp_server_response

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

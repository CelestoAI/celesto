from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="DelegatedAccessConnectResponse")


@_attrs_define
class DelegatedAccessConnectResponse:
    """Response from connect endpoint.

    Attributes:
        status (str): 'redirect' if OAuth needed, 'connected' if already exists
        oauth_url (None | str | Unset): OAuth URL to redirect user to (if status='redirect')
        connection_id (None | str | Unset): Connection ID (if status='connected')
    """

    status: str
    oauth_url: None | str | Unset = UNSET
    connection_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status

        oauth_url: None | str | Unset
        if isinstance(self.oauth_url, Unset):
            oauth_url = UNSET
        else:
            oauth_url = self.oauth_url

        connection_id: None | str | Unset
        if isinstance(self.connection_id, Unset):
            connection_id = UNSET
        else:
            connection_id = self.connection_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "status": status,
            }
        )
        if oauth_url is not UNSET:
            field_dict["oauth_url"] = oauth_url
        if connection_id is not UNSET:
            field_dict["connection_id"] = connection_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        status = d.pop("status")

        def _parse_oauth_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        oauth_url = _parse_oauth_url(d.pop("oauth_url", UNSET))

        def _parse_connection_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        connection_id = _parse_connection_id(d.pop("connection_id", UNSET))

        delegated_access_connect_response = cls(
            status=status,
            oauth_url=oauth_url,
            connection_id=connection_id,
        )

        delegated_access_connect_response.additional_properties = d
        return delegated_access_connect_response

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

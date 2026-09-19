from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="DelegatedAccessConnectRequest")


@_attrs_define
class DelegatedAccessConnectRequest:
    """Request to initiate OAuth flow for a subject.

    Attributes:
        subject (str): Unique identifier for the end-user
        provider (str): Provider key (e.g., google_drive)
        project_name (str): Project name to scope the access
        redirect_uri (None | str | Unset): Optional custom redirect URI after OAuth completion
    """

    subject: str
    provider: str
    project_name: str
    redirect_uri: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        subject = self.subject

        provider = self.provider

        project_name = self.project_name

        redirect_uri: None | str | Unset
        if isinstance(self.redirect_uri, Unset):
            redirect_uri = UNSET
        else:
            redirect_uri = self.redirect_uri

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "subject": subject,
                "provider": provider,
                "project_name": project_name,
            }
        )
        if redirect_uri is not UNSET:
            field_dict["redirect_uri"] = redirect_uri

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        subject = d.pop("subject")

        provider = d.pop("provider")

        project_name = d.pop("project_name")

        def _parse_redirect_uri(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        redirect_uri = _parse_redirect_uri(d.pop("redirect_uri", UNSET))

        delegated_access_connect_request = cls(
            subject=subject,
            provider=provider,
            project_name=project_name,
            redirect_uri=redirect_uri,
        )

        delegated_access_connect_request.additional_properties = d
        return delegated_access_connect_request

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

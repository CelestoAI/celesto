from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
import datetime


T = TypeVar("T", bound="CredentialResponse")


@_attrs_define
class CredentialResponse:
    """
    Attributes:
        provider (str):
        auth_type (str):
        status (str):
        scope (str):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        object_ (str | Unset):  Default: 'credential'.
        secret_hint (None | str | Unset):
        expires_at (datetime.datetime | None | Unset):
        scopes (list[str] | None | Unset):
        account_label (None | str | Unset):
    """

    provider: str
    auth_type: str
    status: str
    scope: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    object_: str | Unset = "credential"
    secret_hint: None | str | Unset = UNSET
    expires_at: datetime.datetime | None | Unset = UNSET
    scopes: list[str] | None | Unset = UNSET
    account_label: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        provider = self.provider

        auth_type = self.auth_type

        status = self.status

        scope = self.scope

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        object_ = self.object_

        secret_hint: None | str | Unset
        if isinstance(self.secret_hint, Unset):
            secret_hint = UNSET
        else:
            secret_hint = self.secret_hint

        expires_at: None | str | Unset
        if isinstance(self.expires_at, Unset):
            expires_at = UNSET
        elif isinstance(self.expires_at, datetime.datetime):
            expires_at = self.expires_at.isoformat()
        else:
            expires_at = self.expires_at

        scopes: list[str] | None | Unset
        if isinstance(self.scopes, Unset):
            scopes = UNSET
        elif isinstance(self.scopes, list):
            scopes = self.scopes

        else:
            scopes = self.scopes

        account_label: None | str | Unset
        if isinstance(self.account_label, Unset):
            account_label = UNSET
        else:
            account_label = self.account_label

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "provider": provider,
                "auth_type": auth_type,
                "status": status,
                "scope": scope,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if object_ is not UNSET:
            field_dict["object"] = object_
        if secret_hint is not UNSET:
            field_dict["secret_hint"] = secret_hint
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at
        if scopes is not UNSET:
            field_dict["scopes"] = scopes
        if account_label is not UNSET:
            field_dict["account_label"] = account_label

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        provider = d.pop("provider")

        auth_type = d.pop("auth_type")

        status = d.pop("status")

        scope = d.pop("scope")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        object_ = d.pop("object", UNSET)

        def _parse_secret_hint(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        secret_hint = _parse_secret_hint(d.pop("secret_hint", UNSET))

        def _parse_expires_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                expires_at_type_0 = datetime.datetime.fromisoformat(data)

                return expires_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        expires_at = _parse_expires_at(d.pop("expires_at", UNSET))

        def _parse_scopes(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                scopes_type_0 = cast(list[str], data)

                return scopes_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        scopes = _parse_scopes(d.pop("scopes", UNSET))

        def _parse_account_label(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        account_label = _parse_account_label(d.pop("account_label", UNSET))

        credential_response = cls(
            provider=provider,
            auth_type=auth_type,
            status=status,
            scope=scope,
            created_at=created_at,
            updated_at=updated_at,
            object_=object_,
            secret_hint=secret_hint,
            expires_at=expires_at,
            scopes=scopes,
            account_label=account_label,
        )

        credential_response.additional_properties = d
        return credential_response

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.credential_upsert_request_secret import CredentialUpsertRequestSecret


T = TypeVar("T", bound="CredentialUpsertRequest")


@_attrs_define
class CredentialUpsertRequest:
    """Bring-your-own: the tenant supplies the credential, Celesto stores it.

    ``secret`` is shaped by ``auth_type``: ``{"api_key": "..."}`` or
    ``{"access_token": "..."}``. Refresh tokens and client secrets are refused
    — Celesto never performs a token exchange, so holding the durable half of
    a credential would add breach exposure for nothing.

        Attributes:
            secret (CredentialUpsertRequestSecret): e.g. {"api_key": "ghp_..."}
            auth_type (str | Unset): api_key | oauth_token Default: 'api_key'.
            expires_at (datetime.datetime | None | Unset):
            scopes (list[str] | None | Unset):
            account_label (None | str | Unset):
    """

    secret: CredentialUpsertRequestSecret
    auth_type: str | Unset = "api_key"
    expires_at: datetime.datetime | None | Unset = UNSET
    scopes: list[str] | None | Unset = UNSET
    account_label: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.credential_upsert_request_secret import (
            CredentialUpsertRequestSecret,
        )  # noqa: PLC0415

        secret = self.secret.to_dict()

        auth_type = self.auth_type

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
                "secret": secret,
            }
        )
        if auth_type is not UNSET:
            field_dict["auth_type"] = auth_type
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at
        if scopes is not UNSET:
            field_dict["scopes"] = scopes
        if account_label is not UNSET:
            field_dict["account_label"] = account_label

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.credential_upsert_request_secret import (
            CredentialUpsertRequestSecret,
        )  # noqa: PLC0415

        d = dict(src_dict)
        secret = CredentialUpsertRequestSecret.from_dict(d.pop("secret"))

        auth_type = d.pop("auth_type", UNSET)

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

        credential_upsert_request = cls(
            secret=secret,
            auth_type=auth_type,
            expires_at=expires_at,
            scopes=scopes,
            account_label=account_label,
        )

        credential_upsert_request.additional_properties = d
        return credential_upsert_request

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

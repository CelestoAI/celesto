from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="CredentialVerifyResponse")


@_attrs_define
class CredentialVerifyResponse:
    """The result of calling the provider with a stored credential.

    Attributes:
        provider (str):
        ok (bool):
        scope (str):
        object_ (str | Unset):  Default: 'credential_verification'.
        account_label (None | str | Unset):
        scopes (list[str] | None | Unset):
        detail (None | str | Unset):
    """

    provider: str
    ok: bool
    scope: str
    object_: str | Unset = "credential_verification"
    account_label: None | str | Unset = UNSET
    scopes: list[str] | None | Unset = UNSET
    detail: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        provider = self.provider

        ok = self.ok

        scope = self.scope

        object_ = self.object_

        account_label: None | str | Unset
        if isinstance(self.account_label, Unset):
            account_label = UNSET
        else:
            account_label = self.account_label

        scopes: list[str] | None | Unset
        if isinstance(self.scopes, Unset):
            scopes = UNSET
        elif isinstance(self.scopes, list):
            scopes = self.scopes

        else:
            scopes = self.scopes

        detail: None | str | Unset
        if isinstance(self.detail, Unset):
            detail = UNSET
        else:
            detail = self.detail

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "provider": provider,
                "ok": ok,
                "scope": scope,
            }
        )
        if object_ is not UNSET:
            field_dict["object"] = object_
        if account_label is not UNSET:
            field_dict["account_label"] = account_label
        if scopes is not UNSET:
            field_dict["scopes"] = scopes
        if detail is not UNSET:
            field_dict["detail"] = detail

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        provider = d.pop("provider")

        ok = d.pop("ok")

        scope = d.pop("scope")

        object_ = d.pop("object", UNSET)

        def _parse_account_label(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        account_label = _parse_account_label(d.pop("account_label", UNSET))

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

        def _parse_detail(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        detail = _parse_detail(d.pop("detail", UNSET))

        credential_verify_response = cls(
            provider=provider,
            ok=ok,
            scope=scope,
            object_=object_,
            account_label=account_label,
            scopes=scopes,
            detail=detail,
        )

        credential_verify_response.additional_properties = d
        return credential_verify_response

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

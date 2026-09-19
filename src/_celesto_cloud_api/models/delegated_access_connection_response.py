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
    from ..models.delegated_access_connection_response_access_rules_type_0 import (
        DelegatedAccessConnectionResponseAccessRulesType0,
    )


T = TypeVar("T", bound="DelegatedAccessConnectionResponse")


@_attrs_define
class DelegatedAccessConnectionResponse:
    """Response representing a delegated access connection.

    Attributes:
        id (str):
        subject (str):
        provider (str):
        project_id (str):
        status (str):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        account_email (None | str | Unset):
        scopes (list[str] | Unset):
        last_used_at (datetime.datetime | None | Unset):
        access_rules (DelegatedAccessConnectionResponseAccessRulesType0 | None | Unset): Access rules for restricting
            file/folder access. NULL means unrestricted.
    """

    id: str
    subject: str
    provider: str
    project_id: str
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    account_email: None | str | Unset = UNSET
    scopes: list[str] | Unset = UNSET
    last_used_at: datetime.datetime | None | Unset = UNSET
    access_rules: DelegatedAccessConnectionResponseAccessRulesType0 | None | Unset = (
        UNSET
    )
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.delegated_access_connection_response_access_rules_type_0 import (
            DelegatedAccessConnectionResponseAccessRulesType0,
        )  # noqa: PLC0415

        id = self.id

        subject = self.subject

        provider = self.provider

        project_id = self.project_id

        status = self.status

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        account_email: None | str | Unset
        if isinstance(self.account_email, Unset):
            account_email = UNSET
        else:
            account_email = self.account_email

        scopes: list[str] | Unset = UNSET
        if not isinstance(self.scopes, Unset):
            scopes = self.scopes

        last_used_at: None | str | Unset
        if isinstance(self.last_used_at, Unset):
            last_used_at = UNSET
        elif isinstance(self.last_used_at, datetime.datetime):
            last_used_at = self.last_used_at.isoformat()
        else:
            last_used_at = self.last_used_at

        access_rules: dict[str, Any] | None | Unset
        if isinstance(self.access_rules, Unset):
            access_rules = UNSET
        elif isinstance(
            self.access_rules, DelegatedAccessConnectionResponseAccessRulesType0
        ):
            access_rules = self.access_rules.to_dict()
        else:
            access_rules = self.access_rules

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "subject": subject,
                "provider": provider,
                "project_id": project_id,
                "status": status,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if account_email is not UNSET:
            field_dict["account_email"] = account_email
        if scopes is not UNSET:
            field_dict["scopes"] = scopes
        if last_used_at is not UNSET:
            field_dict["last_used_at"] = last_used_at
        if access_rules is not UNSET:
            field_dict["access_rules"] = access_rules

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.delegated_access_connection_response_access_rules_type_0 import (
            DelegatedAccessConnectionResponseAccessRulesType0,
        )  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        subject = d.pop("subject")

        provider = d.pop("provider")

        project_id = d.pop("project_id")

        status = d.pop("status")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        def _parse_account_email(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        account_email = _parse_account_email(d.pop("account_email", UNSET))

        scopes = cast(list[str], d.pop("scopes", UNSET))

        def _parse_last_used_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_used_at_type_0 = datetime.datetime.fromisoformat(data)

                return last_used_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        last_used_at = _parse_last_used_at(d.pop("last_used_at", UNSET))

        def _parse_access_rules(
            data: object,
        ) -> DelegatedAccessConnectionResponseAccessRulesType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                access_rules_type_0 = (
                    DelegatedAccessConnectionResponseAccessRulesType0.from_dict(data)
                )

                return access_rules_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                DelegatedAccessConnectionResponseAccessRulesType0 | None | Unset, data
            )

        access_rules = _parse_access_rules(d.pop("access_rules", UNSET))

        delegated_access_connection_response = cls(
            id=id,
            subject=subject,
            provider=provider,
            project_id=project_id,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            account_email=account_email,
            scopes=scopes,
            last_used_at=last_used_at,
            access_rules=access_rules,
        )

        delegated_access_connection_response.additional_properties = d
        return delegated_access_connection_response

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

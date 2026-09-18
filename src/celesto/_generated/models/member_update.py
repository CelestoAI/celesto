from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.membership_status import MembershipStatus
from ..models.organization_role import OrganizationRole
from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="MemberUpdate")


@_attrs_define
class MemberUpdate:
    """Schema for updating a member's role or status.

    Attributes:
        role (None | OrganizationRole | Unset): New role for the member.
        status (MembershipStatus | None | Unset): New status for the member.
    """

    role: None | OrganizationRole | Unset = UNSET
    status: MembershipStatus | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        role: None | str | Unset
        if isinstance(self.role, Unset):
            role = UNSET
        elif isinstance(self.role, OrganizationRole):
            role = self.role.value
        else:
            role = self.role

        status: None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        elif isinstance(self.status, MembershipStatus):
            status = self.status.value
        else:
            status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if role is not UNSET:
            field_dict["role"] = role
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_role(data: object) -> None | OrganizationRole | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                role_type_0 = OrganizationRole(data)

                return role_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | OrganizationRole | Unset, data)

        role = _parse_role(d.pop("role", UNSET))

        def _parse_status(data: object) -> MembershipStatus | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                status_type_0 = MembershipStatus(data)

                return status_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(MembershipStatus | None | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        member_update = cls(
            role=role,
            status=status,
        )

        member_update.additional_properties = d
        return member_update

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

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
import datetime


T = TypeVar("T", bound="OrganizationMemberRead")


@_attrs_define
class OrganizationMemberRead:
    """Schema for reading organization member details.

    Attributes:
        user_id (str): User ID
        first_name (str): First name of the user.
        email (str): Email of the user.
        role (OrganizationRole): User role within an organization
        status (MembershipStatus): Membership status for organization links
        joined_at (datetime.datetime): Timestamp of when the user joined.
        last_name (None | str | Unset): Last name of the user.
        added_by (None | str | Unset): User ID of who added this member (NULL = system).
    """

    user_id: str
    first_name: str
    email: str
    role: OrganizationRole
    status: MembershipStatus
    joined_at: datetime.datetime
    last_name: None | str | Unset = UNSET
    added_by: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = self.user_id

        first_name = self.first_name

        email = self.email

        role = self.role.value

        status = self.status.value

        joined_at = self.joined_at.isoformat()

        last_name: None | str | Unset
        if isinstance(self.last_name, Unset):
            last_name = UNSET
        else:
            last_name = self.last_name

        added_by: None | str | Unset
        if isinstance(self.added_by, Unset):
            added_by = UNSET
        else:
            added_by = self.added_by

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
                "first_name": first_name,
                "email": email,
                "role": role,
                "status": status,
                "joined_at": joined_at,
            }
        )
        if last_name is not UNSET:
            field_dict["last_name"] = last_name
        if added_by is not UNSET:
            field_dict["added_by"] = added_by

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_id = d.pop("user_id")

        first_name = d.pop("first_name")

        email = d.pop("email")

        role = OrganizationRole(d.pop("role"))

        status = MembershipStatus(d.pop("status"))

        joined_at = datetime.datetime.fromisoformat(d.pop("joined_at"))

        def _parse_last_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        last_name = _parse_last_name(d.pop("last_name", UNSET))

        def _parse_added_by(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        added_by = _parse_added_by(d.pop("added_by", UNSET))

        organization_member_read = cls(
            user_id=user_id,
            first_name=first_name,
            email=email,
            role=role,
            status=status,
            joined_at=joined_at,
            last_name=last_name,
            added_by=added_by,
        )

        organization_member_read.additional_properties = d
        return organization_member_read

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

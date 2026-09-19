from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.organization_role import OrganizationRole
from ..types import UNSET, Unset


T = TypeVar("T", bound="AddMemberRequest")


@_attrs_define
class AddMemberRequest:
    """Schema for adding a user to an organization.

    Attributes:
        email (str): Email of the user to add.
        role (OrganizationRole | Unset): User role within an organization
    """

    email: str
    role: OrganizationRole | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        role: str | Unset = UNSET
        if not isinstance(self.role, Unset):
            role = self.role.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "email": email,
            }
        )
        if role is not UNSET:
            field_dict["role"] = role

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        email = d.pop("email")

        _role = d.pop("role", UNSET)
        role: OrganizationRole | Unset
        if isinstance(_role, Unset):
            role = UNSET
        else:
            role = OrganizationRole(_role)

        add_member_request = cls(
            email=email,
            role=role,
        )

        add_member_request.additional_properties = d
        return add_member_request

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import Literal, cast


T = TypeVar("T", bound="InvitationRead")


@_attrs_define
class InvitationRead:
    """
    Attributes:
        email (str):
        status (Literal['PENDING'] | Unset):  Default: 'PENDING'.
    """

    email: str
    status: Literal["PENDING"] | Unset = "PENDING"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        email = self.email

        status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "email": email,
            }
        )
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        email = d.pop("email")

        status = cast(Literal["PENDING"] | Unset, d.pop("status", UNSET))
        if status != "PENDING" and not isinstance(status, Unset):
            raise ValueError(f"status must match const 'PENDING', got '{status}'")

        invitation_read = cls(
            email=email,
            status=status,
        )

        invitation_read.additional_properties = d
        return invitation_read

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

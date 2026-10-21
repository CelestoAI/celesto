from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.recent_sandbox_user import RecentSandboxUser


T = TypeVar("T", bound="RecentSandboxUsers")


@_attrs_define
class RecentSandboxUsers:
    """
    Attributes:
        observed_at (datetime.datetime):
        page (int):
        page_size (int):
        total (int):
        users (list[RecentSandboxUser]):
    """

    observed_at: datetime.datetime
    page: int
    page_size: int
    total: int
    users: list[RecentSandboxUser]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.recent_sandbox_user import RecentSandboxUser  # noqa: PLC0415

        observed_at = self.observed_at.isoformat()

        page = self.page

        page_size = self.page_size

        total = self.total

        users = []
        for users_item_data in self.users:
            users_item = users_item_data.to_dict()
            users.append(users_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "observed_at": observed_at,
                "page": page,
                "page_size": page_size,
                "total": total,
                "users": users,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.recent_sandbox_user import RecentSandboxUser  # noqa: PLC0415

        d = dict(src_dict)
        observed_at = datetime.datetime.fromisoformat(d.pop("observed_at"))

        page = d.pop("page")

        page_size = d.pop("page_size")

        total = d.pop("total")

        users = []
        _users = d.pop("users")
        for users_item_data in _users:
            users_item = RecentSandboxUser.from_dict(users_item_data)

            users.append(users_item)

        recent_sandbox_users = cls(
            observed_at=observed_at,
            page=page,
            page_size=page_size,
            total=total,
            users=users,
        )

        recent_sandbox_users.additional_properties = d
        return recent_sandbox_users

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

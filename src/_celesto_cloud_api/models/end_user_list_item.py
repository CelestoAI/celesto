from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
import datetime


T = TypeVar("T", bound="EndUserListItem")


@_attrs_define
class EndUserListItem:
    """
    Attributes:
        end_user_id (str):
        first_activity_at (datetime.datetime):
        created_at (datetime.datetime):
        spent_usd (str):
        object_ (str | Unset):  Default: 'end_user'.
        budget_cap_usd (None | str | Unset):
    """

    end_user_id: str
    first_activity_at: datetime.datetime
    created_at: datetime.datetime
    spent_usd: str
    object_: str | Unset = "end_user"
    budget_cap_usd: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        end_user_id = self.end_user_id

        first_activity_at = self.first_activity_at.isoformat()

        created_at = self.created_at.isoformat()

        spent_usd = self.spent_usd

        object_ = self.object_

        budget_cap_usd: None | str | Unset
        if isinstance(self.budget_cap_usd, Unset):
            budget_cap_usd = UNSET
        else:
            budget_cap_usd = self.budget_cap_usd

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "end_user_id": end_user_id,
                "first_activity_at": first_activity_at,
                "created_at": created_at,
                "spent_usd": spent_usd,
            }
        )
        if object_ is not UNSET:
            field_dict["object"] = object_
        if budget_cap_usd is not UNSET:
            field_dict["budget_cap_usd"] = budget_cap_usd

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        end_user_id = d.pop("end_user_id")

        first_activity_at = datetime.datetime.fromisoformat(d.pop("first_activity_at"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        spent_usd = d.pop("spent_usd")

        object_ = d.pop("object", UNSET)

        def _parse_budget_cap_usd(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        budget_cap_usd = _parse_budget_cap_usd(d.pop("budget_cap_usd", UNSET))

        end_user_list_item = cls(
            end_user_id=end_user_id,
            first_activity_at=first_activity_at,
            created_at=created_at,
            spent_usd=spent_usd,
            object_=object_,
            budget_cap_usd=budget_cap_usd,
        )

        end_user_list_item.additional_properties = d
        return end_user_list_item

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

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
    from ..models.thread_message_response_item import ThreadMessageResponseItem


T = TypeVar("T", bound="ThreadMessageResponse")


@_attrs_define
class ThreadMessageResponse:
    """A stored turn, projected into a stable shape.

    `item` is the runtime payload as stored; `item_format` identifies its
    schema so consumers are not guessing. Callers that only need the text can
    read `role` and ignore the rest.

        Attributes:
            seq (int):
            item (ThreadMessageResponseItem):
            item_format (str):
            created_at (datetime.datetime):
            role (None | str | Unset):
    """

    seq: int
    item: ThreadMessageResponseItem
    item_format: str
    created_at: datetime.datetime
    role: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.thread_message_response_item import ThreadMessageResponseItem  # noqa: PLC0415

        seq = self.seq

        item = self.item.to_dict()

        item_format = self.item_format

        created_at = self.created_at.isoformat()

        role: None | str | Unset
        if isinstance(self.role, Unset):
            role = UNSET
        else:
            role = self.role

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "seq": seq,
                "item": item,
                "item_format": item_format,
                "created_at": created_at,
            }
        )
        if role is not UNSET:
            field_dict["role"] = role

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.thread_message_response_item import ThreadMessageResponseItem  # noqa: PLC0415

        d = dict(src_dict)
        seq = d.pop("seq")

        item = ThreadMessageResponseItem.from_dict(d.pop("item"))

        item_format = d.pop("item_format")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        def _parse_role(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        role = _parse_role(d.pop("role", UNSET))

        thread_message_response = cls(
            seq=seq,
            item=item,
            item_format=item_format,
            created_at=created_at,
            role=role,
        )

        thread_message_response.additional_properties = d
        return thread_message_response

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

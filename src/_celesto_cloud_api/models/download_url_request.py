from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset


T = TypeVar("T", bound="DownloadUrlRequest")


@_attrs_define
class DownloadUrlRequest:
    """
    Attributes:
        entry_id (int):
        ticket (str | Unset):  Default: ''.
    """

    entry_id: int
    ticket: str | Unset = ""
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        entry_id = self.entry_id

        ticket = self.ticket

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "entryId": entry_id,
            }
        )
        if ticket is not UNSET:
            field_dict["ticket"] = ticket

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        entry_id = d.pop("entryId")

        ticket = d.pop("ticket", UNSET)

        download_url_request = cls(
            entry_id=entry_id,
            ticket=ticket,
        )

        download_url_request.additional_properties = d
        return download_url_request

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

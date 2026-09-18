from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="ComputerPublishedPortResponse")


@_attrs_define
class ComputerPublishedPortResponse:
    """Public route for a port inside a computer.

    Attributes:
        computer_id (str):
        port (int):
        status (str):
        id (None | str | Unset):
        url (None | str | Unset):
        created_at (None | str | Unset):
    """

    computer_id: str
    port: int
    status: str
    id: None | str | Unset = UNSET
    url: None | str | Unset = UNSET
    created_at: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        computer_id = self.computer_id

        port = self.port

        status = self.status

        id: None | str | Unset
        if isinstance(self.id, Unset):
            id = UNSET
        else:
            id = self.id

        url: None | str | Unset
        if isinstance(self.url, Unset):
            url = UNSET
        else:
            url = self.url

        created_at: None | str | Unset
        if isinstance(self.created_at, Unset):
            created_at = UNSET
        else:
            created_at = self.created_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "computer_id": computer_id,
                "port": port,
                "status": status,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if url is not UNSET:
            field_dict["url"] = url
        if created_at is not UNSET:
            field_dict["created_at"] = created_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        computer_id = d.pop("computer_id")

        port = d.pop("port")

        status = d.pop("status")

        def _parse_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        id = _parse_id(d.pop("id", UNSET))

        def _parse_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        url = _parse_url(d.pop("url", UNSET))

        def _parse_created_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        created_at = _parse_created_at(d.pop("created_at", UNSET))

        computer_published_port_response = cls(
            computer_id=computer_id,
            port=port,
            status=status,
            id=id,
            url=url,
            created_at=created_at,
        )

        computer_published_port_response.additional_properties = d
        return computer_published_port_response

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

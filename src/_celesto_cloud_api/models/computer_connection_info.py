from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="ComputerConnectionInfo")


@_attrs_define
class ComputerConnectionInfo:
    """SSH and access connection details.

    Attributes:
        ssh (None | str | Unset):
        access_url (None | str | Unset):
    """

    ssh: None | str | Unset = UNSET
    access_url: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ssh: None | str | Unset
        if isinstance(self.ssh, Unset):
            ssh = UNSET
        else:
            ssh = self.ssh

        access_url: None | str | Unset
        if isinstance(self.access_url, Unset):
            access_url = UNSET
        else:
            access_url = self.access_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if ssh is not UNSET:
            field_dict["ssh"] = ssh
        if access_url is not UNSET:
            field_dict["access_url"] = access_url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_ssh(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        ssh = _parse_ssh(d.pop("ssh", UNSET))

        def _parse_access_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        access_url = _parse_access_url(d.pop("access_url", UNSET))

        computer_connection_info = cls(
            ssh=ssh,
            access_url=access_url,
        )

        computer_connection_info.additional_properties = d
        return computer_connection_info

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

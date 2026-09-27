from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset


T = TypeVar("T", bound="PoolGitCredentialRequest")


@_attrs_define
class PoolGitCredentialRequest:
    """
    Attributes:
        epoch (int):
        state_id (str):
        computer_id (str):
        protocol (str):
        host (str):
    """

    epoch: int
    state_id: str
    computer_id: str
    protocol: str
    host: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        epoch = self.epoch

        state_id = self.state_id

        computer_id = self.computer_id

        protocol = self.protocol

        host = self.host

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "epoch": epoch,
                "state_id": state_id,
                "computer_id": computer_id,
                "protocol": protocol,
                "host": host,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        epoch = d.pop("epoch")

        state_id = d.pop("state_id")

        computer_id = d.pop("computer_id")

        protocol = d.pop("protocol")

        host = d.pop("host")

        pool_git_credential_request = cls(
            epoch=epoch,
            state_id=state_id,
            computer_id=computer_id,
            protocol=protocol,
            host=host,
        )

        pool_git_credential_request.additional_properties = d
        return pool_git_credential_request

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

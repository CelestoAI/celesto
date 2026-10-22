from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from uuid import UUID


T = TypeVar("T", bound="FleetReleaseHostActivationRequest")


@_attrs_define
class FleetReleaseHostActivationRequest:
    """Activation binds the post-update session to the drained session epoch.

    Attributes:
        release_id (str):
        attempt_id (UUID):
        state_id (UUID):
        commit (str):
        archive_sha256 (str):
        drained_session_epoch (int):
    """

    release_id: str
    attempt_id: UUID
    state_id: UUID
    commit: str
    archive_sha256: str
    drained_session_epoch: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        release_id = self.release_id

        attempt_id = str(self.attempt_id)

        state_id = str(self.state_id)

        commit = self.commit

        archive_sha256 = self.archive_sha256

        drained_session_epoch = self.drained_session_epoch

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "release_id": release_id,
                "attempt_id": attempt_id,
                "state_id": state_id,
                "commit": commit,
                "archive_sha256": archive_sha256,
                "drained_session_epoch": drained_session_epoch,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        release_id = d.pop("release_id")

        attempt_id = UUID(d.pop("attempt_id"))

        state_id = UUID(d.pop("state_id"))

        commit = d.pop("commit")

        archive_sha256 = d.pop("archive_sha256")

        drained_session_epoch = d.pop("drained_session_epoch")

        fleet_release_host_activation_request = cls(
            release_id=release_id,
            attempt_id=attempt_id,
            state_id=state_id,
            commit=commit,
            archive_sha256=archive_sha256,
            drained_session_epoch=drained_session_epoch,
        )

        fleet_release_host_activation_request.additional_properties = d
        return fleet_release_host_activation_request

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

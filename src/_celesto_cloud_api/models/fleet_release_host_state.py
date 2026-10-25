from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
from uuid import UUID


T = TypeVar("T", bound="FleetReleaseHostState")


@_attrs_define
class FleetReleaseHostState:
    """Safe state returned to the durable runner record.

    Attributes:
        host_id (str):
        state_id (UUID):
        phase (str):
        fence_reference (None | str):
        drained_session_epoch (int):
        session_epoch (int):
        admitted (bool):
        ready (bool):
        last_seen (None | str):
    """

    host_id: str
    state_id: UUID
    phase: str
    fence_reference: None | str
    drained_session_epoch: int
    session_epoch: int
    admitted: bool
    ready: bool
    last_seen: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        host_id = self.host_id

        state_id = str(self.state_id)

        phase = self.phase

        fence_reference: None | str
        fence_reference = self.fence_reference

        drained_session_epoch = self.drained_session_epoch

        session_epoch = self.session_epoch

        admitted = self.admitted

        ready = self.ready

        last_seen: None | str
        last_seen = self.last_seen

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "host_id": host_id,
                "state_id": state_id,
                "phase": phase,
                "fence_reference": fence_reference,
                "drained_session_epoch": drained_session_epoch,
                "session_epoch": session_epoch,
                "admitted": admitted,
                "ready": ready,
                "last_seen": last_seen,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        host_id = d.pop("host_id")

        state_id = UUID(d.pop("state_id"))

        phase = d.pop("phase")

        def _parse_fence_reference(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        fence_reference = _parse_fence_reference(d.pop("fence_reference"))

        drained_session_epoch = d.pop("drained_session_epoch")

        session_epoch = d.pop("session_epoch")

        admitted = d.pop("admitted")

        ready = d.pop("ready")

        def _parse_last_seen(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        last_seen = _parse_last_seen(d.pop("last_seen"))

        fleet_release_host_state = cls(
            host_id=host_id,
            state_id=state_id,
            phase=phase,
            fence_reference=fence_reference,
            drained_session_epoch=drained_session_epoch,
            session_epoch=session_epoch,
            admitted=admitted,
            ready=ready,
            last_seen=last_seen,
        )

        fleet_release_host_state.additional_properties = d
        return fleet_release_host_state

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.pool_heartbeat_request_running_computers_type_0_item import (
        PoolHeartbeatRequestRunningComputersType0Item,
    )


T = TypeVar("T", bound="PoolHeartbeatRequest")


@_attrs_define
class PoolHeartbeatRequest:
    """
    Attributes:
        epoch (int):
        state_id (str):
        disk_free_mb (int):
        disk_total_mb (int | None | Unset):
        stream_protocol_version (int | Unset):  Default: 1.
        running_computers (list[PoolHeartbeatRequestRunningComputersType0Item] | None | Unset):
    """

    epoch: int
    state_id: str
    disk_free_mb: int
    disk_total_mb: int | None | Unset = UNSET
    stream_protocol_version: int | Unset = 1
    running_computers: (
        list[PoolHeartbeatRequestRunningComputersType0Item] | None | Unset
    ) = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.pool_heartbeat_request_running_computers_type_0_item import (
            PoolHeartbeatRequestRunningComputersType0Item,
        )  # noqa: PLC0415

        epoch = self.epoch

        state_id = self.state_id

        disk_free_mb = self.disk_free_mb

        disk_total_mb: int | None | Unset
        if isinstance(self.disk_total_mb, Unset):
            disk_total_mb = UNSET
        else:
            disk_total_mb = self.disk_total_mb

        stream_protocol_version = self.stream_protocol_version

        running_computers: list[dict[str, Any]] | None | Unset
        if isinstance(self.running_computers, Unset):
            running_computers = UNSET
        elif isinstance(self.running_computers, list):
            running_computers = []
            for running_computers_type_0_item_data in self.running_computers:
                running_computers_type_0_item = (
                    running_computers_type_0_item_data.to_dict()
                )
                running_computers.append(running_computers_type_0_item)

        else:
            running_computers = self.running_computers

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "epoch": epoch,
                "state_id": state_id,
                "disk_free_mb": disk_free_mb,
            }
        )
        if disk_total_mb is not UNSET:
            field_dict["disk_total_mb"] = disk_total_mb
        if stream_protocol_version is not UNSET:
            field_dict["stream_protocol_version"] = stream_protocol_version
        if running_computers is not UNSET:
            field_dict["running_computers"] = running_computers

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pool_heartbeat_request_running_computers_type_0_item import (
            PoolHeartbeatRequestRunningComputersType0Item,
        )  # noqa: PLC0415

        d = dict(src_dict)
        epoch = d.pop("epoch")

        state_id = d.pop("state_id")

        disk_free_mb = d.pop("disk_free_mb")

        def _parse_disk_total_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        disk_total_mb = _parse_disk_total_mb(d.pop("disk_total_mb", UNSET))

        stream_protocol_version = d.pop("stream_protocol_version", UNSET)

        def _parse_running_computers(
            data: object,
        ) -> list[PoolHeartbeatRequestRunningComputersType0Item] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                running_computers_type_0 = []
                _running_computers_type_0 = data
                for running_computers_type_0_item_data in _running_computers_type_0:
                    running_computers_type_0_item = (
                        PoolHeartbeatRequestRunningComputersType0Item.from_dict(
                            running_computers_type_0_item_data
                        )
                    )

                    running_computers_type_0.append(running_computers_type_0_item)

                return running_computers_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                list[PoolHeartbeatRequestRunningComputersType0Item] | None | Unset, data
            )

        running_computers = _parse_running_computers(d.pop("running_computers", UNSET))

        pool_heartbeat_request = cls(
            epoch=epoch,
            state_id=state_id,
            disk_free_mb=disk_free_mb,
            disk_total_mb=disk_total_mb,
            stream_protocol_version=stream_protocol_version,
            running_computers=running_computers,
        )

        pool_heartbeat_request.additional_properties = d
        return pool_heartbeat_request

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

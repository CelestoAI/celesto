from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.inventory import Inventory


T = TypeVar("T", bound="SessionRequest")


@_attrs_define
class SessionRequest:
    """
    Attributes:
        state_id (str):
        inventory (Inventory):
        stream_protocol_version (int | Unset):  Default: 1.
        usage_running_heartbeat (bool | Unset):  Default: False.
        usage_billing_fence (bool | Unset):  Default: False.
        stopped_disk_offload (bool | Unset):  Default: False.
        custom_template_artifacts (bool | Unset):  Default: False.
        long_poll (bool | Unset):  Default: False.
        exec_slots (int | None | Unset):
        light_slots (int | None | Unset):
        heavy_slots (int | None | Unset):
        disk_write_mbps (float | None | Unset):
    """

    state_id: str
    inventory: Inventory
    stream_protocol_version: int | Unset = 1
    usage_running_heartbeat: bool | Unset = False
    usage_billing_fence: bool | Unset = False
    stopped_disk_offload: bool | Unset = False
    custom_template_artifacts: bool | Unset = False
    long_poll: bool | Unset = False
    exec_slots: int | None | Unset = UNSET
    light_slots: int | None | Unset = UNSET
    heavy_slots: int | None | Unset = UNSET
    disk_write_mbps: float | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.inventory import Inventory  # noqa: PLC0415

        state_id = self.state_id

        inventory = self.inventory.to_dict()

        stream_protocol_version = self.stream_protocol_version

        usage_running_heartbeat = self.usage_running_heartbeat

        usage_billing_fence = self.usage_billing_fence

        stopped_disk_offload = self.stopped_disk_offload

        custom_template_artifacts = self.custom_template_artifacts

        long_poll = self.long_poll

        exec_slots: int | None | Unset
        if isinstance(self.exec_slots, Unset):
            exec_slots = UNSET
        else:
            exec_slots = self.exec_slots

        light_slots: int | None | Unset
        if isinstance(self.light_slots, Unset):
            light_slots = UNSET
        else:
            light_slots = self.light_slots

        heavy_slots: int | None | Unset
        if isinstance(self.heavy_slots, Unset):
            heavy_slots = UNSET
        else:
            heavy_slots = self.heavy_slots

        disk_write_mbps: float | None | Unset
        if isinstance(self.disk_write_mbps, Unset):
            disk_write_mbps = UNSET
        else:
            disk_write_mbps = self.disk_write_mbps

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "state_id": state_id,
                "inventory": inventory,
            }
        )
        if stream_protocol_version is not UNSET:
            field_dict["stream_protocol_version"] = stream_protocol_version
        if usage_running_heartbeat is not UNSET:
            field_dict["usage_running_heartbeat"] = usage_running_heartbeat
        if usage_billing_fence is not UNSET:
            field_dict["usage_billing_fence"] = usage_billing_fence
        if stopped_disk_offload is not UNSET:
            field_dict["stopped_disk_offload"] = stopped_disk_offload
        if custom_template_artifacts is not UNSET:
            field_dict["custom_template_artifacts"] = custom_template_artifacts
        if long_poll is not UNSET:
            field_dict["long_poll"] = long_poll
        if exec_slots is not UNSET:
            field_dict["exec_slots"] = exec_slots
        if light_slots is not UNSET:
            field_dict["light_slots"] = light_slots
        if heavy_slots is not UNSET:
            field_dict["heavy_slots"] = heavy_slots
        if disk_write_mbps is not UNSET:
            field_dict["disk_write_mbps"] = disk_write_mbps

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory import Inventory  # noqa: PLC0415

        d = dict(src_dict)
        state_id = d.pop("state_id")

        inventory = Inventory.from_dict(d.pop("inventory"))

        stream_protocol_version = d.pop("stream_protocol_version", UNSET)

        usage_running_heartbeat = d.pop("usage_running_heartbeat", UNSET)

        usage_billing_fence = d.pop("usage_billing_fence", UNSET)

        stopped_disk_offload = d.pop("stopped_disk_offload", UNSET)

        custom_template_artifacts = d.pop("custom_template_artifacts", UNSET)

        long_poll = d.pop("long_poll", UNSET)

        def _parse_exec_slots(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        exec_slots = _parse_exec_slots(d.pop("exec_slots", UNSET))

        def _parse_light_slots(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        light_slots = _parse_light_slots(d.pop("light_slots", UNSET))

        def _parse_heavy_slots(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        heavy_slots = _parse_heavy_slots(d.pop("heavy_slots", UNSET))

        def _parse_disk_write_mbps(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        disk_write_mbps = _parse_disk_write_mbps(d.pop("disk_write_mbps", UNSET))

        session_request = cls(
            state_id=state_id,
            inventory=inventory,
            stream_protocol_version=stream_protocol_version,
            usage_running_heartbeat=usage_running_heartbeat,
            usage_billing_fence=usage_billing_fence,
            stopped_disk_offload=stopped_disk_offload,
            custom_template_artifacts=custom_template_artifacts,
            long_poll=long_poll,
            exec_slots=exec_slots,
            light_slots=light_slots,
            heavy_slots=heavy_slots,
            disk_write_mbps=disk_write_mbps,
        )

        session_request.additional_properties = d
        return session_request

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

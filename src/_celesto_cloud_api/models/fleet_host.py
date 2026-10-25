from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.computer_counts import ComputerCounts
    from ..models.fleet_capacity import FleetCapacity


T = TypeVar("T", bound="FleetHost")


@_attrs_define
class FleetHost:
    """
    Attributes:
        host_id (str):
        provider (str):
        pool_id (str):
        region (str):
        priority (int):
        pool_enabled (bool):
        status (str):
        admitted (bool):
        ready (bool):
        public_egress_ready (bool):
        stopped_disk_offload (bool):
        last_seen (datetime.datetime | None):
        stale (bool):
        eligible (bool):
        ineligibility_reason (None | str):
        computers (ComputerCounts):
        capacity (FleetCapacity):
    """

    host_id: str
    provider: str
    pool_id: str
    region: str
    priority: int
    pool_enabled: bool
    status: str
    admitted: bool
    ready: bool
    public_egress_ready: bool
    stopped_disk_offload: bool
    last_seen: datetime.datetime | None
    stale: bool
    eligible: bool
    ineligibility_reason: None | str
    computers: ComputerCounts
    capacity: FleetCapacity
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.computer_counts import ComputerCounts  # noqa: PLC0415
        from ..models.fleet_capacity import FleetCapacity  # noqa: PLC0415

        host_id = self.host_id

        provider = self.provider

        pool_id = self.pool_id

        region = self.region

        priority = self.priority

        pool_enabled = self.pool_enabled

        status = self.status

        admitted = self.admitted

        ready = self.ready

        public_egress_ready = self.public_egress_ready

        stopped_disk_offload = self.stopped_disk_offload

        last_seen: None | str
        if isinstance(self.last_seen, datetime.datetime):
            last_seen = self.last_seen.isoformat()
        else:
            last_seen = self.last_seen

        stale = self.stale

        eligible = self.eligible

        ineligibility_reason: None | str
        ineligibility_reason = self.ineligibility_reason

        computers = self.computers.to_dict()

        capacity = self.capacity.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "host_id": host_id,
                "provider": provider,
                "pool_id": pool_id,
                "region": region,
                "priority": priority,
                "pool_enabled": pool_enabled,
                "status": status,
                "admitted": admitted,
                "ready": ready,
                "public_egress_ready": public_egress_ready,
                "stopped_disk_offload": stopped_disk_offload,
                "last_seen": last_seen,
                "stale": stale,
                "eligible": eligible,
                "ineligibility_reason": ineligibility_reason,
                "computers": computers,
                "capacity": capacity,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.computer_counts import ComputerCounts  # noqa: PLC0415
        from ..models.fleet_capacity import FleetCapacity  # noqa: PLC0415

        d = dict(src_dict)
        host_id = d.pop("host_id")

        provider = d.pop("provider")

        pool_id = d.pop("pool_id")

        region = d.pop("region")

        priority = d.pop("priority")

        pool_enabled = d.pop("pool_enabled")

        status = d.pop("status")

        admitted = d.pop("admitted")

        ready = d.pop("ready")

        public_egress_ready = d.pop("public_egress_ready")

        stopped_disk_offload = d.pop("stopped_disk_offload")

        def _parse_last_seen(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_seen_type_0 = datetime.datetime.fromisoformat(data)

                return last_seen_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        last_seen = _parse_last_seen(d.pop("last_seen"))

        stale = d.pop("stale")

        eligible = d.pop("eligible")

        def _parse_ineligibility_reason(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        ineligibility_reason = _parse_ineligibility_reason(
            d.pop("ineligibility_reason")
        )

        computers = ComputerCounts.from_dict(d.pop("computers"))

        capacity = FleetCapacity.from_dict(d.pop("capacity"))

        fleet_host = cls(
            host_id=host_id,
            provider=provider,
            pool_id=pool_id,
            region=region,
            priority=priority,
            pool_enabled=pool_enabled,
            status=status,
            admitted=admitted,
            ready=ready,
            public_egress_ready=public_egress_ready,
            stopped_disk_offload=stopped_disk_offload,
            last_seen=last_seen,
            stale=stale,
            eligible=eligible,
            ineligibility_reason=ineligibility_reason,
            computers=computers,
            capacity=capacity,
        )

        fleet_host.additional_properties = d
        return fleet_host

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="ComputerMetricsSummary")


@_attrs_define
class ComputerMetricsSummary:
    """Latest sandbox metrics shown with a computer.

    Attributes:
        observed_at (None | str | Unset):
        stale (bool | Unset):  Default: False.
        partial (bool | Unset):  Default: False.
        runtime_instance_id (None | str | Unset):
        uptime_seconds (int | None | Unset):
        guest_metrics_status (None | str | Unset):
        host_metrics_status (None | str | Unset):
        cpu_used_percent (float | None | Unset):
        ram_used_mb (int | None | Unset):
        ram_total_mb (int | None | Unset):
        disk_used_mb (int | None | Unset):
        disk_total_mb (int | None | Unset):
        network_rx_bytes (int | None | Unset):
        network_tx_bytes (int | None | Unset):
        disk_read_bytes (int | None | Unset):
        disk_write_bytes (int | None | Unset):
    """

    observed_at: None | str | Unset = UNSET
    stale: bool | Unset = False
    partial: bool | Unset = False
    runtime_instance_id: None | str | Unset = UNSET
    uptime_seconds: int | None | Unset = UNSET
    guest_metrics_status: None | str | Unset = UNSET
    host_metrics_status: None | str | Unset = UNSET
    cpu_used_percent: float | None | Unset = UNSET
    ram_used_mb: int | None | Unset = UNSET
    ram_total_mb: int | None | Unset = UNSET
    disk_used_mb: int | None | Unset = UNSET
    disk_total_mb: int | None | Unset = UNSET
    network_rx_bytes: int | None | Unset = UNSET
    network_tx_bytes: int | None | Unset = UNSET
    disk_read_bytes: int | None | Unset = UNSET
    disk_write_bytes: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        observed_at: None | str | Unset
        if isinstance(self.observed_at, Unset):
            observed_at = UNSET
        else:
            observed_at = self.observed_at

        stale = self.stale

        partial = self.partial

        runtime_instance_id: None | str | Unset
        if isinstance(self.runtime_instance_id, Unset):
            runtime_instance_id = UNSET
        else:
            runtime_instance_id = self.runtime_instance_id

        uptime_seconds: int | None | Unset
        if isinstance(self.uptime_seconds, Unset):
            uptime_seconds = UNSET
        else:
            uptime_seconds = self.uptime_seconds

        guest_metrics_status: None | str | Unset
        if isinstance(self.guest_metrics_status, Unset):
            guest_metrics_status = UNSET
        else:
            guest_metrics_status = self.guest_metrics_status

        host_metrics_status: None | str | Unset
        if isinstance(self.host_metrics_status, Unset):
            host_metrics_status = UNSET
        else:
            host_metrics_status = self.host_metrics_status

        cpu_used_percent: float | None | Unset
        if isinstance(self.cpu_used_percent, Unset):
            cpu_used_percent = UNSET
        else:
            cpu_used_percent = self.cpu_used_percent

        ram_used_mb: int | None | Unset
        if isinstance(self.ram_used_mb, Unset):
            ram_used_mb = UNSET
        else:
            ram_used_mb = self.ram_used_mb

        ram_total_mb: int | None | Unset
        if isinstance(self.ram_total_mb, Unset):
            ram_total_mb = UNSET
        else:
            ram_total_mb = self.ram_total_mb

        disk_used_mb: int | None | Unset
        if isinstance(self.disk_used_mb, Unset):
            disk_used_mb = UNSET
        else:
            disk_used_mb = self.disk_used_mb

        disk_total_mb: int | None | Unset
        if isinstance(self.disk_total_mb, Unset):
            disk_total_mb = UNSET
        else:
            disk_total_mb = self.disk_total_mb

        network_rx_bytes: int | None | Unset
        if isinstance(self.network_rx_bytes, Unset):
            network_rx_bytes = UNSET
        else:
            network_rx_bytes = self.network_rx_bytes

        network_tx_bytes: int | None | Unset
        if isinstance(self.network_tx_bytes, Unset):
            network_tx_bytes = UNSET
        else:
            network_tx_bytes = self.network_tx_bytes

        disk_read_bytes: int | None | Unset
        if isinstance(self.disk_read_bytes, Unset):
            disk_read_bytes = UNSET
        else:
            disk_read_bytes = self.disk_read_bytes

        disk_write_bytes: int | None | Unset
        if isinstance(self.disk_write_bytes, Unset):
            disk_write_bytes = UNSET
        else:
            disk_write_bytes = self.disk_write_bytes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if observed_at is not UNSET:
            field_dict["observed_at"] = observed_at
        if stale is not UNSET:
            field_dict["stale"] = stale
        if partial is not UNSET:
            field_dict["partial"] = partial
        if runtime_instance_id is not UNSET:
            field_dict["runtime_instance_id"] = runtime_instance_id
        if uptime_seconds is not UNSET:
            field_dict["uptime_seconds"] = uptime_seconds
        if guest_metrics_status is not UNSET:
            field_dict["guest_metrics_status"] = guest_metrics_status
        if host_metrics_status is not UNSET:
            field_dict["host_metrics_status"] = host_metrics_status
        if cpu_used_percent is not UNSET:
            field_dict["cpu_used_percent"] = cpu_used_percent
        if ram_used_mb is not UNSET:
            field_dict["ram_used_mb"] = ram_used_mb
        if ram_total_mb is not UNSET:
            field_dict["ram_total_mb"] = ram_total_mb
        if disk_used_mb is not UNSET:
            field_dict["disk_used_mb"] = disk_used_mb
        if disk_total_mb is not UNSET:
            field_dict["disk_total_mb"] = disk_total_mb
        if network_rx_bytes is not UNSET:
            field_dict["network_rx_bytes"] = network_rx_bytes
        if network_tx_bytes is not UNSET:
            field_dict["network_tx_bytes"] = network_tx_bytes
        if disk_read_bytes is not UNSET:
            field_dict["disk_read_bytes"] = disk_read_bytes
        if disk_write_bytes is not UNSET:
            field_dict["disk_write_bytes"] = disk_write_bytes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_observed_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        observed_at = _parse_observed_at(d.pop("observed_at", UNSET))

        stale = d.pop("stale", UNSET)

        partial = d.pop("partial", UNSET)

        def _parse_runtime_instance_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        runtime_instance_id = _parse_runtime_instance_id(
            d.pop("runtime_instance_id", UNSET)
        )

        def _parse_uptime_seconds(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        uptime_seconds = _parse_uptime_seconds(d.pop("uptime_seconds", UNSET))

        def _parse_guest_metrics_status(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        guest_metrics_status = _parse_guest_metrics_status(
            d.pop("guest_metrics_status", UNSET)
        )

        def _parse_host_metrics_status(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        host_metrics_status = _parse_host_metrics_status(
            d.pop("host_metrics_status", UNSET)
        )

        def _parse_cpu_used_percent(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        cpu_used_percent = _parse_cpu_used_percent(d.pop("cpu_used_percent", UNSET))

        def _parse_ram_used_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        ram_used_mb = _parse_ram_used_mb(d.pop("ram_used_mb", UNSET))

        def _parse_ram_total_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        ram_total_mb = _parse_ram_total_mb(d.pop("ram_total_mb", UNSET))

        def _parse_disk_used_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        disk_used_mb = _parse_disk_used_mb(d.pop("disk_used_mb", UNSET))

        def _parse_disk_total_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        disk_total_mb = _parse_disk_total_mb(d.pop("disk_total_mb", UNSET))

        def _parse_network_rx_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        network_rx_bytes = _parse_network_rx_bytes(d.pop("network_rx_bytes", UNSET))

        def _parse_network_tx_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        network_tx_bytes = _parse_network_tx_bytes(d.pop("network_tx_bytes", UNSET))

        def _parse_disk_read_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        disk_read_bytes = _parse_disk_read_bytes(d.pop("disk_read_bytes", UNSET))

        def _parse_disk_write_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        disk_write_bytes = _parse_disk_write_bytes(d.pop("disk_write_bytes", UNSET))

        computer_metrics_summary = cls(
            observed_at=observed_at,
            stale=stale,
            partial=partial,
            runtime_instance_id=runtime_instance_id,
            uptime_seconds=uptime_seconds,
            guest_metrics_status=guest_metrics_status,
            host_metrics_status=host_metrics_status,
            cpu_used_percent=cpu_used_percent,
            ram_used_mb=ram_used_mb,
            ram_total_mb=ram_total_mb,
            disk_used_mb=disk_used_mb,
            disk_total_mb=disk_total_mb,
            network_rx_bytes=network_rx_bytes,
            network_tx_bytes=network_tx_bytes,
            disk_read_bytes=disk_read_bytes,
            disk_write_bytes=disk_write_bytes,
        )

        computer_metrics_summary.additional_properties = d
        return computer_metrics_summary

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

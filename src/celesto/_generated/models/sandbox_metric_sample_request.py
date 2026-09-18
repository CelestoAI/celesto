from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
import datetime


T = TypeVar("T", bound="SandboxMetricSampleRequest")


@_attrs_define
class SandboxMetricSampleRequest:
    """Single per-sandbox telemetry sample from a host agent.

    Attributes:
        computer_id (str):
        runtime_instance_id (None | str | Unset):
        guest_boot_id (None | str | Unset):
        backend (None | str | Unset):
        status (None | str | Unset):
        guest_agent_version (None | str | Unset):
        observed_at (datetime.datetime | None | Unset):
        stale (bool | Unset):  Default: False.
        partial (bool | Unset):  Default: False.
        uptime_seconds (int | None | Unset):
        guest_metrics_status (None | str | Unset):
        host_metrics_status (None | str | Unset):
        guest_cpu_used_percent (float | None | Unset):
        guest_cpu_total_jiffies (int | None | Unset):
        guest_cpu_idle_jiffies (int | None | Unset):
        guest_ram_used_mb (int | None | Unset):
        guest_ram_total_mb (int | None | Unset):
        guest_disk_used_mb (int | None | Unset):
        guest_disk_total_mb (int | None | Unset):
        host_cpu_used_percent (float | None | Unset):
        host_memory_rss_mb (int | None | Unset):
        host_memory_limit_mb (int | None | Unset):
        host_network_rx_bytes (int | None | Unset):
        host_network_tx_bytes (int | None | Unset):
        host_disk_read_bytes (int | None | Unset):
        host_disk_write_bytes (int | None | Unset):
        host_disk_allocated_mb (int | None | Unset):
        host_disk_size_mb (int | None | Unset):
    """

    computer_id: str
    runtime_instance_id: None | str | Unset = UNSET
    guest_boot_id: None | str | Unset = UNSET
    backend: None | str | Unset = UNSET
    status: None | str | Unset = UNSET
    guest_agent_version: None | str | Unset = UNSET
    observed_at: datetime.datetime | None | Unset = UNSET
    stale: bool | Unset = False
    partial: bool | Unset = False
    uptime_seconds: int | None | Unset = UNSET
    guest_metrics_status: None | str | Unset = UNSET
    host_metrics_status: None | str | Unset = UNSET
    guest_cpu_used_percent: float | None | Unset = UNSET
    guest_cpu_total_jiffies: int | None | Unset = UNSET
    guest_cpu_idle_jiffies: int | None | Unset = UNSET
    guest_ram_used_mb: int | None | Unset = UNSET
    guest_ram_total_mb: int | None | Unset = UNSET
    guest_disk_used_mb: int | None | Unset = UNSET
    guest_disk_total_mb: int | None | Unset = UNSET
    host_cpu_used_percent: float | None | Unset = UNSET
    host_memory_rss_mb: int | None | Unset = UNSET
    host_memory_limit_mb: int | None | Unset = UNSET
    host_network_rx_bytes: int | None | Unset = UNSET
    host_network_tx_bytes: int | None | Unset = UNSET
    host_disk_read_bytes: int | None | Unset = UNSET
    host_disk_write_bytes: int | None | Unset = UNSET
    host_disk_allocated_mb: int | None | Unset = UNSET
    host_disk_size_mb: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        computer_id = self.computer_id

        runtime_instance_id: None | str | Unset
        if isinstance(self.runtime_instance_id, Unset):
            runtime_instance_id = UNSET
        else:
            runtime_instance_id = self.runtime_instance_id

        guest_boot_id: None | str | Unset
        if isinstance(self.guest_boot_id, Unset):
            guest_boot_id = UNSET
        else:
            guest_boot_id = self.guest_boot_id

        backend: None | str | Unset
        if isinstance(self.backend, Unset):
            backend = UNSET
        else:
            backend = self.backend

        status: None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        else:
            status = self.status

        guest_agent_version: None | str | Unset
        if isinstance(self.guest_agent_version, Unset):
            guest_agent_version = UNSET
        else:
            guest_agent_version = self.guest_agent_version

        observed_at: None | str | Unset
        if isinstance(self.observed_at, Unset):
            observed_at = UNSET
        elif isinstance(self.observed_at, datetime.datetime):
            observed_at = self.observed_at.isoformat()
        else:
            observed_at = self.observed_at

        stale = self.stale

        partial = self.partial

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

        guest_cpu_used_percent: float | None | Unset
        if isinstance(self.guest_cpu_used_percent, Unset):
            guest_cpu_used_percent = UNSET
        else:
            guest_cpu_used_percent = self.guest_cpu_used_percent

        guest_cpu_total_jiffies: int | None | Unset
        if isinstance(self.guest_cpu_total_jiffies, Unset):
            guest_cpu_total_jiffies = UNSET
        else:
            guest_cpu_total_jiffies = self.guest_cpu_total_jiffies

        guest_cpu_idle_jiffies: int | None | Unset
        if isinstance(self.guest_cpu_idle_jiffies, Unset):
            guest_cpu_idle_jiffies = UNSET
        else:
            guest_cpu_idle_jiffies = self.guest_cpu_idle_jiffies

        guest_ram_used_mb: int | None | Unset
        if isinstance(self.guest_ram_used_mb, Unset):
            guest_ram_used_mb = UNSET
        else:
            guest_ram_used_mb = self.guest_ram_used_mb

        guest_ram_total_mb: int | None | Unset
        if isinstance(self.guest_ram_total_mb, Unset):
            guest_ram_total_mb = UNSET
        else:
            guest_ram_total_mb = self.guest_ram_total_mb

        guest_disk_used_mb: int | None | Unset
        if isinstance(self.guest_disk_used_mb, Unset):
            guest_disk_used_mb = UNSET
        else:
            guest_disk_used_mb = self.guest_disk_used_mb

        guest_disk_total_mb: int | None | Unset
        if isinstance(self.guest_disk_total_mb, Unset):
            guest_disk_total_mb = UNSET
        else:
            guest_disk_total_mb = self.guest_disk_total_mb

        host_cpu_used_percent: float | None | Unset
        if isinstance(self.host_cpu_used_percent, Unset):
            host_cpu_used_percent = UNSET
        else:
            host_cpu_used_percent = self.host_cpu_used_percent

        host_memory_rss_mb: int | None | Unset
        if isinstance(self.host_memory_rss_mb, Unset):
            host_memory_rss_mb = UNSET
        else:
            host_memory_rss_mb = self.host_memory_rss_mb

        host_memory_limit_mb: int | None | Unset
        if isinstance(self.host_memory_limit_mb, Unset):
            host_memory_limit_mb = UNSET
        else:
            host_memory_limit_mb = self.host_memory_limit_mb

        host_network_rx_bytes: int | None | Unset
        if isinstance(self.host_network_rx_bytes, Unset):
            host_network_rx_bytes = UNSET
        else:
            host_network_rx_bytes = self.host_network_rx_bytes

        host_network_tx_bytes: int | None | Unset
        if isinstance(self.host_network_tx_bytes, Unset):
            host_network_tx_bytes = UNSET
        else:
            host_network_tx_bytes = self.host_network_tx_bytes

        host_disk_read_bytes: int | None | Unset
        if isinstance(self.host_disk_read_bytes, Unset):
            host_disk_read_bytes = UNSET
        else:
            host_disk_read_bytes = self.host_disk_read_bytes

        host_disk_write_bytes: int | None | Unset
        if isinstance(self.host_disk_write_bytes, Unset):
            host_disk_write_bytes = UNSET
        else:
            host_disk_write_bytes = self.host_disk_write_bytes

        host_disk_allocated_mb: int | None | Unset
        if isinstance(self.host_disk_allocated_mb, Unset):
            host_disk_allocated_mb = UNSET
        else:
            host_disk_allocated_mb = self.host_disk_allocated_mb

        host_disk_size_mb: int | None | Unset
        if isinstance(self.host_disk_size_mb, Unset):
            host_disk_size_mb = UNSET
        else:
            host_disk_size_mb = self.host_disk_size_mb

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "computer_id": computer_id,
            }
        )
        if runtime_instance_id is not UNSET:
            field_dict["runtime_instance_id"] = runtime_instance_id
        if guest_boot_id is not UNSET:
            field_dict["guest_boot_id"] = guest_boot_id
        if backend is not UNSET:
            field_dict["backend"] = backend
        if status is not UNSET:
            field_dict["status"] = status
        if guest_agent_version is not UNSET:
            field_dict["guest_agent_version"] = guest_agent_version
        if observed_at is not UNSET:
            field_dict["observed_at"] = observed_at
        if stale is not UNSET:
            field_dict["stale"] = stale
        if partial is not UNSET:
            field_dict["partial"] = partial
        if uptime_seconds is not UNSET:
            field_dict["uptime_seconds"] = uptime_seconds
        if guest_metrics_status is not UNSET:
            field_dict["guest_metrics_status"] = guest_metrics_status
        if host_metrics_status is not UNSET:
            field_dict["host_metrics_status"] = host_metrics_status
        if guest_cpu_used_percent is not UNSET:
            field_dict["guest_cpu_used_percent"] = guest_cpu_used_percent
        if guest_cpu_total_jiffies is not UNSET:
            field_dict["guest_cpu_total_jiffies"] = guest_cpu_total_jiffies
        if guest_cpu_idle_jiffies is not UNSET:
            field_dict["guest_cpu_idle_jiffies"] = guest_cpu_idle_jiffies
        if guest_ram_used_mb is not UNSET:
            field_dict["guest_ram_used_mb"] = guest_ram_used_mb
        if guest_ram_total_mb is not UNSET:
            field_dict["guest_ram_total_mb"] = guest_ram_total_mb
        if guest_disk_used_mb is not UNSET:
            field_dict["guest_disk_used_mb"] = guest_disk_used_mb
        if guest_disk_total_mb is not UNSET:
            field_dict["guest_disk_total_mb"] = guest_disk_total_mb
        if host_cpu_used_percent is not UNSET:
            field_dict["host_cpu_used_percent"] = host_cpu_used_percent
        if host_memory_rss_mb is not UNSET:
            field_dict["host_memory_rss_mb"] = host_memory_rss_mb
        if host_memory_limit_mb is not UNSET:
            field_dict["host_memory_limit_mb"] = host_memory_limit_mb
        if host_network_rx_bytes is not UNSET:
            field_dict["host_network_rx_bytes"] = host_network_rx_bytes
        if host_network_tx_bytes is not UNSET:
            field_dict["host_network_tx_bytes"] = host_network_tx_bytes
        if host_disk_read_bytes is not UNSET:
            field_dict["host_disk_read_bytes"] = host_disk_read_bytes
        if host_disk_write_bytes is not UNSET:
            field_dict["host_disk_write_bytes"] = host_disk_write_bytes
        if host_disk_allocated_mb is not UNSET:
            field_dict["host_disk_allocated_mb"] = host_disk_allocated_mb
        if host_disk_size_mb is not UNSET:
            field_dict["host_disk_size_mb"] = host_disk_size_mb

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        computer_id = d.pop("computer_id")

        def _parse_runtime_instance_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        runtime_instance_id = _parse_runtime_instance_id(
            d.pop("runtime_instance_id", UNSET)
        )

        def _parse_guest_boot_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        guest_boot_id = _parse_guest_boot_id(d.pop("guest_boot_id", UNSET))

        def _parse_backend(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        backend = _parse_backend(d.pop("backend", UNSET))

        def _parse_status(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_guest_agent_version(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        guest_agent_version = _parse_guest_agent_version(
            d.pop("guest_agent_version", UNSET)
        )

        def _parse_observed_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                observed_at_type_0 = datetime.datetime.fromisoformat(data)

                return observed_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        observed_at = _parse_observed_at(d.pop("observed_at", UNSET))

        stale = d.pop("stale", UNSET)

        partial = d.pop("partial", UNSET)

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

        def _parse_guest_cpu_used_percent(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        guest_cpu_used_percent = _parse_guest_cpu_used_percent(
            d.pop("guest_cpu_used_percent", UNSET)
        )

        def _parse_guest_cpu_total_jiffies(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        guest_cpu_total_jiffies = _parse_guest_cpu_total_jiffies(
            d.pop("guest_cpu_total_jiffies", UNSET)
        )

        def _parse_guest_cpu_idle_jiffies(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        guest_cpu_idle_jiffies = _parse_guest_cpu_idle_jiffies(
            d.pop("guest_cpu_idle_jiffies", UNSET)
        )

        def _parse_guest_ram_used_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        guest_ram_used_mb = _parse_guest_ram_used_mb(d.pop("guest_ram_used_mb", UNSET))

        def _parse_guest_ram_total_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        guest_ram_total_mb = _parse_guest_ram_total_mb(
            d.pop("guest_ram_total_mb", UNSET)
        )

        def _parse_guest_disk_used_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        guest_disk_used_mb = _parse_guest_disk_used_mb(
            d.pop("guest_disk_used_mb", UNSET)
        )

        def _parse_guest_disk_total_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        guest_disk_total_mb = _parse_guest_disk_total_mb(
            d.pop("guest_disk_total_mb", UNSET)
        )

        def _parse_host_cpu_used_percent(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        host_cpu_used_percent = _parse_host_cpu_used_percent(
            d.pop("host_cpu_used_percent", UNSET)
        )

        def _parse_host_memory_rss_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        host_memory_rss_mb = _parse_host_memory_rss_mb(
            d.pop("host_memory_rss_mb", UNSET)
        )

        def _parse_host_memory_limit_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        host_memory_limit_mb = _parse_host_memory_limit_mb(
            d.pop("host_memory_limit_mb", UNSET)
        )

        def _parse_host_network_rx_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        host_network_rx_bytes = _parse_host_network_rx_bytes(
            d.pop("host_network_rx_bytes", UNSET)
        )

        def _parse_host_network_tx_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        host_network_tx_bytes = _parse_host_network_tx_bytes(
            d.pop("host_network_tx_bytes", UNSET)
        )

        def _parse_host_disk_read_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        host_disk_read_bytes = _parse_host_disk_read_bytes(
            d.pop("host_disk_read_bytes", UNSET)
        )

        def _parse_host_disk_write_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        host_disk_write_bytes = _parse_host_disk_write_bytes(
            d.pop("host_disk_write_bytes", UNSET)
        )

        def _parse_host_disk_allocated_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        host_disk_allocated_mb = _parse_host_disk_allocated_mb(
            d.pop("host_disk_allocated_mb", UNSET)
        )

        def _parse_host_disk_size_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        host_disk_size_mb = _parse_host_disk_size_mb(d.pop("host_disk_size_mb", UNSET))

        sandbox_metric_sample_request = cls(
            computer_id=computer_id,
            runtime_instance_id=runtime_instance_id,
            guest_boot_id=guest_boot_id,
            backend=backend,
            status=status,
            guest_agent_version=guest_agent_version,
            observed_at=observed_at,
            stale=stale,
            partial=partial,
            uptime_seconds=uptime_seconds,
            guest_metrics_status=guest_metrics_status,
            host_metrics_status=host_metrics_status,
            guest_cpu_used_percent=guest_cpu_used_percent,
            guest_cpu_total_jiffies=guest_cpu_total_jiffies,
            guest_cpu_idle_jiffies=guest_cpu_idle_jiffies,
            guest_ram_used_mb=guest_ram_used_mb,
            guest_ram_total_mb=guest_ram_total_mb,
            guest_disk_used_mb=guest_disk_used_mb,
            guest_disk_total_mb=guest_disk_total_mb,
            host_cpu_used_percent=host_cpu_used_percent,
            host_memory_rss_mb=host_memory_rss_mb,
            host_memory_limit_mb=host_memory_limit_mb,
            host_network_rx_bytes=host_network_rx_bytes,
            host_network_tx_bytes=host_network_tx_bytes,
            host_disk_read_bytes=host_disk_read_bytes,
            host_disk_write_bytes=host_disk_write_bytes,
            host_disk_allocated_mb=host_disk_allocated_mb,
            host_disk_size_mb=host_disk_size_mb,
        )

        sandbox_metric_sample_request.additional_properties = d
        return sandbox_metric_sample_request

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

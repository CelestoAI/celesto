from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="SandboxMetricSampleResponse")


@_attrs_define
class SandboxMetricSampleResponse:
    """
    Attributes:
        observed_at (str):
        partial (bool | Unset):  Default: False.
        stale (bool | Unset):  Default: False.
        guest_metrics_status (None | str | Unset):
        host_metrics_status (None | str | Unset):
        guest_cpu_used_percent (float | None | Unset):
        guest_ram_used_mb (int | None | Unset):
        guest_ram_total_mb (int | None | Unset):
        guest_disk_used_mb (int | None | Unset):
        guest_disk_total_mb (int | None | Unset):
        uptime_seconds (int | None | Unset):
        host_cpu_used_percent (float | None | Unset):
        host_memory_rss_mb (int | None | Unset):
        host_network_rx_bytes (int | None | Unset):
        host_network_tx_bytes (int | None | Unset):
        host_disk_read_bytes (int | None | Unset):
        host_disk_write_bytes (int | None | Unset):
    """

    observed_at: str
    partial: bool | Unset = False
    stale: bool | Unset = False
    guest_metrics_status: None | str | Unset = UNSET
    host_metrics_status: None | str | Unset = UNSET
    guest_cpu_used_percent: float | None | Unset = UNSET
    guest_ram_used_mb: int | None | Unset = UNSET
    guest_ram_total_mb: int | None | Unset = UNSET
    guest_disk_used_mb: int | None | Unset = UNSET
    guest_disk_total_mb: int | None | Unset = UNSET
    uptime_seconds: int | None | Unset = UNSET
    host_cpu_used_percent: float | None | Unset = UNSET
    host_memory_rss_mb: int | None | Unset = UNSET
    host_network_rx_bytes: int | None | Unset = UNSET
    host_network_tx_bytes: int | None | Unset = UNSET
    host_disk_read_bytes: int | None | Unset = UNSET
    host_disk_write_bytes: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        observed_at = self.observed_at

        partial = self.partial

        stale = self.stale

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

        uptime_seconds: int | None | Unset
        if isinstance(self.uptime_seconds, Unset):
            uptime_seconds = UNSET
        else:
            uptime_seconds = self.uptime_seconds

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

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "observed_at": observed_at,
            }
        )
        if partial is not UNSET:
            field_dict["partial"] = partial
        if stale is not UNSET:
            field_dict["stale"] = stale
        if guest_metrics_status is not UNSET:
            field_dict["guest_metrics_status"] = guest_metrics_status
        if host_metrics_status is not UNSET:
            field_dict["host_metrics_status"] = host_metrics_status
        if guest_cpu_used_percent is not UNSET:
            field_dict["guest_cpu_used_percent"] = guest_cpu_used_percent
        if guest_ram_used_mb is not UNSET:
            field_dict["guest_ram_used_mb"] = guest_ram_used_mb
        if guest_ram_total_mb is not UNSET:
            field_dict["guest_ram_total_mb"] = guest_ram_total_mb
        if guest_disk_used_mb is not UNSET:
            field_dict["guest_disk_used_mb"] = guest_disk_used_mb
        if guest_disk_total_mb is not UNSET:
            field_dict["guest_disk_total_mb"] = guest_disk_total_mb
        if uptime_seconds is not UNSET:
            field_dict["uptime_seconds"] = uptime_seconds
        if host_cpu_used_percent is not UNSET:
            field_dict["host_cpu_used_percent"] = host_cpu_used_percent
        if host_memory_rss_mb is not UNSET:
            field_dict["host_memory_rss_mb"] = host_memory_rss_mb
        if host_network_rx_bytes is not UNSET:
            field_dict["host_network_rx_bytes"] = host_network_rx_bytes
        if host_network_tx_bytes is not UNSET:
            field_dict["host_network_tx_bytes"] = host_network_tx_bytes
        if host_disk_read_bytes is not UNSET:
            field_dict["host_disk_read_bytes"] = host_disk_read_bytes
        if host_disk_write_bytes is not UNSET:
            field_dict["host_disk_write_bytes"] = host_disk_write_bytes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        observed_at = d.pop("observed_at")

        partial = d.pop("partial", UNSET)

        stale = d.pop("stale", UNSET)

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

        def _parse_uptime_seconds(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        uptime_seconds = _parse_uptime_seconds(d.pop("uptime_seconds", UNSET))

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

        sandbox_metric_sample_response = cls(
            observed_at=observed_at,
            partial=partial,
            stale=stale,
            guest_metrics_status=guest_metrics_status,
            host_metrics_status=host_metrics_status,
            guest_cpu_used_percent=guest_cpu_used_percent,
            guest_ram_used_mb=guest_ram_used_mb,
            guest_ram_total_mb=guest_ram_total_mb,
            guest_disk_used_mb=guest_disk_used_mb,
            guest_disk_total_mb=guest_disk_total_mb,
            uptime_seconds=uptime_seconds,
            host_cpu_used_percent=host_cpu_used_percent,
            host_memory_rss_mb=host_memory_rss_mb,
            host_network_rx_bytes=host_network_rx_bytes,
            host_network_tx_bytes=host_network_tx_bytes,
            host_disk_read_bytes=host_disk_read_bytes,
            host_disk_write_bytes=host_disk_write_bytes,
        )

        sandbox_metric_sample_response.additional_properties = d
        return sandbox_metric_sample_response

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

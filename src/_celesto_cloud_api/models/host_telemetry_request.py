from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.sandbox_metric_sample_request import SandboxMetricSampleRequest


T = TypeVar("T", bound="HostTelemetryRequest")


@_attrs_define
class HostTelemetryRequest:
    """Telemetry batch from a host agent.

    Attributes:
        host_boot_id (None | str | Unset):
        agent_version (None | str | Unset):
        samples (list[SandboxMetricSampleRequest] | Unset):
    """

    host_boot_id: None | str | Unset = UNSET
    agent_version: None | str | Unset = UNSET
    samples: list[SandboxMetricSampleRequest] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.sandbox_metric_sample_request import SandboxMetricSampleRequest  # noqa: PLC0415

        host_boot_id: None | str | Unset
        if isinstance(self.host_boot_id, Unset):
            host_boot_id = UNSET
        else:
            host_boot_id = self.host_boot_id

        agent_version: None | str | Unset
        if isinstance(self.agent_version, Unset):
            agent_version = UNSET
        else:
            agent_version = self.agent_version

        samples: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.samples, Unset):
            samples = []
            for samples_item_data in self.samples:
                samples_item = samples_item_data.to_dict()
                samples.append(samples_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if host_boot_id is not UNSET:
            field_dict["host_boot_id"] = host_boot_id
        if agent_version is not UNSET:
            field_dict["agent_version"] = agent_version
        if samples is not UNSET:
            field_dict["samples"] = samples

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sandbox_metric_sample_request import SandboxMetricSampleRequest  # noqa: PLC0415

        d = dict(src_dict)

        def _parse_host_boot_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        host_boot_id = _parse_host_boot_id(d.pop("host_boot_id", UNSET))

        def _parse_agent_version(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        agent_version = _parse_agent_version(d.pop("agent_version", UNSET))

        _samples = d.pop("samples", UNSET)
        samples: list[SandboxMetricSampleRequest] | Unset = UNSET
        if _samples is not UNSET:
            samples = []
            for samples_item_data in _samples:
                samples_item = SandboxMetricSampleRequest.from_dict(samples_item_data)

                samples.append(samples_item)

        host_telemetry_request = cls(
            host_boot_id=host_boot_id,
            agent_version=agent_version,
            samples=samples,
        )

        host_telemetry_request.additional_properties = d
        return host_telemetry_request

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.computer_metrics_summary import ComputerMetricsSummary
    from ..models.sandbox_metric_sample_response import SandboxMetricSampleResponse


T = TypeVar("T", bound="ComputerObservabilityResponse")


@_attrs_define
class ComputerObservabilityResponse:
    """
    Attributes:
        latest (ComputerMetricsSummary | None | Unset):
        samples (list[SandboxMetricSampleResponse] | Unset):
    """

    latest: ComputerMetricsSummary | None | Unset = UNSET
    samples: list[SandboxMetricSampleResponse] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.computer_metrics_summary import ComputerMetricsSummary  # noqa: PLC0415
        from ..models.sandbox_metric_sample_response import SandboxMetricSampleResponse  # noqa: PLC0415

        latest: dict[str, Any] | None | Unset
        if isinstance(self.latest, Unset):
            latest = UNSET
        elif isinstance(self.latest, ComputerMetricsSummary):
            latest = self.latest.to_dict()
        else:
            latest = self.latest

        samples: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.samples, Unset):
            samples = []
            for samples_item_data in self.samples:
                samples_item = samples_item_data.to_dict()
                samples.append(samples_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if latest is not UNSET:
            field_dict["latest"] = latest
        if samples is not UNSET:
            field_dict["samples"] = samples

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.computer_metrics_summary import ComputerMetricsSummary  # noqa: PLC0415
        from ..models.sandbox_metric_sample_response import SandboxMetricSampleResponse  # noqa: PLC0415

        d = dict(src_dict)

        def _parse_latest(data: object) -> ComputerMetricsSummary | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                latest_type_0 = ComputerMetricsSummary.from_dict(data)

                return latest_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ComputerMetricsSummary | None | Unset, data)

        latest = _parse_latest(d.pop("latest", UNSET))

        _samples = d.pop("samples", UNSET)
        samples: list[SandboxMetricSampleResponse] | Unset = UNSET
        if _samples is not UNSET:
            samples = []
            for samples_item_data in _samples:
                samples_item = SandboxMetricSampleResponse.from_dict(samples_item_data)

                samples.append(samples_item)

        computer_observability_response = cls(
            latest=latest,
            samples=samples,
        )

        computer_observability_response.additional_properties = d
        return computer_observability_response

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

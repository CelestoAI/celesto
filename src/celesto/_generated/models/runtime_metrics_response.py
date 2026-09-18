from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast

if TYPE_CHECKING:
    from ..models.metrics_runs_day import MetricsRunsDay
    from ..models.metrics_spend_day import MetricsSpendDay
    from ..models.runtime_metrics_totals import RuntimeMetricsTotals


T = TypeVar("T", bound="RuntimeMetricsResponse")


@_attrs_define
class RuntimeMetricsResponse:
    """
    Attributes:
        runs_by_day (list[MetricsRunsDay]):
        spend_by_day (list[MetricsSpendDay]):
        totals (RuntimeMetricsTotals):
    """

    runs_by_day: list[MetricsRunsDay]
    spend_by_day: list[MetricsSpendDay]
    totals: RuntimeMetricsTotals
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.metrics_runs_day import MetricsRunsDay  # noqa: PLC0415
        from ..models.metrics_spend_day import MetricsSpendDay  # noqa: PLC0415
        from ..models.runtime_metrics_totals import RuntimeMetricsTotals  # noqa: PLC0415

        runs_by_day = []
        for runs_by_day_item_data in self.runs_by_day:
            runs_by_day_item = runs_by_day_item_data.to_dict()
            runs_by_day.append(runs_by_day_item)

        spend_by_day = []
        for spend_by_day_item_data in self.spend_by_day:
            spend_by_day_item = spend_by_day_item_data.to_dict()
            spend_by_day.append(spend_by_day_item)

        totals = self.totals.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "runs_by_day": runs_by_day,
                "spend_by_day": spend_by_day,
                "totals": totals,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.metrics_runs_day import MetricsRunsDay  # noqa: PLC0415
        from ..models.metrics_spend_day import MetricsSpendDay  # noqa: PLC0415
        from ..models.runtime_metrics_totals import RuntimeMetricsTotals  # noqa: PLC0415

        d = dict(src_dict)
        runs_by_day = []
        _runs_by_day = d.pop("runs_by_day")
        for runs_by_day_item_data in _runs_by_day:
            runs_by_day_item = MetricsRunsDay.from_dict(runs_by_day_item_data)

            runs_by_day.append(runs_by_day_item)

        spend_by_day = []
        _spend_by_day = d.pop("spend_by_day")
        for spend_by_day_item_data in _spend_by_day:
            spend_by_day_item = MetricsSpendDay.from_dict(spend_by_day_item_data)

            spend_by_day.append(spend_by_day_item)

        totals = RuntimeMetricsTotals.from_dict(d.pop("totals"))

        runtime_metrics_response = cls(
            runs_by_day=runs_by_day,
            spend_by_day=spend_by_day,
            totals=totals,
        )

        runtime_metrics_response.additional_properties = d
        return runtime_metrics_response

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

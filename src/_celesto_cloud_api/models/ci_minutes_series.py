from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.ci_minutes_series_days import CiMinutesSeriesDays
from ..models.ci_minutes_series_interval import CiMinutesSeriesInterval
from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.ci_minutes_bucket import CiMinutesBucket


T = TypeVar("T", bound="CiMinutesSeries")


@_attrs_define
class CiMinutesSeries:
    """Platform-wide CI minutes over time, plus the same-length period before it.

    Attributes:
        observed_at (datetime.datetime):
        interval (CiMinutesSeriesInterval):
        days (CiMinutesSeriesDays):
        runtime_coverage_started_at (datetime.datetime | None):
        total_minutes (float):
        previous_total_minutes (float | None):
        buckets (list[CiMinutesBucket]):
        previous_buckets (list[CiMinutesBucket]):
    """

    observed_at: datetime.datetime
    interval: CiMinutesSeriesInterval
    days: CiMinutesSeriesDays
    runtime_coverage_started_at: datetime.datetime | None
    total_minutes: float
    previous_total_minutes: float | None
    buckets: list[CiMinutesBucket]
    previous_buckets: list[CiMinutesBucket]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.ci_minutes_bucket import CiMinutesBucket  # noqa: PLC0415

        observed_at = self.observed_at.isoformat()

        interval = self.interval.value

        days = self.days.value

        runtime_coverage_started_at: None | str
        if isinstance(self.runtime_coverage_started_at, datetime.datetime):
            runtime_coverage_started_at = self.runtime_coverage_started_at.isoformat()
        else:
            runtime_coverage_started_at = self.runtime_coverage_started_at

        total_minutes = self.total_minutes

        previous_total_minutes: float | None
        previous_total_minutes = self.previous_total_minutes

        buckets = []
        for buckets_item_data in self.buckets:
            buckets_item = buckets_item_data.to_dict()
            buckets.append(buckets_item)

        previous_buckets = []
        for previous_buckets_item_data in self.previous_buckets:
            previous_buckets_item = previous_buckets_item_data.to_dict()
            previous_buckets.append(previous_buckets_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "observed_at": observed_at,
                "interval": interval,
                "days": days,
                "runtime_coverage_started_at": runtime_coverage_started_at,
                "total_minutes": total_minutes,
                "previous_total_minutes": previous_total_minutes,
                "buckets": buckets,
                "previous_buckets": previous_buckets,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.ci_minutes_bucket import CiMinutesBucket  # noqa: PLC0415

        d = dict(src_dict)
        observed_at = datetime.datetime.fromisoformat(d.pop("observed_at"))

        interval = CiMinutesSeriesInterval(d.pop("interval"))

        days = CiMinutesSeriesDays(d.pop("days"))

        def _parse_runtime_coverage_started_at(
            data: object,
        ) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                runtime_coverage_started_at_type_0 = datetime.datetime.fromisoformat(
                    data
                )

                return runtime_coverage_started_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        runtime_coverage_started_at = _parse_runtime_coverage_started_at(
            d.pop("runtime_coverage_started_at")
        )

        total_minutes = d.pop("total_minutes")

        def _parse_previous_total_minutes(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        previous_total_minutes = _parse_previous_total_minutes(
            d.pop("previous_total_minutes")
        )

        buckets = []
        _buckets = d.pop("buckets")
        for buckets_item_data in _buckets:
            buckets_item = CiMinutesBucket.from_dict(buckets_item_data)

            buckets.append(buckets_item)

        previous_buckets = []
        _previous_buckets = d.pop("previous_buckets")
        for previous_buckets_item_data in _previous_buckets:
            previous_buckets_item = CiMinutesBucket.from_dict(
                previous_buckets_item_data
            )

            previous_buckets.append(previous_buckets_item)

        ci_minutes_series = cls(
            observed_at=observed_at,
            interval=interval,
            days=days,
            runtime_coverage_started_at=runtime_coverage_started_at,
            total_minutes=total_minutes,
            previous_total_minutes=previous_total_minutes,
            buckets=buckets,
            previous_buckets=previous_buckets,
        )

        ci_minutes_series.additional_properties = d
        return ci_minutes_series

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

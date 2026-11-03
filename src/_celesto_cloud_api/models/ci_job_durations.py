from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast


T = TypeVar("T", bound="CiJobDurations")


@_attrs_define
class CiJobDurations:
    """
    Attributes:
        jobs (int):
        timed_jobs (int):
        average_minutes (float | None):
        median_minutes (float | None):
        p95_minutes (float | None):
    """

    jobs: int
    timed_jobs: int
    average_minutes: float | None
    median_minutes: float | None
    p95_minutes: float | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        jobs = self.jobs

        timed_jobs = self.timed_jobs

        average_minutes: float | None
        average_minutes = self.average_minutes

        median_minutes: float | None
        median_minutes = self.median_minutes

        p95_minutes: float | None
        p95_minutes = self.p95_minutes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "jobs": jobs,
                "timed_jobs": timed_jobs,
                "average_minutes": average_minutes,
                "median_minutes": median_minutes,
                "p95_minutes": p95_minutes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        jobs = d.pop("jobs")

        timed_jobs = d.pop("timed_jobs")

        def _parse_average_minutes(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        average_minutes = _parse_average_minutes(d.pop("average_minutes"))

        def _parse_median_minutes(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        median_minutes = _parse_median_minutes(d.pop("median_minutes"))

        def _parse_p95_minutes(data: object) -> float | None:
            if data is None:
                return data
            return cast(float | None, data)

        p95_minutes = _parse_p95_minutes(d.pop("p95_minutes"))

        ci_job_durations = cls(
            jobs=jobs,
            timed_jobs=timed_jobs,
            average_minutes=average_minutes,
            median_minutes=median_minutes,
            p95_minutes=p95_minutes,
        )

        ci_job_durations.additional_properties = d
        return ci_job_durations

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

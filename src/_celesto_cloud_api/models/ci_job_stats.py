from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.ci_job_durations import CiJobDurations
    from ..models.ci_machine_job_stats import CiMachineJobStats


T = TypeVar("T", bound="CiJobStats")


@_attrs_define
class CiJobStats:
    """
    Attributes:
        observed_at (datetime.datetime):
        started_at (datetime.datetime):
        ended_at (datetime.datetime):
        machines (list[CiMachineJobStats]):
        total (CiJobDurations):
    """

    observed_at: datetime.datetime
    started_at: datetime.datetime
    ended_at: datetime.datetime
    machines: list[CiMachineJobStats]
    total: CiJobDurations
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.ci_job_durations import CiJobDurations  # noqa: PLC0415
        from ..models.ci_machine_job_stats import CiMachineJobStats  # noqa: PLC0415

        observed_at = self.observed_at.isoformat()

        started_at = self.started_at.isoformat()

        ended_at = self.ended_at.isoformat()

        machines = []
        for machines_item_data in self.machines:
            machines_item = machines_item_data.to_dict()
            machines.append(machines_item)

        total = self.total.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "observed_at": observed_at,
                "started_at": started_at,
                "ended_at": ended_at,
                "machines": machines,
                "total": total,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.ci_job_durations import CiJobDurations  # noqa: PLC0415
        from ..models.ci_machine_job_stats import CiMachineJobStats  # noqa: PLC0415

        d = dict(src_dict)
        observed_at = datetime.datetime.fromisoformat(d.pop("observed_at"))

        started_at = datetime.datetime.fromisoformat(d.pop("started_at"))

        ended_at = datetime.datetime.fromisoformat(d.pop("ended_at"))

        machines = []
        _machines = d.pop("machines")
        for machines_item_data in _machines:
            machines_item = CiMachineJobStats.from_dict(machines_item_data)

            machines.append(machines_item)

        total = CiJobDurations.from_dict(d.pop("total"))

        ci_job_stats = cls(
            observed_at=observed_at,
            started_at=started_at,
            ended_at=ended_at,
            machines=machines,
            total=total,
        )

        ci_job_stats.additional_properties = d
        return ci_job_stats

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

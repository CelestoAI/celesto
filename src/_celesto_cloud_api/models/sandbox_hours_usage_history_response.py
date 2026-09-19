from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.sandbox_hours_usage_bucket import SandboxHoursUsageBucket


T = TypeVar("T", bound="SandboxHoursUsageHistoryResponse")


@_attrs_define
class SandboxHoursUsageHistoryResponse:
    """Sandbox-hour usage aggregated from tracked Autumn events.

    Spans billing cycles, unlike the per-cycle balance in the billing summary.

        Attributes:
            range_ (str): Range the usage was aggregated over
            total_hours (str): Total sandbox-hours consumed across the range
            event_count (int): Number of usage events in the range
            buckets (list[SandboxHoursUsageBucket] | Unset): Daily usage bins, oldest first
    """

    range_: str
    total_hours: str
    event_count: int
    buckets: list[SandboxHoursUsageBucket] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.sandbox_hours_usage_bucket import SandboxHoursUsageBucket  # noqa: PLC0415

        range_ = self.range_

        total_hours = self.total_hours

        event_count = self.event_count

        buckets: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.buckets, Unset):
            buckets = []
            for buckets_item_data in self.buckets:
                buckets_item = buckets_item_data.to_dict()
                buckets.append(buckets_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "range": range_,
                "total_hours": total_hours,
                "event_count": event_count,
            }
        )
        if buckets is not UNSET:
            field_dict["buckets"] = buckets

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sandbox_hours_usage_bucket import SandboxHoursUsageBucket  # noqa: PLC0415

        d = dict(src_dict)
        range_ = d.pop("range")

        total_hours = d.pop("total_hours")

        event_count = d.pop("event_count")

        _buckets = d.pop("buckets", UNSET)
        buckets: list[SandboxHoursUsageBucket] | Unset = UNSET
        if _buckets is not UNSET:
            buckets = []
            for buckets_item_data in _buckets:
                buckets_item = SandboxHoursUsageBucket.from_dict(buckets_item_data)

                buckets.append(buckets_item)

        sandbox_hours_usage_history_response = cls(
            range_=range_,
            total_hours=total_hours,
            event_count=event_count,
            buckets=buckets,
        )

        sandbox_hours_usage_history_response.additional_properties = d
        return sandbox_hours_usage_history_response

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

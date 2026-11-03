from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.running_sandbox_spend_response import RunningSandboxSpendResponse
    from ..models.spend_by_project_response import SpendByProjectResponse
    from ..models.spend_by_sandbox_response import SpendBySandboxResponse
    from ..models.spend_by_size_response import SpendBySizeResponse
    from ..models.spend_by_surface_response import SpendBySurfaceResponse
    from ..models.spend_day_response import SpendDayResponse


T = TypeVar("T", bound="UsageSpendResponse")


@_attrs_define
class UsageSpendResponse:
    """Where an organization's sandbox credit went over a UTC day range.

    Totals are recomputed from checkpointed runtime every 15 minutes (and
    cached for up to 5 more); ``running_now`` is read live.
    Estimates until Autumn invoices them.

        Attributes:
            from_day (datetime.date):
            to_day (datetime.date):
            total_seconds (int):
            total_estimated_cost_usd (str):
            daily (list[SpendDayResponse]):
            by_surface (list[SpendBySurfaceResponse]):
            by_size (list[SpendBySizeResponse]):
            by_project (list[SpendByProjectResponse]):
            top_sandboxes (list[SpendBySandboxResponse]):
            running_now (list[RunningSandboxSpendResponse]):
    """

    from_day: datetime.date
    to_day: datetime.date
    total_seconds: int
    total_estimated_cost_usd: str
    daily: list[SpendDayResponse]
    by_surface: list[SpendBySurfaceResponse]
    by_size: list[SpendBySizeResponse]
    by_project: list[SpendByProjectResponse]
    top_sandboxes: list[SpendBySandboxResponse]
    running_now: list[RunningSandboxSpendResponse]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.running_sandbox_spend_response import RunningSandboxSpendResponse  # noqa: PLC0415
        from ..models.spend_by_project_response import SpendByProjectResponse  # noqa: PLC0415
        from ..models.spend_by_sandbox_response import SpendBySandboxResponse  # noqa: PLC0415
        from ..models.spend_by_size_response import SpendBySizeResponse  # noqa: PLC0415
        from ..models.spend_by_surface_response import SpendBySurfaceResponse  # noqa: PLC0415
        from ..models.spend_day_response import SpendDayResponse  # noqa: PLC0415

        from_day = self.from_day.isoformat()

        to_day = self.to_day.isoformat()

        total_seconds = self.total_seconds

        total_estimated_cost_usd = self.total_estimated_cost_usd

        daily = []
        for daily_item_data in self.daily:
            daily_item = daily_item_data.to_dict()
            daily.append(daily_item)

        by_surface = []
        for by_surface_item_data in self.by_surface:
            by_surface_item = by_surface_item_data.to_dict()
            by_surface.append(by_surface_item)

        by_size = []
        for by_size_item_data in self.by_size:
            by_size_item = by_size_item_data.to_dict()
            by_size.append(by_size_item)

        by_project = []
        for by_project_item_data in self.by_project:
            by_project_item = by_project_item_data.to_dict()
            by_project.append(by_project_item)

        top_sandboxes = []
        for top_sandboxes_item_data in self.top_sandboxes:
            top_sandboxes_item = top_sandboxes_item_data.to_dict()
            top_sandboxes.append(top_sandboxes_item)

        running_now = []
        for running_now_item_data in self.running_now:
            running_now_item = running_now_item_data.to_dict()
            running_now.append(running_now_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "from_day": from_day,
                "to_day": to_day,
                "total_seconds": total_seconds,
                "total_estimated_cost_usd": total_estimated_cost_usd,
                "daily": daily,
                "by_surface": by_surface,
                "by_size": by_size,
                "by_project": by_project,
                "top_sandboxes": top_sandboxes,
                "running_now": running_now,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.running_sandbox_spend_response import RunningSandboxSpendResponse  # noqa: PLC0415
        from ..models.spend_by_project_response import SpendByProjectResponse  # noqa: PLC0415
        from ..models.spend_by_sandbox_response import SpendBySandboxResponse  # noqa: PLC0415
        from ..models.spend_by_size_response import SpendBySizeResponse  # noqa: PLC0415
        from ..models.spend_by_surface_response import SpendBySurfaceResponse  # noqa: PLC0415
        from ..models.spend_day_response import SpendDayResponse  # noqa: PLC0415

        d = dict(src_dict)
        from_day = datetime.date.fromisoformat(d.pop("from_day"))

        to_day = datetime.date.fromisoformat(d.pop("to_day"))

        total_seconds = d.pop("total_seconds")

        total_estimated_cost_usd = d.pop("total_estimated_cost_usd")

        daily = []
        _daily = d.pop("daily")
        for daily_item_data in _daily:
            daily_item = SpendDayResponse.from_dict(daily_item_data)

            daily.append(daily_item)

        by_surface = []
        _by_surface = d.pop("by_surface")
        for by_surface_item_data in _by_surface:
            by_surface_item = SpendBySurfaceResponse.from_dict(by_surface_item_data)

            by_surface.append(by_surface_item)

        by_size = []
        _by_size = d.pop("by_size")
        for by_size_item_data in _by_size:
            by_size_item = SpendBySizeResponse.from_dict(by_size_item_data)

            by_size.append(by_size_item)

        by_project = []
        _by_project = d.pop("by_project")
        for by_project_item_data in _by_project:
            by_project_item = SpendByProjectResponse.from_dict(by_project_item_data)

            by_project.append(by_project_item)

        top_sandboxes = []
        _top_sandboxes = d.pop("top_sandboxes")
        for top_sandboxes_item_data in _top_sandboxes:
            top_sandboxes_item = SpendBySandboxResponse.from_dict(
                top_sandboxes_item_data
            )

            top_sandboxes.append(top_sandboxes_item)

        running_now = []
        _running_now = d.pop("running_now")
        for running_now_item_data in _running_now:
            running_now_item = RunningSandboxSpendResponse.from_dict(
                running_now_item_data
            )

            running_now.append(running_now_item)

        usage_spend_response = cls(
            from_day=from_day,
            to_day=to_day,
            total_seconds=total_seconds,
            total_estimated_cost_usd=total_estimated_cost_usd,
            daily=daily,
            by_surface=by_surface,
            by_size=by_size,
            by_project=by_project,
            top_sandboxes=top_sandboxes,
            running_now=running_now,
        )

        usage_spend_response.additional_properties = d
        return usage_spend_response

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

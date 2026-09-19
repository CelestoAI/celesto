from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast

if TYPE_CHECKING:
    from ..models.task_monitor_response import TaskMonitorResponse


T = TypeVar("T", bound="TaskMonitorListResponse")


@_attrs_define
class TaskMonitorListResponse:
    """Paginated response model for task monitor entries.

    Attributes:
        tasks (list[TaskMonitorResponse]):
        total (int):
        page (int):
        page_size (int):
        has_next (bool):
    """

    tasks: list[TaskMonitorResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.task_monitor_response import TaskMonitorResponse  # noqa: PLC0415

        tasks = []
        for tasks_item_data in self.tasks:
            tasks_item = tasks_item_data.to_dict()
            tasks.append(tasks_item)

        total = self.total

        page = self.page

        page_size = self.page_size

        has_next = self.has_next

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tasks": tasks,
                "total": total,
                "page": page,
                "page_size": page_size,
                "has_next": has_next,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.task_monitor_response import TaskMonitorResponse  # noqa: PLC0415

        d = dict(src_dict)
        tasks = []
        _tasks = d.pop("tasks")
        for tasks_item_data in _tasks:
            tasks_item = TaskMonitorResponse.from_dict(tasks_item_data)

            tasks.append(tasks_item)

        total = d.pop("total")

        page = d.pop("page")

        page_size = d.pop("page_size")

        has_next = d.pop("has_next")

        task_monitor_list_response = cls(
            tasks=tasks,
            total=total,
            page=page,
            page_size=page_size,
            has_next=has_next,
        )

        task_monitor_list_response.additional_properties = d
        return task_monitor_list_response

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

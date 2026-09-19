from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.task_input_type import TaskInputType


T = TypeVar("T", bound="TaskMonitorRequest")


@_attrs_define
class TaskMonitorRequest:
    """
    Attributes:
        organization_id (str):
        input_ (TaskInputType):
        task_type (None | str | Unset): Optional override for task type column
    """

    organization_id: str
    input_: TaskInputType
    task_type: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.task_input_type import TaskInputType  # noqa: PLC0415

        organization_id = self.organization_id

        input_ = self.input_.to_dict()

        task_type: None | str | Unset
        if isinstance(self.task_type, Unset):
            task_type = UNSET
        else:
            task_type = self.task_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "organization_id": organization_id,
                "input": input_,
            }
        )
        if task_type is not UNSET:
            field_dict["task_type"] = task_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.task_input_type import TaskInputType  # noqa: PLC0415

        d = dict(src_dict)
        organization_id = d.pop("organization_id")

        input_ = TaskInputType.from_dict(d.pop("input"))

        def _parse_task_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        task_type = _parse_task_type(d.pop("task_type", UNSET))

        task_monitor_request = cls(
            organization_id=organization_id,
            input_=input_,
            task_type=task_type,
        )

        task_monitor_request.additional_properties = d
        return task_monitor_request

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

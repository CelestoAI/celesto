from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.status import Status
from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.task_input_type import TaskInputType
    from ..models.task_monitor_response_output_type_0 import (
        TaskMonitorResponseOutputType0,
    )


T = TypeVar("T", bound="TaskMonitorResponse")


@_attrs_define
class TaskMonitorResponse:
    """
    Attributes:
        id (str):
        input_ (TaskInputType):
        status (Status):
        output (None | TaskMonitorResponseOutputType0 | Unset):
        task_type (None | str | Unset): Task category for quick filtering
    """

    id: str
    input_: TaskInputType
    status: Status
    output: None | TaskMonitorResponseOutputType0 | Unset = UNSET
    task_type: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.task_input_type import TaskInputType  # noqa: PLC0415
        from ..models.task_monitor_response_output_type_0 import (
            TaskMonitorResponseOutputType0,
        )  # noqa: PLC0415

        id = self.id

        input_ = self.input_.to_dict()

        status = self.status.value

        output: dict[str, Any] | None | Unset
        if isinstance(self.output, Unset):
            output = UNSET
        elif isinstance(self.output, TaskMonitorResponseOutputType0):
            output = self.output.to_dict()
        else:
            output = self.output

        task_type: None | str | Unset
        if isinstance(self.task_type, Unset):
            task_type = UNSET
        else:
            task_type = self.task_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "input": input_,
                "status": status,
            }
        )
        if output is not UNSET:
            field_dict["output"] = output
        if task_type is not UNSET:
            field_dict["task_type"] = task_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.task_input_type import TaskInputType  # noqa: PLC0415
        from ..models.task_monitor_response_output_type_0 import (
            TaskMonitorResponseOutputType0,
        )  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        input_ = TaskInputType.from_dict(d.pop("input"))

        status = Status(d.pop("status"))

        def _parse_output(
            data: object,
        ) -> None | TaskMonitorResponseOutputType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                output_type_0 = TaskMonitorResponseOutputType0.from_dict(data)

                return output_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TaskMonitorResponseOutputType0 | Unset, data)

        output = _parse_output(d.pop("output", UNSET))

        def _parse_task_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        task_type = _parse_task_type(d.pop("task_type", UNSET))

        task_monitor_response = cls(
            id=id,
            input_=input_,
            status=status,
            output=output,
            task_type=task_type,
        )

        task_monitor_response.additional_properties = d
        return task_monitor_response

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

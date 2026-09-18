from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.task_input_type_data_type_0 import TaskInputTypeDataType0
    from ..models.task_input_type_data_type_2_item_type_0 import (
        TaskInputTypeDataType2ItemType0,
    )


T = TypeVar("T", bound="TaskInputType")


@_attrs_define
class TaskInputType:
    """
    Attributes:
        name (str):
        description (str):
        data (list[str | TaskInputTypeDataType2ItemType0] | str | TaskInputTypeDataType0):
        task_type (str):
        goal (str | Unset):
        value_props (str | Unset):
        cta (str | Unset):
        channel (str | Unset):
        tone (str | Unset):
        word_limit (int | Unset):
        sender_name (str | Unset):
        senders_org_name (str | Unset):
    """

    name: str
    description: str
    data: list[str | TaskInputTypeDataType2ItemType0] | str | TaskInputTypeDataType0
    task_type: str
    goal: str | Unset = UNSET
    value_props: str | Unset = UNSET
    cta: str | Unset = UNSET
    channel: str | Unset = UNSET
    tone: str | Unset = UNSET
    word_limit: int | Unset = UNSET
    sender_name: str | Unset = UNSET
    senders_org_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.task_input_type_data_type_0 import TaskInputTypeDataType0  # noqa: PLC0415
        from ..models.task_input_type_data_type_2_item_type_0 import (
            TaskInputTypeDataType2ItemType0,
        )  # noqa: PLC0415

        name = self.name

        description = self.description

        data: dict[str, Any] | list[dict[str, Any] | str] | str
        if isinstance(self.data, TaskInputTypeDataType0):
            data = self.data.to_dict()
        elif isinstance(self.data, list):
            data = []
            for data_type_2_item_data in self.data:
                data_type_2_item: dict[str, Any] | str
                if isinstance(data_type_2_item_data, TaskInputTypeDataType2ItemType0):
                    data_type_2_item = data_type_2_item_data.to_dict()
                else:
                    data_type_2_item = data_type_2_item_data
                data.append(data_type_2_item)

        else:
            data = self.data

        task_type = self.task_type

        goal = self.goal

        value_props = self.value_props

        cta = self.cta

        channel = self.channel

        tone = self.tone

        word_limit = self.word_limit

        sender_name = self.sender_name

        senders_org_name = self.senders_org_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "data": data,
                "task_type": task_type,
            }
        )
        if goal is not UNSET:
            field_dict["goal"] = goal
        if value_props is not UNSET:
            field_dict["value_props"] = value_props
        if cta is not UNSET:
            field_dict["cta"] = cta
        if channel is not UNSET:
            field_dict["channel"] = channel
        if tone is not UNSET:
            field_dict["tone"] = tone
        if word_limit is not UNSET:
            field_dict["word_limit"] = word_limit
        if sender_name is not UNSET:
            field_dict["sender_name"] = sender_name
        if senders_org_name is not UNSET:
            field_dict["senders_org_name"] = senders_org_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.task_input_type_data_type_0 import TaskInputTypeDataType0  # noqa: PLC0415
        from ..models.task_input_type_data_type_2_item_type_0 import (
            TaskInputTypeDataType2ItemType0,
        )  # noqa: PLC0415

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        def _parse_data(
            data: object,
        ) -> list[str | TaskInputTypeDataType2ItemType0] | str | TaskInputTypeDataType0:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                data_type_0 = TaskInputTypeDataType0.from_dict(data)

                return data_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            try:
                if not isinstance(data, list):
                    raise TypeError()
                data_type_2 = []
                _data_type_2 = data
                for data_type_2_item_data in _data_type_2:

                    def _parse_data_type_2_item(
                        data: object,
                    ) -> str | TaskInputTypeDataType2ItemType0:
                        try:
                            if not isinstance(data, dict):
                                raise TypeError()
                            data_type_2_item_type_0 = (
                                TaskInputTypeDataType2ItemType0.from_dict(data)
                            )

                            return data_type_2_item_type_0
                        except (TypeError, ValueError, AttributeError, KeyError):
                            pass
                        return cast(str | TaskInputTypeDataType2ItemType0, data)

                    data_type_2_item = _parse_data_type_2_item(data_type_2_item_data)

                    data_type_2.append(data_type_2_item)

                return data_type_2
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                list[str | TaskInputTypeDataType2ItemType0]
                | str
                | TaskInputTypeDataType0,
                data,
            )

        data = _parse_data(d.pop("data"))

        task_type = d.pop("task_type")

        goal = d.pop("goal", UNSET)

        value_props = d.pop("value_props", UNSET)

        cta = d.pop("cta", UNSET)

        channel = d.pop("channel", UNSET)

        tone = d.pop("tone", UNSET)

        word_limit = d.pop("word_limit", UNSET)

        sender_name = d.pop("sender_name", UNSET)

        senders_org_name = d.pop("senders_org_name", UNSET)

        task_input_type = cls(
            name=name,
            description=description,
            data=data,
            task_type=task_type,
            goal=goal,
            value_props=value_props,
            cta=cta,
            channel=channel,
            tone=tone,
            word_limit=word_limit,
            sender_name=sender_name,
            senders_org_name=senders_org_name,
        )

        task_input_type.additional_properties = d
        return task_input_type

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

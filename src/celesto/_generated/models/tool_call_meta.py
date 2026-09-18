from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.tool_call_meta_args_type_0 import ToolCallMetaArgsType0


T = TypeVar("T", bound="ToolCallMeta")


@_attrs_define
class ToolCallMeta:
    """Metadata for a tool call in an LLM response.

    Attributes:
        name (str):
        call_id (None | str | Unset):
        args (None | ToolCallMetaArgsType0 | Unset):
    """

    name: str
    call_id: None | str | Unset = UNSET
    args: None | ToolCallMetaArgsType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.tool_call_meta_args_type_0 import ToolCallMetaArgsType0  # noqa: PLC0415

        name = self.name

        call_id: None | str | Unset
        if isinstance(self.call_id, Unset):
            call_id = UNSET
        else:
            call_id = self.call_id

        args: dict[str, Any] | None | Unset
        if isinstance(self.args, Unset):
            args = UNSET
        elif isinstance(self.args, ToolCallMetaArgsType0):
            args = self.args.to_dict()
        else:
            args = self.args

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if call_id is not UNSET:
            field_dict["call_id"] = call_id
        if args is not UNSET:
            field_dict["args"] = args

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.tool_call_meta_args_type_0 import ToolCallMetaArgsType0  # noqa: PLC0415

        d = dict(src_dict)
        name = d.pop("name")

        def _parse_call_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        call_id = _parse_call_id(d.pop("call_id", UNSET))

        def _parse_args(data: object) -> None | ToolCallMetaArgsType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                args_type_0 = ToolCallMetaArgsType0.from_dict(data)

                return args_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ToolCallMetaArgsType0 | Unset, data)

        args = _parse_args(d.pop("args", UNSET))

        tool_call_meta = cls(
            name=name,
            call_id=call_id,
            args=args,
        )

        tool_call_meta.additional_properties = d
        return tool_call_meta

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

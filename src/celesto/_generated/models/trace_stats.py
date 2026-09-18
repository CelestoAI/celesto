from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="TraceStats")


@_attrs_define
class TraceStats:
    """Aggregated statistics for a trace.

    Attributes:
        total_tokens (int | None | Unset): Total tokens used
        input_tokens (int | None | Unset):
        output_tokens (int | None | Unset):
        tool_calls_count (int | Unset):  Default: 0.
        llm_calls_count (int | Unset):  Default: 0.
        errors_count (int | Unset):  Default: 0.
    """

    total_tokens: int | None | Unset = UNSET
    input_tokens: int | None | Unset = UNSET
    output_tokens: int | None | Unset = UNSET
    tool_calls_count: int | Unset = 0
    llm_calls_count: int | Unset = 0
    errors_count: int | Unset = 0
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total_tokens: int | None | Unset
        if isinstance(self.total_tokens, Unset):
            total_tokens = UNSET
        else:
            total_tokens = self.total_tokens

        input_tokens: int | None | Unset
        if isinstance(self.input_tokens, Unset):
            input_tokens = UNSET
        else:
            input_tokens = self.input_tokens

        output_tokens: int | None | Unset
        if isinstance(self.output_tokens, Unset):
            output_tokens = UNSET
        else:
            output_tokens = self.output_tokens

        tool_calls_count = self.tool_calls_count

        llm_calls_count = self.llm_calls_count

        errors_count = self.errors_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if total_tokens is not UNSET:
            field_dict["total_tokens"] = total_tokens
        if input_tokens is not UNSET:
            field_dict["input_tokens"] = input_tokens
        if output_tokens is not UNSET:
            field_dict["output_tokens"] = output_tokens
        if tool_calls_count is not UNSET:
            field_dict["tool_calls_count"] = tool_calls_count
        if llm_calls_count is not UNSET:
            field_dict["llm_calls_count"] = llm_calls_count
        if errors_count is not UNSET:
            field_dict["errors_count"] = errors_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_total_tokens(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        total_tokens = _parse_total_tokens(d.pop("total_tokens", UNSET))

        def _parse_input_tokens(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        input_tokens = _parse_input_tokens(d.pop("input_tokens", UNSET))

        def _parse_output_tokens(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        output_tokens = _parse_output_tokens(d.pop("output_tokens", UNSET))

        tool_calls_count = d.pop("tool_calls_count", UNSET)

        llm_calls_count = d.pop("llm_calls_count", UNSET)

        errors_count = d.pop("errors_count", UNSET)

        trace_stats = cls(
            total_tokens=total_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tool_calls_count=tool_calls_count,
            llm_calls_count=llm_calls_count,
            errors_count=errors_count,
        )

        trace_stats.additional_properties = d
        return trace_stats

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

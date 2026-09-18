from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="AgentBuilderRunResponse")


@_attrs_define
class AgentBuilderRunResponse:
    """Response containing agent run output

    Attributes:
        output (str):
        trace_id (None | str | Unset):
    """

    output: str
    trace_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        output = self.output

        trace_id: None | str | Unset
        if isinstance(self.trace_id, Unset):
            trace_id = UNSET
        else:
            trace_id = self.trace_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "output": output,
            }
        )
        if trace_id is not UNSET:
            field_dict["trace_id"] = trace_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        output = d.pop("output")

        def _parse_trace_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        trace_id = _parse_trace_id(d.pop("trace_id", UNSET))

        agent_builder_run_response = cls(
            output=output,
            trace_id=trace_id,
        )

        agent_builder_run_response.additional_properties = d
        return agent_builder_run_response

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

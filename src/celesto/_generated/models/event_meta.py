from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.token_usage import TokenUsage
    from ..models.tool_call_meta import ToolCallMeta


T = TypeVar("T", bound="EventMeta")


@_attrs_define
class EventMeta:
    """Typed metadata for trace events.

    Fields vary based on event kind:
    - agent: tools, handoffs
    - llm: model, tokens, tool_calls, tool_defs, response_id, input_preview, output_preview
    - tool: input, output, call_id
    - handoff: from_agent, to_agent

        Attributes:
            model (None | str | Unset):
            tokens (None | TokenUsage | Unset):
            tool_calls (list[ToolCallMeta] | None | Unset):
            tool_defs (list[str] | None | Unset):
            response_id (None | str | Unset):
            input_preview (None | str | Unset):
            output_preview (None | str | Unset):
            input_ (Any | None | Unset):
            output (Any | None | Unset):
            call_id (None | str | Unset):
            tools (list[str] | None | Unset):
            handoffs (list[str] | None | Unset):
            from_agent (None | str | Unset):
            to_agent (None | str | Unset):
            triggered (bool | None | Unset):
    """

    model: None | str | Unset = UNSET
    tokens: None | TokenUsage | Unset = UNSET
    tool_calls: list[ToolCallMeta] | None | Unset = UNSET
    tool_defs: list[str] | None | Unset = UNSET
    response_id: None | str | Unset = UNSET
    input_preview: None | str | Unset = UNSET
    output_preview: None | str | Unset = UNSET
    input_: Any | None | Unset = UNSET
    output: Any | None | Unset = UNSET
    call_id: None | str | Unset = UNSET
    tools: list[str] | None | Unset = UNSET
    handoffs: list[str] | None | Unset = UNSET
    from_agent: None | str | Unset = UNSET
    to_agent: None | str | Unset = UNSET
    triggered: bool | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.token_usage import TokenUsage  # noqa: PLC0415
        from ..models.tool_call_meta import ToolCallMeta  # noqa: PLC0415

        model: None | str | Unset
        if isinstance(self.model, Unset):
            model = UNSET
        else:
            model = self.model

        tokens: dict[str, Any] | None | Unset
        if isinstance(self.tokens, Unset):
            tokens = UNSET
        elif isinstance(self.tokens, TokenUsage):
            tokens = self.tokens.to_dict()
        else:
            tokens = self.tokens

        tool_calls: list[dict[str, Any]] | None | Unset
        if isinstance(self.tool_calls, Unset):
            tool_calls = UNSET
        elif isinstance(self.tool_calls, list):
            tool_calls = []
            for tool_calls_type_0_item_data in self.tool_calls:
                tool_calls_type_0_item = tool_calls_type_0_item_data.to_dict()
                tool_calls.append(tool_calls_type_0_item)

        else:
            tool_calls = self.tool_calls

        tool_defs: list[str] | None | Unset
        if isinstance(self.tool_defs, Unset):
            tool_defs = UNSET
        elif isinstance(self.tool_defs, list):
            tool_defs = self.tool_defs

        else:
            tool_defs = self.tool_defs

        response_id: None | str | Unset
        if isinstance(self.response_id, Unset):
            response_id = UNSET
        else:
            response_id = self.response_id

        input_preview: None | str | Unset
        if isinstance(self.input_preview, Unset):
            input_preview = UNSET
        else:
            input_preview = self.input_preview

        output_preview: None | str | Unset
        if isinstance(self.output_preview, Unset):
            output_preview = UNSET
        else:
            output_preview = self.output_preview

        input_: Any | None | Unset
        if isinstance(self.input_, Unset):
            input_ = UNSET
        else:
            input_ = self.input_

        output: Any | None | Unset
        if isinstance(self.output, Unset):
            output = UNSET
        else:
            output = self.output

        call_id: None | str | Unset
        if isinstance(self.call_id, Unset):
            call_id = UNSET
        else:
            call_id = self.call_id

        tools: list[str] | None | Unset
        if isinstance(self.tools, Unset):
            tools = UNSET
        elif isinstance(self.tools, list):
            tools = self.tools

        else:
            tools = self.tools

        handoffs: list[str] | None | Unset
        if isinstance(self.handoffs, Unset):
            handoffs = UNSET
        elif isinstance(self.handoffs, list):
            handoffs = self.handoffs

        else:
            handoffs = self.handoffs

        from_agent: None | str | Unset
        if isinstance(self.from_agent, Unset):
            from_agent = UNSET
        else:
            from_agent = self.from_agent

        to_agent: None | str | Unset
        if isinstance(self.to_agent, Unset):
            to_agent = UNSET
        else:
            to_agent = self.to_agent

        triggered: bool | None | Unset
        if isinstance(self.triggered, Unset):
            triggered = UNSET
        else:
            triggered = self.triggered

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if model is not UNSET:
            field_dict["model"] = model
        if tokens is not UNSET:
            field_dict["tokens"] = tokens
        if tool_calls is not UNSET:
            field_dict["tool_calls"] = tool_calls
        if tool_defs is not UNSET:
            field_dict["tool_defs"] = tool_defs
        if response_id is not UNSET:
            field_dict["response_id"] = response_id
        if input_preview is not UNSET:
            field_dict["input_preview"] = input_preview
        if output_preview is not UNSET:
            field_dict["output_preview"] = output_preview
        if input_ is not UNSET:
            field_dict["input"] = input_
        if output is not UNSET:
            field_dict["output"] = output
        if call_id is not UNSET:
            field_dict["call_id"] = call_id
        if tools is not UNSET:
            field_dict["tools"] = tools
        if handoffs is not UNSET:
            field_dict["handoffs"] = handoffs
        if from_agent is not UNSET:
            field_dict["from_agent"] = from_agent
        if to_agent is not UNSET:
            field_dict["to_agent"] = to_agent
        if triggered is not UNSET:
            field_dict["triggered"] = triggered

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.token_usage import TokenUsage  # noqa: PLC0415
        from ..models.tool_call_meta import ToolCallMeta  # noqa: PLC0415

        d = dict(src_dict)

        def _parse_model(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        model = _parse_model(d.pop("model", UNSET))

        def _parse_tokens(data: object) -> None | TokenUsage | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                tokens_type_0 = TokenUsage.from_dict(data)

                return tokens_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TokenUsage | Unset, data)

        tokens = _parse_tokens(d.pop("tokens", UNSET))

        def _parse_tool_calls(data: object) -> list[ToolCallMeta] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tool_calls_type_0 = []
                _tool_calls_type_0 = data
                for tool_calls_type_0_item_data in _tool_calls_type_0:
                    tool_calls_type_0_item = ToolCallMeta.from_dict(
                        tool_calls_type_0_item_data
                    )

                    tool_calls_type_0.append(tool_calls_type_0_item)

                return tool_calls_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[ToolCallMeta] | None | Unset, data)

        tool_calls = _parse_tool_calls(d.pop("tool_calls", UNSET))

        def _parse_tool_defs(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tool_defs_type_0 = cast(list[str], data)

                return tool_defs_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        tool_defs = _parse_tool_defs(d.pop("tool_defs", UNSET))

        def _parse_response_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        response_id = _parse_response_id(d.pop("response_id", UNSET))

        def _parse_input_preview(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        input_preview = _parse_input_preview(d.pop("input_preview", UNSET))

        def _parse_output_preview(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        output_preview = _parse_output_preview(d.pop("output_preview", UNSET))

        def _parse_input_(data: object) -> Any | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Any | None | Unset, data)

        input_ = _parse_input_(d.pop("input", UNSET))

        def _parse_output(data: object) -> Any | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Any | None | Unset, data)

        output = _parse_output(d.pop("output", UNSET))

        def _parse_call_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        call_id = _parse_call_id(d.pop("call_id", UNSET))

        def _parse_tools(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tools_type_0 = cast(list[str], data)

                return tools_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        tools = _parse_tools(d.pop("tools", UNSET))

        def _parse_handoffs(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                handoffs_type_0 = cast(list[str], data)

                return handoffs_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        handoffs = _parse_handoffs(d.pop("handoffs", UNSET))

        def _parse_from_agent(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        from_agent = _parse_from_agent(d.pop("from_agent", UNSET))

        def _parse_to_agent(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        to_agent = _parse_to_agent(d.pop("to_agent", UNSET))

        def _parse_triggered(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        triggered = _parse_triggered(d.pop("triggered", UNSET))

        event_meta = cls(
            model=model,
            tokens=tokens,
            tool_calls=tool_calls,
            tool_defs=tool_defs,
            response_id=response_id,
            input_preview=input_preview,
            output_preview=output_preview,
            input_=input_,
            output=output,
            call_id=call_id,
            tools=tools,
            handoffs=handoffs,
            from_agent=from_agent,
            to_agent=to_agent,
            triggered=triggered,
        )

        event_meta.additional_properties = d
        return event_meta

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

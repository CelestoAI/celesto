from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.outbound_generation_request_channel import (
    OutboundGenerationRequestChannel,
)
from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.persona_data import PersonaData


T = TypeVar("T", bound="OutboundGenerationRequest")


@_attrs_define
class OutboundGenerationRequest:
    """Request schema for generating outbound messages.

    Example:
        {'channel': 'email', 'cta': 'Would you be open to a quick 15-min call next week?', 'goal': 'book a 15-min demo',
            'persona': {'company': 'Nimbus Data', 'name': 'Jordan Lee', 'problems': ['spread across tools', 'slow
            handoffs'], 'recent_post': 'revops tooling debt', 'role': 'VP Sales'}, 'tone': 'professional yet friendly',
            'value_props': 'AI-powered sales automation, real-time insights, seamless CRM integration'}

    Attributes:
        persona (PersonaData): Schema for persona data used in outbound generation. Example: {'company': 'Nimbus Data',
            'company_context': {'company_size': '50-200 employees', 'industry_focus': 'Data Analytics'}, 'name': 'Jordan
            Lee', 'problems': ['spread across tools', 'slow handoffs'], 'recent_post': 'revops tooling debt', 'role': 'VP
            Sales'}.
        channel (OutboundGenerationRequestChannel | Unset): Communication channel Default:
            OutboundGenerationRequestChannel.EMAIL.
        goal (None | str | Unset): Desired outcome of the message Default: 'book a quick fit call'.
        value_props (None | str | Unset): Comma-separated value propositions Default: 'omnipresent GTM copilot; live
            knowledge base from every convo; cleaner CRM'.
        cta (None | str | Unset): Call to action Default: "Reply 'yes' for a 5-min video (no forms).".
        tone (None | str | Unset): Writing style/tone Default: 'crisp, no fluff'.
        word_limit (int | None | Unset): Maximum word count (defaults: 120 for email, 420 for LinkedIn)
    """

    persona: PersonaData
    channel: OutboundGenerationRequestChannel | Unset = (
        OutboundGenerationRequestChannel.EMAIL
    )
    goal: None | str | Unset = "book a quick fit call"
    value_props: None | str | Unset = (
        "omnipresent GTM copilot; live knowledge base from every convo; cleaner CRM"
    )
    cta: None | str | Unset = "Reply 'yes' for a 5-min video (no forms)."
    tone: None | str | Unset = "crisp, no fluff"
    word_limit: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.persona_data import PersonaData  # noqa: PLC0415

        persona = self.persona.to_dict()

        channel: str | Unset = UNSET
        if not isinstance(self.channel, Unset):
            channel = self.channel.value

        goal: None | str | Unset
        if isinstance(self.goal, Unset):
            goal = UNSET
        else:
            goal = self.goal

        value_props: None | str | Unset
        if isinstance(self.value_props, Unset):
            value_props = UNSET
        else:
            value_props = self.value_props

        cta: None | str | Unset
        if isinstance(self.cta, Unset):
            cta = UNSET
        else:
            cta = self.cta

        tone: None | str | Unset
        if isinstance(self.tone, Unset):
            tone = UNSET
        else:
            tone = self.tone

        word_limit: int | None | Unset
        if isinstance(self.word_limit, Unset):
            word_limit = UNSET
        else:
            word_limit = self.word_limit

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "persona": persona,
            }
        )
        if channel is not UNSET:
            field_dict["channel"] = channel
        if goal is not UNSET:
            field_dict["goal"] = goal
        if value_props is not UNSET:
            field_dict["value_props"] = value_props
        if cta is not UNSET:
            field_dict["cta"] = cta
        if tone is not UNSET:
            field_dict["tone"] = tone
        if word_limit is not UNSET:
            field_dict["word_limit"] = word_limit

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.persona_data import PersonaData  # noqa: PLC0415

        d = dict(src_dict)
        persona = PersonaData.from_dict(d.pop("persona"))

        _channel = d.pop("channel", UNSET)
        channel: OutboundGenerationRequestChannel | Unset
        if isinstance(_channel, Unset):
            channel = UNSET
        else:
            channel = OutboundGenerationRequestChannel(_channel)

        def _parse_goal(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        goal = _parse_goal(d.pop("goal", UNSET))

        def _parse_value_props(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        value_props = _parse_value_props(d.pop("value_props", UNSET))

        def _parse_cta(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        cta = _parse_cta(d.pop("cta", UNSET))

        def _parse_tone(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tone = _parse_tone(d.pop("tone", UNSET))

        def _parse_word_limit(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        word_limit = _parse_word_limit(d.pop("word_limit", UNSET))

        outbound_generation_request = cls(
            persona=persona,
            channel=channel,
            goal=goal,
            value_props=value_props,
            cta=cta,
            tone=tone,
            word_limit=word_limit,
        )

        outbound_generation_request.additional_properties = d
        return outbound_generation_request

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

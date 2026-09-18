from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.selected_contact_request_channel_type_0 import (
    SelectedContactRequestChannelType0,
)
from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="SelectedContactRequest")


@_attrs_define
class SelectedContactRequest:
    """
    Attributes:
        contact_id (str):
        goal (None | str | Unset): Override goal for this contact
        value_props (None | str | Unset): Override value props for this contact
        cta (None | str | Unset): Override call-to-action
        channel (None | SelectedContactRequestChannelType0 | Unset): Preferred channel for this contact
        tone (None | str | Unset): Tone override
        word_limit (int | None | Unset): Word/character limit override
        sender_name (None | str | Unset): Sender name override
        senders_org_name (None | str | Unset): Sender org name override
    """

    contact_id: str
    goal: None | str | Unset = UNSET
    value_props: None | str | Unset = UNSET
    cta: None | str | Unset = UNSET
    channel: None | SelectedContactRequestChannelType0 | Unset = UNSET
    tone: None | str | Unset = UNSET
    word_limit: int | None | Unset = UNSET
    sender_name: None | str | Unset = UNSET
    senders_org_name: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        contact_id = self.contact_id

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

        channel: None | str | Unset
        if isinstance(self.channel, Unset):
            channel = UNSET
        elif isinstance(self.channel, SelectedContactRequestChannelType0):
            channel = self.channel.value
        else:
            channel = self.channel

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

        sender_name: None | str | Unset
        if isinstance(self.sender_name, Unset):
            sender_name = UNSET
        else:
            sender_name = self.sender_name

        senders_org_name: None | str | Unset
        if isinstance(self.senders_org_name, Unset):
            senders_org_name = UNSET
        else:
            senders_org_name = self.senders_org_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "contact_id": contact_id,
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
        d = dict(src_dict)
        contact_id = d.pop("contact_id")

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

        def _parse_channel(
            data: object,
        ) -> None | SelectedContactRequestChannelType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                channel_type_0 = SelectedContactRequestChannelType0(data)

                return channel_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | SelectedContactRequestChannelType0 | Unset, data)

        channel = _parse_channel(d.pop("channel", UNSET))

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

        def _parse_sender_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        sender_name = _parse_sender_name(d.pop("sender_name", UNSET))

        def _parse_senders_org_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        senders_org_name = _parse_senders_org_name(d.pop("senders_org_name", UNSET))

        selected_contact_request = cls(
            contact_id=contact_id,
            goal=goal,
            value_props=value_props,
            cta=cta,
            channel=channel,
            tone=tone,
            word_limit=word_limit,
            sender_name=sender_name,
            senders_org_name=senders_org_name,
        )

        selected_contact_request.additional_properties = d
        return selected_contact_request

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

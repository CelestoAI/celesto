from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.bulk_cold_dm_request_channel_type_0 import BulkColdDMRequestChannelType0
from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.selected_contact_request import SelectedContactRequest


T = TypeVar("T", bound="BulkColdDMRequest")


@_attrs_define
class BulkColdDMRequest:
    """
    Attributes:
        contacts (list[SelectedContactRequest]):
        goal (str): Desired outcome of the outreach
        value_props (str): Comma separated value propositions to highlight
        cta (str): Call-to-action for the message
        channel (BulkColdDMRequestChannelType0 | None | Unset): Default channel for all contacts Default:
            BulkColdDMRequestChannelType0.EMAIL.
        tone (None | str | Unset): Desired tone for the outreach
        word_limit (int | None | Unset): Word/character limit to apply
        sender_name (None | str | Unset): Default sender name
        senders_org_name (None | str | Unset): Default sender organization name
    """

    contacts: list[SelectedContactRequest]
    goal: str
    value_props: str
    cta: str
    channel: BulkColdDMRequestChannelType0 | None | Unset = (
        BulkColdDMRequestChannelType0.EMAIL
    )
    tone: None | str | Unset = UNSET
    word_limit: int | None | Unset = UNSET
    sender_name: None | str | Unset = UNSET
    senders_org_name: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.selected_contact_request import SelectedContactRequest  # noqa: PLC0415

        contacts = []
        for contacts_item_data in self.contacts:
            contacts_item = contacts_item_data.to_dict()
            contacts.append(contacts_item)

        goal = self.goal

        value_props = self.value_props

        cta = self.cta

        channel: None | str | Unset
        if isinstance(self.channel, Unset):
            channel = UNSET
        elif isinstance(self.channel, BulkColdDMRequestChannelType0):
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
                "contacts": contacts,
                "goal": goal,
                "value_props": value_props,
                "cta": cta,
            }
        )
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
        from ..models.selected_contact_request import SelectedContactRequest  # noqa: PLC0415

        d = dict(src_dict)
        contacts = []
        _contacts = d.pop("contacts")
        for contacts_item_data in _contacts:
            contacts_item = SelectedContactRequest.from_dict(contacts_item_data)

            contacts.append(contacts_item)

        goal = d.pop("goal")

        value_props = d.pop("value_props")

        cta = d.pop("cta")

        def _parse_channel(
            data: object,
        ) -> BulkColdDMRequestChannelType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                channel_type_0 = BulkColdDMRequestChannelType0(data)

                return channel_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(BulkColdDMRequestChannelType0 | None | Unset, data)

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

        bulk_cold_dm_request = cls(
            contacts=contacts,
            goal=goal,
            value_props=value_props,
            cta=cta,
            channel=channel,
            tone=tone,
            word_limit=word_limit,
            sender_name=sender_name,
            senders_org_name=senders_org_name,
        )

        bulk_cold_dm_request.additional_properties = d
        return bulk_cold_dm_request

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.outbound_generation_response_channel import (
    OutboundGenerationResponseChannel,
)


T = TypeVar("T", bound="OutboundGenerationResponse")


@_attrs_define
class OutboundGenerationResponse:
    """Response schema for generated outbound messages.

    Example:
        {'channel': 'email', 'compliance_notes': 'Personalized based on recent LinkedIn post about revops challenges.
            CTA is low-commitment video offer.', 'message': "Hi Jordan, Saw your post about revops tooling debt. We help VPs
            like you consolidate scattered tools into one GTM copilot that captures every conversation and keeps your CRM
            clean. Reply 'yes' for a 5-min video (no forms).", 'subject': 'RevOps tooling debt at Nimbus?', 'word_count':
            42}

    Attributes:
        subject (str): Email subject line or LinkedIn DM hook
        message (str): The generated message body
        compliance_notes (str): Compliance and personalization notes
        channel (OutboundGenerationResponseChannel): Communication channel used
        word_count (int): Actual word count of the message
    """

    subject: str
    message: str
    compliance_notes: str
    channel: OutboundGenerationResponseChannel
    word_count: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        subject = self.subject

        message = self.message

        compliance_notes = self.compliance_notes

        channel = self.channel.value

        word_count = self.word_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "subject": subject,
                "message": message,
                "compliance_notes": compliance_notes,
                "channel": channel,
                "word_count": word_count,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        subject = d.pop("subject")

        message = d.pop("message")

        compliance_notes = d.pop("compliance_notes")

        channel = OutboundGenerationResponseChannel(d.pop("channel"))

        word_count = d.pop("word_count")

        outbound_generation_response = cls(
            subject=subject,
            message=message,
            compliance_notes=compliance_notes,
            channel=channel,
            word_count=word_count,
        )

        outbound_generation_response.additional_properties = d
        return outbound_generation_response

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

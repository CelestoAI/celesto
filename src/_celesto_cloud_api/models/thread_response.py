from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.thread_status import ThreadStatus
from ..types import UNSET, Unset
from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.thread_response_metadata_type_0 import ThreadResponseMetadataType0


T = TypeVar("T", bound="ThreadResponse")


@_attrs_define
class ThreadResponse:
    """
    Attributes:
        id (str):
        organization_id (str):
        project_id (str):
        status (ThreadStatus): Lifecycle status of a conversation thread.
        message_count (int):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        agent_id (None | str | Unset):
        subject (None | str | Unset):
        title (None | str | Unset):
        metadata (None | ThreadResponseMetadataType0 | Unset):
        last_message_at (datetime.datetime | None | Unset):
    """

    id: str
    organization_id: str
    project_id: str
    status: ThreadStatus
    message_count: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    agent_id: None | str | Unset = UNSET
    subject: None | str | Unset = UNSET
    title: None | str | Unset = UNSET
    metadata: None | ThreadResponseMetadataType0 | Unset = UNSET
    last_message_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.thread_response_metadata_type_0 import ThreadResponseMetadataType0  # noqa: PLC0415

        id = self.id

        organization_id = self.organization_id

        project_id = self.project_id

        status = self.status.value

        message_count = self.message_count

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        agent_id: None | str | Unset
        if isinstance(self.agent_id, Unset):
            agent_id = UNSET
        else:
            agent_id = self.agent_id

        subject: None | str | Unset
        if isinstance(self.subject, Unset):
            subject = UNSET
        else:
            subject = self.subject

        title: None | str | Unset
        if isinstance(self.title, Unset):
            title = UNSET
        else:
            title = self.title

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, ThreadResponseMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        last_message_at: None | str | Unset
        if isinstance(self.last_message_at, Unset):
            last_message_at = UNSET
        elif isinstance(self.last_message_at, datetime.datetime):
            last_message_at = self.last_message_at.isoformat()
        else:
            last_message_at = self.last_message_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "organization_id": organization_id,
                "project_id": project_id,
                "status": status,
                "message_count": message_count,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if agent_id is not UNSET:
            field_dict["agent_id"] = agent_id
        if subject is not UNSET:
            field_dict["subject"] = subject
        if title is not UNSET:
            field_dict["title"] = title
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if last_message_at is not UNSET:
            field_dict["last_message_at"] = last_message_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.thread_response_metadata_type_0 import ThreadResponseMetadataType0  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        organization_id = d.pop("organization_id")

        project_id = d.pop("project_id")

        status = ThreadStatus(d.pop("status"))

        message_count = d.pop("message_count")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        def _parse_agent_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        agent_id = _parse_agent_id(d.pop("agent_id", UNSET))

        def _parse_subject(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        subject = _parse_subject(d.pop("subject", UNSET))

        def _parse_title(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        title = _parse_title(d.pop("title", UNSET))

        def _parse_metadata(data: object) -> None | ThreadResponseMetadataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = ThreadResponseMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ThreadResponseMetadataType0 | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        def _parse_last_message_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_message_at_type_0 = datetime.datetime.fromisoformat(data)

                return last_message_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        last_message_at = _parse_last_message_at(d.pop("last_message_at", UNSET))

        thread_response = cls(
            id=id,
            organization_id=organization_id,
            project_id=project_id,
            status=status,
            message_count=message_count,
            created_at=created_at,
            updated_at=updated_at,
            agent_id=agent_id,
            subject=subject,
            title=title,
            metadata=metadata,
            last_message_at=last_message_at,
        )

        thread_response.additional_properties = d
        return thread_response

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

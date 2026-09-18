from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.thread_create_request_metadata_type_0 import (
        ThreadCreateRequestMetadataType0,
    )


T = TypeVar("T", bound="ThreadCreateRequest")


@_attrs_define
class ThreadCreateRequest:
    """Create a conversation thread.

    Supply `project_id`, or `organization_id` to use that organization's
    default project.

        Attributes:
            project_id (None | str | Unset): Project to create the thread in
            organization_id (None | str | Unset): Organization; resolves to its default project
            agent_id (None | str | Unset): Agent this thread talks to
            subject (None | str | Unset): End-user identifier in the caller's own namespace, e.g. 'customer:acme:u_9'
            title (None | str | Unset):
            metadata (None | ThreadCreateRequestMetadataType0 | Unset): Caller-defined data stored verbatim
    """

    project_id: None | str | Unset = UNSET
    organization_id: None | str | Unset = UNSET
    agent_id: None | str | Unset = UNSET
    subject: None | str | Unset = UNSET
    title: None | str | Unset = UNSET
    metadata: None | ThreadCreateRequestMetadataType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.thread_create_request_metadata_type_0 import (
            ThreadCreateRequestMetadataType0,
        )  # noqa: PLC0415

        project_id: None | str | Unset
        if isinstance(self.project_id, Unset):
            project_id = UNSET
        else:
            project_id = self.project_id

        organization_id: None | str | Unset
        if isinstance(self.organization_id, Unset):
            organization_id = UNSET
        else:
            organization_id = self.organization_id

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
        elif isinstance(self.metadata, ThreadCreateRequestMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if organization_id is not UNSET:
            field_dict["organization_id"] = organization_id
        if agent_id is not UNSET:
            field_dict["agent_id"] = agent_id
        if subject is not UNSET:
            field_dict["subject"] = subject
        if title is not UNSET:
            field_dict["title"] = title
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.thread_create_request_metadata_type_0 import (
            ThreadCreateRequestMetadataType0,
        )  # noqa: PLC0415

        d = dict(src_dict)

        def _parse_project_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        project_id = _parse_project_id(d.pop("project_id", UNSET))

        def _parse_organization_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        organization_id = _parse_organization_id(d.pop("organization_id", UNSET))

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

        def _parse_metadata(
            data: object,
        ) -> None | ThreadCreateRequestMetadataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = ThreadCreateRequestMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ThreadCreateRequestMetadataType0 | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        thread_create_request = cls(
            project_id=project_id,
            organization_id=organization_id,
            agent_id=agent_id,
            subject=subject,
            title=title,
            metadata=metadata,
        )

        thread_create_request.additional_properties = d
        return thread_create_request

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

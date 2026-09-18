from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.thread_status import ThreadStatus
from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.thread_update_request_metadata_type_0 import (
        ThreadUpdateRequestMetadataType0,
    )


T = TypeVar("T", bound="ThreadUpdateRequest")


@_attrs_define
class ThreadUpdateRequest:
    """Patch a thread. Omitted fields are left unchanged.

    Attributes:
        agent_id (None | str | Unset):
        title (None | str | Unset):
        status (None | ThreadStatus | Unset):
        metadata (None | ThreadUpdateRequestMetadataType0 | Unset):
    """

    agent_id: None | str | Unset = UNSET
    title: None | str | Unset = UNSET
    status: None | ThreadStatus | Unset = UNSET
    metadata: None | ThreadUpdateRequestMetadataType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.thread_update_request_metadata_type_0 import (
            ThreadUpdateRequestMetadataType0,
        )  # noqa: PLC0415

        agent_id: None | str | Unset
        if isinstance(self.agent_id, Unset):
            agent_id = UNSET
        else:
            agent_id = self.agent_id

        title: None | str | Unset
        if isinstance(self.title, Unset):
            title = UNSET
        else:
            title = self.title

        status: None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        elif isinstance(self.status, ThreadStatus):
            status = self.status.value
        else:
            status = self.status

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, ThreadUpdateRequestMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if agent_id is not UNSET:
            field_dict["agent_id"] = agent_id
        if title is not UNSET:
            field_dict["title"] = title
        if status is not UNSET:
            field_dict["status"] = status
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.thread_update_request_metadata_type_0 import (
            ThreadUpdateRequestMetadataType0,
        )  # noqa: PLC0415

        d = dict(src_dict)

        def _parse_agent_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        agent_id = _parse_agent_id(d.pop("agent_id", UNSET))

        def _parse_title(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        title = _parse_title(d.pop("title", UNSET))

        def _parse_status(data: object) -> None | ThreadStatus | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                status_type_0 = ThreadStatus(data)

                return status_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ThreadStatus | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_metadata(
            data: object,
        ) -> None | ThreadUpdateRequestMetadataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = ThreadUpdateRequestMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ThreadUpdateRequestMetadataType0 | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        thread_update_request = cls(
            agent_id=agent_id,
            title=title,
            status=status,
            metadata=metadata,
        )

        thread_update_request.additional_properties = d
        return thread_update_request

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

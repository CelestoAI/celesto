from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.document_status import DocumentStatus
from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.document_update_document_metadata_type_0 import (
        DocumentUpdateDocumentMetadataType0,
    )


T = TypeVar("T", bound="DocumentUpdate")


@_attrs_define
class DocumentUpdate:
    """Schema for updating an existing document

    Attributes:
        title (None | str | Unset):
        description (None | str | Unset):
        document_type (None | str | Unset):
        tags (list[str] | None | Unset):
        document_metadata (DocumentUpdateDocumentMetadataType0 | None | Unset):
        project_id (None | str | Unset):
        status (DocumentStatus | None | Unset):
    """

    title: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    document_type: None | str | Unset = UNSET
    tags: list[str] | None | Unset = UNSET
    document_metadata: DocumentUpdateDocumentMetadataType0 | None | Unset = UNSET
    project_id: None | str | Unset = UNSET
    status: DocumentStatus | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.document_update_document_metadata_type_0 import (
            DocumentUpdateDocumentMetadataType0,
        )  # noqa: PLC0415

        title: None | str | Unset
        if isinstance(self.title, Unset):
            title = UNSET
        else:
            title = self.title

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        document_type: None | str | Unset
        if isinstance(self.document_type, Unset):
            document_type = UNSET
        else:
            document_type = self.document_type

        tags: list[str] | None | Unset
        if isinstance(self.tags, Unset):
            tags = UNSET
        elif isinstance(self.tags, list):
            tags = self.tags

        else:
            tags = self.tags

        document_metadata: dict[str, Any] | None | Unset
        if isinstance(self.document_metadata, Unset):
            document_metadata = UNSET
        elif isinstance(self.document_metadata, DocumentUpdateDocumentMetadataType0):
            document_metadata = self.document_metadata.to_dict()
        else:
            document_metadata = self.document_metadata

        project_id: None | str | Unset
        if isinstance(self.project_id, Unset):
            project_id = UNSET
        else:
            project_id = self.project_id

        status: None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        elif isinstance(self.status, DocumentStatus):
            status = self.status.value
        else:
            status = self.status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if title is not UNSET:
            field_dict["title"] = title
        if description is not UNSET:
            field_dict["description"] = description
        if document_type is not UNSET:
            field_dict["document_type"] = document_type
        if tags is not UNSET:
            field_dict["tags"] = tags
        if document_metadata is not UNSET:
            field_dict["document_metadata"] = document_metadata
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.document_update_document_metadata_type_0 import (
            DocumentUpdateDocumentMetadataType0,
        )  # noqa: PLC0415

        d = dict(src_dict)

        def _parse_title(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        title = _parse_title(d.pop("title", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_document_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        document_type = _parse_document_type(d.pop("document_type", UNSET))

        def _parse_tags(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                tags_type_0 = cast(list[str], data)

                return tags_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        tags = _parse_tags(d.pop("tags", UNSET))

        def _parse_document_metadata(
            data: object,
        ) -> DocumentUpdateDocumentMetadataType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                document_metadata_type_0 = (
                    DocumentUpdateDocumentMetadataType0.from_dict(data)
                )

                return document_metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(DocumentUpdateDocumentMetadataType0 | None | Unset, data)

        document_metadata = _parse_document_metadata(d.pop("document_metadata", UNSET))

        def _parse_project_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        project_id = _parse_project_id(d.pop("project_id", UNSET))

        def _parse_status(data: object) -> DocumentStatus | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                status_type_0 = DocumentStatus(data)

                return status_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(DocumentStatus | None | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        document_update = cls(
            title=title,
            description=description,
            document_type=document_type,
            tags=tags,
            document_metadata=document_metadata,
            project_id=project_id,
            status=status,
        )

        document_update.additional_properties = d
        return document_update

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

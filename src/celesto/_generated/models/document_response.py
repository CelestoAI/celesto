from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.document_status import DocumentStatus
from ..types import UNSET, Unset
from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.document_response_document_metadata import (
        DocumentResponseDocumentMetadata,
    )


T = TypeVar("T", bound="DocumentResponse")


@_attrs_define
class DocumentResponse:
    """Response schema for document operations

    Attributes:
        title (str):
        document_type (str):
        id (str):
        organization_id (str):
        filename (str):
        original_filename (str):
        file_size (int):
        content_type (str):
        created_by (str):
        updated_by (str):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        description (None | str | Unset):
        tags (list[str] | Unset):
        document_metadata (DocumentResponseDocumentMetadata | Unset):
        project_id (None | str | Unset):
        status (DocumentStatus | None | Unset):
        download_url (None | str | Unset):
    """

    title: str
    document_type: str
    id: str
    organization_id: str
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    created_by: str
    updated_by: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    description: None | str | Unset = UNSET
    tags: list[str] | Unset = UNSET
    document_metadata: DocumentResponseDocumentMetadata | Unset = UNSET
    project_id: None | str | Unset = UNSET
    status: DocumentStatus | None | Unset = UNSET
    download_url: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.document_response_document_metadata import (
            DocumentResponseDocumentMetadata,
        )  # noqa: PLC0415

        title = self.title

        document_type = self.document_type

        id = self.id

        organization_id = self.organization_id

        filename = self.filename

        original_filename = self.original_filename

        file_size = self.file_size

        content_type = self.content_type

        created_by = self.created_by

        updated_by = self.updated_by

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        tags: list[str] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags

        document_metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.document_metadata, Unset):
            document_metadata = self.document_metadata.to_dict()

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

        download_url: None | str | Unset
        if isinstance(self.download_url, Unset):
            download_url = UNSET
        else:
            download_url = self.download_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "title": title,
                "document_type": document_type,
                "id": id,
                "organization_id": organization_id,
                "filename": filename,
                "original_filename": original_filename,
                "file_size": file_size,
                "content_type": content_type,
                "created_by": created_by,
                "updated_by": updated_by,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if tags is not UNSET:
            field_dict["tags"] = tags
        if document_metadata is not UNSET:
            field_dict["document_metadata"] = document_metadata
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if status is not UNSET:
            field_dict["status"] = status
        if download_url is not UNSET:
            field_dict["download_url"] = download_url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.document_response_document_metadata import (
            DocumentResponseDocumentMetadata,
        )  # noqa: PLC0415

        d = dict(src_dict)
        title = d.pop("title")

        document_type = d.pop("document_type")

        id = d.pop("id")

        organization_id = d.pop("organization_id")

        filename = d.pop("filename")

        original_filename = d.pop("original_filename")

        file_size = d.pop("file_size")

        content_type = d.pop("content_type")

        created_by = d.pop("created_by")

        updated_by = d.pop("updated_by")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        tags = cast(list[str], d.pop("tags", UNSET))

        _document_metadata = d.pop("document_metadata", UNSET)
        document_metadata: DocumentResponseDocumentMetadata | Unset
        if isinstance(_document_metadata, Unset):
            document_metadata = UNSET
        else:
            document_metadata = DocumentResponseDocumentMetadata.from_dict(
                _document_metadata
            )

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

        def _parse_download_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        download_url = _parse_download_url(d.pop("download_url", UNSET))

        document_response = cls(
            title=title,
            document_type=document_type,
            id=id,
            organization_id=organization_id,
            filename=filename,
            original_filename=original_filename,
            file_size=file_size,
            content_type=content_type,
            created_by=created_by,
            updated_by=updated_by,
            created_at=created_at,
            updated_at=updated_at,
            description=description,
            tags=tags,
            document_metadata=document_metadata,
            project_id=project_id,
            status=status,
            download_url=download_url,
        )

        document_response.additional_properties = d
        return document_response

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

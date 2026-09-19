from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field
import json
from .. import types

from ..types import UNSET, Unset

from ..models.document_scope import DocumentScope
from ..types import UNSET, Unset


T = TypeVar("T", bound="BodyUploadDocumentV1DocumentsPost")


@_attrs_define
class BodyUploadDocumentV1DocumentsPost:
    """
    Attributes:
        file (str):
        title (str): Document title
        document_type (str): Type of document (pdf, word, excel, etc.)
        description (str | Unset): Document description
        tags (str | Unset): Comma-separated list of tags Default: ''.
        scope (DocumentScope | Unset): Document access scope
        organization_id (str | Unset): Organization ID (required for organization scope)
        project_id (str | Unset): Project ID (required for project scope)
    """

    file: str
    title: str
    document_type: str
    description: str | Unset = UNSET
    tags: str | Unset = ""
    scope: DocumentScope | Unset = UNSET
    organization_id: str | Unset = UNSET
    project_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file = self.file

        title = self.title

        document_type = self.document_type

        description = self.description

        tags = self.tags

        scope: str | Unset = UNSET
        if not isinstance(self.scope, Unset):
            scope = self.scope.value

        organization_id = self.organization_id

        project_id = self.project_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "file": file,
                "title": title,
                "document_type": document_type,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if tags is not UNSET:
            field_dict["tags"] = tags
        if scope is not UNSET:
            field_dict["scope"] = scope
        if organization_id is not UNSET:
            field_dict["organization_id"] = organization_id
        if project_id is not UNSET:
            field_dict["project_id"] = project_id

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(("file", (None, str(self.file).encode(), "text/plain")))

        files.append(("title", (None, str(self.title).encode(), "text/plain")))

        files.append(
            ("document_type", (None, str(self.document_type).encode(), "text/plain"))
        )

        if not isinstance(self.description, Unset):
            files.append(
                ("description", (None, str(self.description).encode(), "text/plain"))
            )

        if not isinstance(self.tags, Unset):
            files.append(("tags", (None, str(self.tags).encode(), "text/plain")))

        if not isinstance(self.scope, Unset):
            files.append(
                ("scope", (None, str(self.scope.value).encode(), "text/plain"))
            )

        if not isinstance(self.organization_id, Unset):
            files.append(
                (
                    "organization_id",
                    (None, str(self.organization_id).encode(), "text/plain"),
                )
            )

        if not isinstance(self.project_id, Unset):
            files.append(
                ("project_id", (None, str(self.project_id).encode(), "text/plain"))
            )

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file = d.pop("file")

        title = d.pop("title")

        document_type = d.pop("document_type")

        description = d.pop("description", UNSET)

        tags = d.pop("tags", UNSET)

        _scope = d.pop("scope", UNSET)
        scope: DocumentScope | Unset
        if isinstance(_scope, Unset):
            scope = UNSET
        else:
            scope = DocumentScope(_scope)

        organization_id = d.pop("organization_id", UNSET)

        project_id = d.pop("project_id", UNSET)

        body_upload_document_v1_documents_post = cls(
            file=file,
            title=title,
            document_type=document_type,
            description=description,
            tags=tags,
            scope=scope,
            organization_id=organization_id,
            project_id=project_id,
        )

        body_upload_document_v1_documents_post.additional_properties = d
        return body_upload_document_v1_documents_post

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

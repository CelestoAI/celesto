from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field
import json
from .. import types

from ..types import UNSET, Unset

from ..models.document_type import DocumentType
from ..types import UNSET, Unset


T = TypeVar("T", bound="BodyUploadFileV1FilesUploadPost")


@_attrs_define
class BodyUploadFileV1FilesUploadPost:
    """
    Attributes:
        file (str):
        file_type (DocumentType | Unset):
        application_id (str | Unset): The ID of the application to associate the file with
    """

    file: str
    file_type: DocumentType | Unset = UNSET
    application_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file = self.file

        file_type: str | Unset = UNSET
        if not isinstance(self.file_type, Unset):
            file_type = self.file_type.value

        application_id = self.application_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "file": file,
            }
        )
        if file_type is not UNSET:
            field_dict["file_type"] = file_type
        if application_id is not UNSET:
            field_dict["application_id"] = application_id

        return field_dict

    def to_multipart(self) -> types.RequestFiles:
        files: types.RequestFiles = []

        files.append(("file", (None, str(self.file).encode(), "text/plain")))

        if not isinstance(self.file_type, Unset):
            files.append(
                ("file_type", (None, str(self.file_type.value).encode(), "text/plain"))
            )

        if not isinstance(self.application_id, Unset):
            files.append(
                (
                    "application_id",
                    (None, str(self.application_id).encode(), "text/plain"),
                )
            )

        for prop_name, prop in self.additional_properties.items():
            files.append((prop_name, (None, str(prop).encode(), "text/plain")))

        return files

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file = d.pop("file")

        _file_type = d.pop("file_type", UNSET)
        file_type: DocumentType | Unset
        if isinstance(_file_type, Unset):
            file_type = UNSET
        else:
            file_type = DocumentType(_file_type)

        application_id = d.pop("application_id", UNSET)

        body_upload_file_v1_files_upload_post = cls(
            file=file,
            file_type=file_type,
            application_id=application_id,
        )

        body_upload_file_v1_files_upload_post.additional_properties = d
        return body_upload_file_v1_files_upload_post

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

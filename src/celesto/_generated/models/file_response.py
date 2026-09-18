from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
import datetime


T = TypeVar("T", bound="FileResponse")


@_attrs_define
class FileResponse:
    """Response model for file operations

    Attributes:
        id (str):
        filename (str):
        original_filename (str):
        file_size (int):
        content_type (str):
        created_at (datetime.datetime):
        download_url (None | str | Unset):
        file_metadata (None | str | Unset):
    """

    id: str
    filename: str
    original_filename: str
    file_size: int
    content_type: str
    created_at: datetime.datetime
    download_url: None | str | Unset = UNSET
    file_metadata: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        filename = self.filename

        original_filename = self.original_filename

        file_size = self.file_size

        content_type = self.content_type

        created_at = self.created_at.isoformat()

        download_url: None | str | Unset
        if isinstance(self.download_url, Unset):
            download_url = UNSET
        else:
            download_url = self.download_url

        file_metadata: None | str | Unset
        if isinstance(self.file_metadata, Unset):
            file_metadata = UNSET
        else:
            file_metadata = self.file_metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "filename": filename,
                "original_filename": original_filename,
                "file_size": file_size,
                "content_type": content_type,
                "created_at": created_at,
            }
        )
        if download_url is not UNSET:
            field_dict["download_url"] = download_url
        if file_metadata is not UNSET:
            field_dict["file_metadata"] = file_metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        filename = d.pop("filename")

        original_filename = d.pop("original_filename")

        file_size = d.pop("file_size")

        content_type = d.pop("content_type")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        def _parse_download_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        download_url = _parse_download_url(d.pop("download_url", UNSET))

        def _parse_file_metadata(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        file_metadata = _parse_file_metadata(d.pop("file_metadata", UNSET))

        file_response = cls(
            id=id,
            filename=filename,
            original_filename=original_filename,
            file_size=file_size,
            content_type=content_type,
            created_at=created_at,
            download_url=download_url,
            file_metadata=file_metadata,
        )

        file_response.additional_properties = d
        return file_response

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

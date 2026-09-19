from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast

if TYPE_CHECKING:
    from ..models.file_response import FileResponse


T = TypeVar("T", bound="FileListResponse")


@_attrs_define
class FileListResponse:
    """Response model for listing files

    Attributes:
        total (int):
        files (list[FileResponse]):
    """

    total: int
    files: list[FileResponse]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.file_response import FileResponse  # noqa: PLC0415

        total = self.total

        files = []
        for files_item_data in self.files:
            files_item = files_item_data.to_dict()
            files.append(files_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total": total,
                "files": files,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.file_response import FileResponse  # noqa: PLC0415

        d = dict(src_dict)
        total = d.pop("total")

        files = []
        _files = d.pop("files")
        for files_item_data in _files:
            files_item = FileResponse.from_dict(files_item_data)

            files.append(files_item)

        file_list_response = cls(
            total=total,
            files=files,
        )

        file_list_response.additional_properties = d
        return file_list_response

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

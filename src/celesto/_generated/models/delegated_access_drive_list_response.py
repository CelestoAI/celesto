from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.delegated_drive_file import DelegatedDriveFile


T = TypeVar("T", bound="DelegatedAccessDriveListResponse")


@_attrs_define
class DelegatedAccessDriveListResponse:
    """Response for listing Google Drive files for a delegated subject.

    Attributes:
        files (list[DelegatedDriveFile]):
        next_page_token (None | str | Unset):
    """

    files: list[DelegatedDriveFile]
    next_page_token: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.delegated_drive_file import DelegatedDriveFile  # noqa: PLC0415

        files = []
        for files_item_data in self.files:
            files_item = files_item_data.to_dict()
            files.append(files_item)

        next_page_token: None | str | Unset
        if isinstance(self.next_page_token, Unset):
            next_page_token = UNSET
        else:
            next_page_token = self.next_page_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "files": files,
            }
        )
        if next_page_token is not UNSET:
            field_dict["next_page_token"] = next_page_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.delegated_drive_file import DelegatedDriveFile  # noqa: PLC0415

        d = dict(src_dict)
        files = []
        _files = d.pop("files")
        for files_item_data in _files:
            files_item = DelegatedDriveFile.from_dict(files_item_data)

            files.append(files_item)

        def _parse_next_page_token(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        next_page_token = _parse_next_page_token(d.pop("next_page_token", UNSET))

        delegated_access_drive_list_response = cls(
            files=files,
            next_page_token=next_page_token,
        )

        delegated_access_drive_list_response.additional_properties = d
        return delegated_access_drive_list_response

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

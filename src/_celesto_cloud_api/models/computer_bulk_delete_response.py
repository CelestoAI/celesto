from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="ComputerBulkDeleteResponse")


@_attrs_define
class ComputerBulkDeleteResponse:
    """Response after deleting multiple computers.

    Attributes:
        deleted (int): Number of computers deleted
        deleted_ids (list[str] | Unset): IDs of computers that were deleted
        failed_ids (list[str] | Unset): IDs that could not be deleted (not found / not owned / already deleted)
    """

    deleted: int
    deleted_ids: list[str] | Unset = UNSET
    failed_ids: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        deleted = self.deleted

        deleted_ids: list[str] | Unset = UNSET
        if not isinstance(self.deleted_ids, Unset):
            deleted_ids = self.deleted_ids

        failed_ids: list[str] | Unset = UNSET
        if not isinstance(self.failed_ids, Unset):
            failed_ids = self.failed_ids

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "deleted": deleted,
            }
        )
        if deleted_ids is not UNSET:
            field_dict["deleted_ids"] = deleted_ids
        if failed_ids is not UNSET:
            field_dict["failed_ids"] = failed_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        deleted = d.pop("deleted")

        deleted_ids = cast(list[str], d.pop("deleted_ids", UNSET))

        failed_ids = cast(list[str], d.pop("failed_ids", UNSET))

        computer_bulk_delete_response = cls(
            deleted=deleted,
            deleted_ids=deleted_ids,
            failed_ids=failed_ids,
        )

        computer_bulk_delete_response.additional_properties = d
        return computer_bulk_delete_response

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

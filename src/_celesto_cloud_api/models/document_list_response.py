from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast

if TYPE_CHECKING:
    from ..models.document_response import DocumentResponse


T = TypeVar("T", bound="DocumentListResponse")


@_attrs_define
class DocumentListResponse:
    """Response schema for listing documents

    Attributes:
        total (int):
        documents (list[DocumentResponse]):
    """

    total: int
    documents: list[DocumentResponse]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.document_response import DocumentResponse  # noqa: PLC0415

        total = self.total

        documents = []
        for documents_item_data in self.documents:
            documents_item = documents_item_data.to_dict()
            documents.append(documents_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total": total,
                "documents": documents,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.document_response import DocumentResponse  # noqa: PLC0415

        d = dict(src_dict)
        total = d.pop("total")

        documents = []
        _documents = d.pop("documents")
        for documents_item_data in _documents:
            documents_item = DocumentResponse.from_dict(documents_item_data)

            documents.append(documents_item)

        document_list_response = cls(
            total=total,
            documents=documents,
        )

        document_list_response.additional_properties = d
        return document_list_response

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

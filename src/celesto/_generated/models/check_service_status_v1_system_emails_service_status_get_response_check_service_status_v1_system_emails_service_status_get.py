from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset


T = TypeVar(
    "T",
    bound="CheckServiceStatusV1SystemEmailsServiceStatusGetResponseCheckServiceStatusV1SystemEmailsServiceStatusGet",
)


@_attrs_define
class CheckServiceStatusV1SystemEmailsServiceStatusGetResponseCheckServiceStatusV1SystemEmailsServiceStatusGet:
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        check_service_status_v1_system_emails_service_status_get_response_check_service_status_v1_system_emails_service_status_get = cls()

        check_service_status_v1_system_emails_service_status_get_response_check_service_status_v1_system_emails_service_status_get.additional_properties = d
        return check_service_status_v1_system_emails_service_status_get_response_check_service_status_v1_system_emails_service_status_get

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

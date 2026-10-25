from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset


T = TypeVar("T", bound="CustomTemplateLintRequest")


@_attrs_define
class CustomTemplateLintRequest:
    """A script to check against a base before anything is created.

    Attributes:
        build_script (str):
        base_template_id (str | Unset):  Default: 'coding-agent'.
    """

    build_script: str
    base_template_id: str | Unset = "coding-agent"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        build_script = self.build_script

        base_template_id = self.base_template_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "build_script": build_script,
            }
        )
        if base_template_id is not UNSET:
            field_dict["base_template_id"] = base_template_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        build_script = d.pop("build_script")

        base_template_id = d.pop("base_template_id", UNSET)

        custom_template_lint_request = cls(
            build_script=build_script,
            base_template_id=base_template_id,
        )

        custom_template_lint_request.additional_properties = d
        return custom_template_lint_request

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

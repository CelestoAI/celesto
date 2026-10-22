from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast

if TYPE_CHECKING:
    from ..models.custom_template_response import CustomTemplateResponse


T = TypeVar("T", bound="CustomTemplateListResponse")


@_attrs_define
class CustomTemplateListResponse:
    """The organization's templates, newest first.

    Attributes:
        templates (list[CustomTemplateResponse]):
        count (int):
    """

    templates: list[CustomTemplateResponse]
    count: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.custom_template_response import CustomTemplateResponse  # noqa: PLC0415

        templates = []
        for templates_item_data in self.templates:
            templates_item = templates_item_data.to_dict()
            templates.append(templates_item)

        count = self.count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "templates": templates,
                "count": count,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.custom_template_response import CustomTemplateResponse  # noqa: PLC0415

        d = dict(src_dict)
        templates = []
        _templates = d.pop("templates")
        for templates_item_data in _templates:
            templates_item = CustomTemplateResponse.from_dict(templates_item_data)

            templates.append(templates_item)

        count = d.pop("count")

        custom_template_list_response = cls(
            templates=templates,
            count=count,
        )

        custom_template_list_response.additional_properties = d
        return custom_template_list_response

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

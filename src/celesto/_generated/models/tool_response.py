from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="ToolResponse")


@_attrs_define
class ToolResponse:
    """One entry in the code registry an agent may name in `tools`.

    Attributes:
        name (str):
        description (str):
        requires_credential (bool):
        provider (None | str | Unset):
    """

    name: str
    description: str
    requires_credential: bool
    provider: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        requires_credential = self.requires_credential

        provider: None | str | Unset
        if isinstance(self.provider, Unset):
            provider = UNSET
        else:
            provider = self.provider

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "requires_credential": requires_credential,
            }
        )
        if provider is not UNSET:
            field_dict["provider"] = provider

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        requires_credential = d.pop("requires_credential")

        def _parse_provider(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        provider = _parse_provider(d.pop("provider", UNSET))

        tool_response = cls(
            name=name,
            description=description,
            requires_credential=requires_credential,
            provider=provider,
        )

        tool_response.additional_properties = d
        return tool_response

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

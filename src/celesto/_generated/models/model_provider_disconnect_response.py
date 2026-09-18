from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.model_provider import ModelProvider
from ..types import UNSET, Unset


T = TypeVar("T", bound="ModelProviderDisconnectResponse")


@_attrs_define
class ModelProviderDisconnectResponse:
    """
    Attributes:
        provider (ModelProvider): LLM providers users can connect their own credentials for.
        disconnected (bool | Unset):  Default: True.
    """

    provider: ModelProvider
    disconnected: bool | Unset = True
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        provider = self.provider.value

        disconnected = self.disconnected

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "provider": provider,
            }
        )
        if disconnected is not UNSET:
            field_dict["disconnected"] = disconnected

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        provider = ModelProvider(d.pop("provider"))

        disconnected = d.pop("disconnected", UNSET)

        model_provider_disconnect_response = cls(
            provider=provider,
            disconnected=disconnected,
        )

        model_provider_disconnect_response.additional_properties = d
        return model_provider_disconnect_response

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

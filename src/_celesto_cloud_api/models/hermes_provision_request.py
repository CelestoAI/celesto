from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.hermes_provider import HermesProvider
from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="HermesProvisionRequest")


@_attrs_define
class HermesProvisionRequest:
    """
    Attributes:
        api_key (None | str | Unset):
        provider (HermesProvider | None | Unset): LLM provider to configure during provisioning
        reuse_saved_api_key (bool | Unset): Reuse the organization-scoped OPENAI_API_KEY secret for OpenAI Default:
            False.
        model (None | str | Unset):
    """

    api_key: None | str | Unset = UNSET
    provider: HermesProvider | None | Unset = UNSET
    reuse_saved_api_key: bool | Unset = False
    model: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        api_key: None | str | Unset
        if isinstance(self.api_key, Unset):
            api_key = UNSET
        else:
            api_key = self.api_key

        provider: None | str | Unset
        if isinstance(self.provider, Unset):
            provider = UNSET
        elif isinstance(self.provider, HermesProvider):
            provider = self.provider.value
        else:
            provider = self.provider

        reuse_saved_api_key = self.reuse_saved_api_key

        model: None | str | Unset
        if isinstance(self.model, Unset):
            model = UNSET
        else:
            model = self.model

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if api_key is not UNSET:
            field_dict["api_key"] = api_key
        if provider is not UNSET:
            field_dict["provider"] = provider
        if reuse_saved_api_key is not UNSET:
            field_dict["reuse_saved_api_key"] = reuse_saved_api_key
        if model is not UNSET:
            field_dict["model"] = model

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_api_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        api_key = _parse_api_key(d.pop("api_key", UNSET))

        def _parse_provider(data: object) -> HermesProvider | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                provider_type_0 = HermesProvider(data)

                return provider_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(HermesProvider | None | Unset, data)

        provider = _parse_provider(d.pop("provider", UNSET))

        reuse_saved_api_key = d.pop("reuse_saved_api_key", UNSET)

        def _parse_model(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        model = _parse_model(d.pop("model", UNSET))

        hermes_provision_request = cls(
            api_key=api_key,
            provider=provider,
            reuse_saved_api_key=reuse_saved_api_key,
            model=model,
        )

        hermes_provision_request.additional_properties = d
        return hermes_provision_request

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

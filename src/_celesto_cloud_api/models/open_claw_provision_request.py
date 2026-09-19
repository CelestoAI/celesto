from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.open_claw_provider import OpenClawProvider
from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="OpenClawProvisionRequest")


@_attrs_define
class OpenClawProvisionRequest:
    """
    Attributes:
        telegram_bot_token (None | str | Unset):
        api_key (None | str | Unset): Deprecated: configure LLM credentials via the instance LLM endpoint
        provider (None | OpenClawProvider | Unset): Deprecated: configure provider via the instance LLM endpoint
        reuse_saved_api_key (bool | Unset): Deprecated: configure LLM credentials via the instance LLM endpoint Default:
            False.
        model (None | str | Unset): Deprecated: configure model via the instance LLM endpoint
    """

    telegram_bot_token: None | str | Unset = UNSET
    api_key: None | str | Unset = UNSET
    provider: None | OpenClawProvider | Unset = UNSET
    reuse_saved_api_key: bool | Unset = False
    model: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        telegram_bot_token: None | str | Unset
        if isinstance(self.telegram_bot_token, Unset):
            telegram_bot_token = UNSET
        else:
            telegram_bot_token = self.telegram_bot_token

        api_key: None | str | Unset
        if isinstance(self.api_key, Unset):
            api_key = UNSET
        else:
            api_key = self.api_key

        provider: None | str | Unset
        if isinstance(self.provider, Unset):
            provider = UNSET
        elif isinstance(self.provider, OpenClawProvider):
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
        if telegram_bot_token is not UNSET:
            field_dict["telegram_bot_token"] = telegram_bot_token
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

        def _parse_telegram_bot_token(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        telegram_bot_token = _parse_telegram_bot_token(
            d.pop("telegram_bot_token", UNSET)
        )

        def _parse_api_key(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        api_key = _parse_api_key(d.pop("api_key", UNSET))

        def _parse_provider(data: object) -> None | OpenClawProvider | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                provider_type_0 = OpenClawProvider(data)

                return provider_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | OpenClawProvider | Unset, data)

        provider = _parse_provider(d.pop("provider", UNSET))

        reuse_saved_api_key = d.pop("reuse_saved_api_key", UNSET)

        def _parse_model(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        model = _parse_model(d.pop("model", UNSET))

        open_claw_provision_request = cls(
            telegram_bot_token=telegram_bot_token,
            api_key=api_key,
            provider=provider,
            reuse_saved_api_key=reuse_saved_api_key,
            model=model,
        )

        open_claw_provision_request.additional_properties = d
        return open_claw_provision_request

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

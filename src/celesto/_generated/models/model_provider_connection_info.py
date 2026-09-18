from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.model_provider import ModelProvider
from ..types import UNSET, Unset
from typing import cast
import datetime


T = TypeVar("T", bound="ModelProviderConnectionInfo")


@_attrs_define
class ModelProviderConnectionInfo:
    """Status of one provider, connected or not.

    Deliberately has no field for the plaintext key — it is structurally
    impossible for this response to leak a credential.

        Attributes:
            provider (ModelProvider): LLM providers users can connect their own credentials for.
            label (str):
            connected (bool):
            default_model (str):
            models (list[str]):
            allow_any_model (bool): Provider accepts arbitrary model ids; `models` is empty and clients should render a
                free-text field
            platform_fallback (bool): Celesto's own key covers this provider when the org hasn't connected one
            oauth_available (bool): Whether 'Sign in with provider' is currently offered
            docs_url (str):
            default_max_tokens (int | None | Unset): Output cap applied when the agent sets none (providers that reserve
                credit for unbounded requests)
            auth_type (None | str | Unset):
            masked_preview (None | str | Unset):
            status (None | str | Unset):
            connected_at (datetime.datetime | None | Unset):
            last_validated_at (datetime.datetime | None | Unset):
            last_used_at (datetime.datetime | None | Unset):
    """

    provider: ModelProvider
    label: str
    connected: bool
    default_model: str
    models: list[str]
    allow_any_model: bool
    platform_fallback: bool
    oauth_available: bool
    docs_url: str
    default_max_tokens: int | None | Unset = UNSET
    auth_type: None | str | Unset = UNSET
    masked_preview: None | str | Unset = UNSET
    status: None | str | Unset = UNSET
    connected_at: datetime.datetime | None | Unset = UNSET
    last_validated_at: datetime.datetime | None | Unset = UNSET
    last_used_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        provider = self.provider.value

        label = self.label

        connected = self.connected

        default_model = self.default_model

        models = self.models

        allow_any_model = self.allow_any_model

        platform_fallback = self.platform_fallback

        oauth_available = self.oauth_available

        docs_url = self.docs_url

        default_max_tokens: int | None | Unset
        if isinstance(self.default_max_tokens, Unset):
            default_max_tokens = UNSET
        else:
            default_max_tokens = self.default_max_tokens

        auth_type: None | str | Unset
        if isinstance(self.auth_type, Unset):
            auth_type = UNSET
        else:
            auth_type = self.auth_type

        masked_preview: None | str | Unset
        if isinstance(self.masked_preview, Unset):
            masked_preview = UNSET
        else:
            masked_preview = self.masked_preview

        status: None | str | Unset
        if isinstance(self.status, Unset):
            status = UNSET
        else:
            status = self.status

        connected_at: None | str | Unset
        if isinstance(self.connected_at, Unset):
            connected_at = UNSET
        elif isinstance(self.connected_at, datetime.datetime):
            connected_at = self.connected_at.isoformat()
        else:
            connected_at = self.connected_at

        last_validated_at: None | str | Unset
        if isinstance(self.last_validated_at, Unset):
            last_validated_at = UNSET
        elif isinstance(self.last_validated_at, datetime.datetime):
            last_validated_at = self.last_validated_at.isoformat()
        else:
            last_validated_at = self.last_validated_at

        last_used_at: None | str | Unset
        if isinstance(self.last_used_at, Unset):
            last_used_at = UNSET
        elif isinstance(self.last_used_at, datetime.datetime):
            last_used_at = self.last_used_at.isoformat()
        else:
            last_used_at = self.last_used_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "provider": provider,
                "label": label,
                "connected": connected,
                "default_model": default_model,
                "models": models,
                "allow_any_model": allow_any_model,
                "platform_fallback": platform_fallback,
                "oauth_available": oauth_available,
                "docs_url": docs_url,
            }
        )
        if default_max_tokens is not UNSET:
            field_dict["default_max_tokens"] = default_max_tokens
        if auth_type is not UNSET:
            field_dict["auth_type"] = auth_type
        if masked_preview is not UNSET:
            field_dict["masked_preview"] = masked_preview
        if status is not UNSET:
            field_dict["status"] = status
        if connected_at is not UNSET:
            field_dict["connected_at"] = connected_at
        if last_validated_at is not UNSET:
            field_dict["last_validated_at"] = last_validated_at
        if last_used_at is not UNSET:
            field_dict["last_used_at"] = last_used_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        provider = ModelProvider(d.pop("provider"))

        label = d.pop("label")

        connected = d.pop("connected")

        default_model = d.pop("default_model")

        models = cast(list[str], d.pop("models"))

        allow_any_model = d.pop("allow_any_model")

        platform_fallback = d.pop("platform_fallback")

        oauth_available = d.pop("oauth_available")

        docs_url = d.pop("docs_url")

        def _parse_default_max_tokens(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        default_max_tokens = _parse_default_max_tokens(
            d.pop("default_max_tokens", UNSET)
        )

        def _parse_auth_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        auth_type = _parse_auth_type(d.pop("auth_type", UNSET))

        def _parse_masked_preview(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        masked_preview = _parse_masked_preview(d.pop("masked_preview", UNSET))

        def _parse_status(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        status = _parse_status(d.pop("status", UNSET))

        def _parse_connected_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                connected_at_type_0 = datetime.datetime.fromisoformat(data)

                return connected_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        connected_at = _parse_connected_at(d.pop("connected_at", UNSET))

        def _parse_last_validated_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_validated_at_type_0 = datetime.datetime.fromisoformat(data)

                return last_validated_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        last_validated_at = _parse_last_validated_at(d.pop("last_validated_at", UNSET))

        def _parse_last_used_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_used_at_type_0 = datetime.datetime.fromisoformat(data)

                return last_used_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        last_used_at = _parse_last_used_at(d.pop("last_used_at", UNSET))

        model_provider_connection_info = cls(
            provider=provider,
            label=label,
            connected=connected,
            default_model=default_model,
            models=models,
            allow_any_model=allow_any_model,
            platform_fallback=platform_fallback,
            oauth_available=oauth_available,
            docs_url=docs_url,
            default_max_tokens=default_max_tokens,
            auth_type=auth_type,
            masked_preview=masked_preview,
            status=status,
            connected_at=connected_at,
            last_validated_at=last_validated_at,
            last_used_at=last_used_at,
        )

        model_provider_connection_info.additional_properties = d
        return model_provider_connection_info

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

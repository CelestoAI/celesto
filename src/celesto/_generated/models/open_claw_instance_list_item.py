from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.open_claw_instance_status import OpenClawInstanceStatus
from ..models.open_claw_provider import OpenClawProvider
from ..types import UNSET, Unset
from typing import cast
import datetime


T = TypeVar("T", bound="OpenClawInstanceListItem")


@_attrs_define
class OpenClawInstanceListItem:
    """
    Attributes:
        instance_id (str):
        status (OpenClawInstanceStatus): Lifecycle status for hosted OpenClaw instances.
        provider (OpenClawProvider): Supported LLM providers for OpenClaw instances.
        model (str):
        created_at (datetime.datetime):
        telegram_bot_username (None | str | Unset):
        gateway_url (None | str | Unset):
        pairing_status (None | str | Unset):
        paired_at (datetime.datetime | None | Unset):
        runtime_status (None | str | Unset):
        llm_status (None | str | Unset):
        telegram_status (None | str | Unset):
        runtime_error (None | str | Unset):
        llm_error (None | str | Unset):
        telegram_error (None | str | Unset):
    """

    instance_id: str
    status: OpenClawInstanceStatus
    provider: OpenClawProvider
    model: str
    created_at: datetime.datetime
    telegram_bot_username: None | str | Unset = UNSET
    gateway_url: None | str | Unset = UNSET
    pairing_status: None | str | Unset = UNSET
    paired_at: datetime.datetime | None | Unset = UNSET
    runtime_status: None | str | Unset = UNSET
    llm_status: None | str | Unset = UNSET
    telegram_status: None | str | Unset = UNSET
    runtime_error: None | str | Unset = UNSET
    llm_error: None | str | Unset = UNSET
    telegram_error: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        instance_id = self.instance_id

        status = self.status.value

        provider = self.provider.value

        model = self.model

        created_at = self.created_at.isoformat()

        telegram_bot_username: None | str | Unset
        if isinstance(self.telegram_bot_username, Unset):
            telegram_bot_username = UNSET
        else:
            telegram_bot_username = self.telegram_bot_username

        gateway_url: None | str | Unset
        if isinstance(self.gateway_url, Unset):
            gateway_url = UNSET
        else:
            gateway_url = self.gateway_url

        pairing_status: None | str | Unset
        if isinstance(self.pairing_status, Unset):
            pairing_status = UNSET
        else:
            pairing_status = self.pairing_status

        paired_at: None | str | Unset
        if isinstance(self.paired_at, Unset):
            paired_at = UNSET
        elif isinstance(self.paired_at, datetime.datetime):
            paired_at = self.paired_at.isoformat()
        else:
            paired_at = self.paired_at

        runtime_status: None | str | Unset
        if isinstance(self.runtime_status, Unset):
            runtime_status = UNSET
        else:
            runtime_status = self.runtime_status

        llm_status: None | str | Unset
        if isinstance(self.llm_status, Unset):
            llm_status = UNSET
        else:
            llm_status = self.llm_status

        telegram_status: None | str | Unset
        if isinstance(self.telegram_status, Unset):
            telegram_status = UNSET
        else:
            telegram_status = self.telegram_status

        runtime_error: None | str | Unset
        if isinstance(self.runtime_error, Unset):
            runtime_error = UNSET
        else:
            runtime_error = self.runtime_error

        llm_error: None | str | Unset
        if isinstance(self.llm_error, Unset):
            llm_error = UNSET
        else:
            llm_error = self.llm_error

        telegram_error: None | str | Unset
        if isinstance(self.telegram_error, Unset):
            telegram_error = UNSET
        else:
            telegram_error = self.telegram_error

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "instance_id": instance_id,
                "status": status,
                "provider": provider,
                "model": model,
                "created_at": created_at,
            }
        )
        if telegram_bot_username is not UNSET:
            field_dict["telegram_bot_username"] = telegram_bot_username
        if gateway_url is not UNSET:
            field_dict["gateway_url"] = gateway_url
        if pairing_status is not UNSET:
            field_dict["pairing_status"] = pairing_status
        if paired_at is not UNSET:
            field_dict["paired_at"] = paired_at
        if runtime_status is not UNSET:
            field_dict["runtime_status"] = runtime_status
        if llm_status is not UNSET:
            field_dict["llm_status"] = llm_status
        if telegram_status is not UNSET:
            field_dict["telegram_status"] = telegram_status
        if runtime_error is not UNSET:
            field_dict["runtime_error"] = runtime_error
        if llm_error is not UNSET:
            field_dict["llm_error"] = llm_error
        if telegram_error is not UNSET:
            field_dict["telegram_error"] = telegram_error

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        instance_id = d.pop("instance_id")

        status = OpenClawInstanceStatus(d.pop("status"))

        provider = OpenClawProvider(d.pop("provider"))

        model = d.pop("model")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        def _parse_telegram_bot_username(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        telegram_bot_username = _parse_telegram_bot_username(
            d.pop("telegram_bot_username", UNSET)
        )

        def _parse_gateway_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        gateway_url = _parse_gateway_url(d.pop("gateway_url", UNSET))

        def _parse_pairing_status(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        pairing_status = _parse_pairing_status(d.pop("pairing_status", UNSET))

        def _parse_paired_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                paired_at_type_0 = datetime.datetime.fromisoformat(data)

                return paired_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        paired_at = _parse_paired_at(d.pop("paired_at", UNSET))

        def _parse_runtime_status(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        runtime_status = _parse_runtime_status(d.pop("runtime_status", UNSET))

        def _parse_llm_status(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        llm_status = _parse_llm_status(d.pop("llm_status", UNSET))

        def _parse_telegram_status(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        telegram_status = _parse_telegram_status(d.pop("telegram_status", UNSET))

        def _parse_runtime_error(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        runtime_error = _parse_runtime_error(d.pop("runtime_error", UNSET))

        def _parse_llm_error(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        llm_error = _parse_llm_error(d.pop("llm_error", UNSET))

        def _parse_telegram_error(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        telegram_error = _parse_telegram_error(d.pop("telegram_error", UNSET))

        open_claw_instance_list_item = cls(
            instance_id=instance_id,
            status=status,
            provider=provider,
            model=model,
            created_at=created_at,
            telegram_bot_username=telegram_bot_username,
            gateway_url=gateway_url,
            pairing_status=pairing_status,
            paired_at=paired_at,
            runtime_status=runtime_status,
            llm_status=llm_status,
            telegram_status=telegram_status,
            runtime_error=runtime_error,
            llm_error=llm_error,
            telegram_error=telegram_error,
        )

        open_claw_instance_list_item.additional_properties = d
        return open_claw_instance_list_item

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

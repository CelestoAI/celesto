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


T = TypeVar("T", bound="OpenClawProvisionResponse")


@_attrs_define
class OpenClawProvisionResponse:
    """
    Attributes:
        instance_id (str):
        status (OpenClawInstanceStatus): Lifecycle status for hosted OpenClaw instances.
        provider (OpenClawProvider): Supported LLM providers for OpenClaw instances.
        model (str):
        estimated_ready_seconds (int):
        gateway_url (None | str | Unset):
        runtime_status (None | str | Unset):
        llm_status (None | str | Unset):
        telegram_status (None | str | Unset):
    """

    instance_id: str
    status: OpenClawInstanceStatus
    provider: OpenClawProvider
    model: str
    estimated_ready_seconds: int
    gateway_url: None | str | Unset = UNSET
    runtime_status: None | str | Unset = UNSET
    llm_status: None | str | Unset = UNSET
    telegram_status: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        instance_id = self.instance_id

        status = self.status.value

        provider = self.provider.value

        model = self.model

        estimated_ready_seconds = self.estimated_ready_seconds

        gateway_url: None | str | Unset
        if isinstance(self.gateway_url, Unset):
            gateway_url = UNSET
        else:
            gateway_url = self.gateway_url

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

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "instance_id": instance_id,
                "status": status,
                "provider": provider,
                "model": model,
                "estimated_ready_seconds": estimated_ready_seconds,
            }
        )
        if gateway_url is not UNSET:
            field_dict["gateway_url"] = gateway_url
        if runtime_status is not UNSET:
            field_dict["runtime_status"] = runtime_status
        if llm_status is not UNSET:
            field_dict["llm_status"] = llm_status
        if telegram_status is not UNSET:
            field_dict["telegram_status"] = telegram_status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        instance_id = d.pop("instance_id")

        status = OpenClawInstanceStatus(d.pop("status"))

        provider = OpenClawProvider(d.pop("provider"))

        model = d.pop("model")

        estimated_ready_seconds = d.pop("estimated_ready_seconds")

        def _parse_gateway_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        gateway_url = _parse_gateway_url(d.pop("gateway_url", UNSET))

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

        open_claw_provision_response = cls(
            instance_id=instance_id,
            status=status,
            provider=provider,
            model=model,
            estimated_ready_seconds=estimated_ready_seconds,
            gateway_url=gateway_url,
            runtime_status=runtime_status,
            llm_status=llm_status,
            telegram_status=telegram_status,
        )

        open_claw_provision_response.additional_properties = d
        return open_claw_provision_response

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

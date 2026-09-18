from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.hermes_instance_status import HermesInstanceStatus
from ..models.hermes_provider import HermesProvider
from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="HermesProvisionResponse")


@_attrs_define
class HermesProvisionResponse:
    """
    Attributes:
        instance_id (str):
        status (HermesInstanceStatus): Lifecycle status for hosted Hermes instances.
        api_key (str):
        provider (HermesProvider): Supported API-key LLM providers for Hermes V1.
        model (str):
        api_url (None | str | Unset):
        dashboard_url (None | str | Unset):
        dashboard_username (None | str | Unset):
        estimated_ready_seconds (int | Unset):  Default: 90.
        runtime_status (None | str | Unset):
        llm_status (None | str | Unset):
        provisioning_step (None | str | Unset):
        retryable (bool | Unset):  Default: False.
    """

    instance_id: str
    status: HermesInstanceStatus
    api_key: str
    provider: HermesProvider
    model: str
    api_url: None | str | Unset = UNSET
    dashboard_url: None | str | Unset = UNSET
    dashboard_username: None | str | Unset = UNSET
    estimated_ready_seconds: int | Unset = 90
    runtime_status: None | str | Unset = UNSET
    llm_status: None | str | Unset = UNSET
    provisioning_step: None | str | Unset = UNSET
    retryable: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        instance_id = self.instance_id

        status = self.status.value

        api_key = self.api_key

        provider = self.provider.value

        model = self.model

        api_url: None | str | Unset
        if isinstance(self.api_url, Unset):
            api_url = UNSET
        else:
            api_url = self.api_url

        dashboard_url: None | str | Unset
        if isinstance(self.dashboard_url, Unset):
            dashboard_url = UNSET
        else:
            dashboard_url = self.dashboard_url

        dashboard_username: None | str | Unset
        if isinstance(self.dashboard_username, Unset):
            dashboard_username = UNSET
        else:
            dashboard_username = self.dashboard_username

        estimated_ready_seconds = self.estimated_ready_seconds

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

        provisioning_step: None | str | Unset
        if isinstance(self.provisioning_step, Unset):
            provisioning_step = UNSET
        else:
            provisioning_step = self.provisioning_step

        retryable = self.retryable

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "instance_id": instance_id,
                "status": status,
                "api_key": api_key,
                "provider": provider,
                "model": model,
            }
        )
        if api_url is not UNSET:
            field_dict["api_url"] = api_url
        if dashboard_url is not UNSET:
            field_dict["dashboard_url"] = dashboard_url
        if dashboard_username is not UNSET:
            field_dict["dashboard_username"] = dashboard_username
        if estimated_ready_seconds is not UNSET:
            field_dict["estimated_ready_seconds"] = estimated_ready_seconds
        if runtime_status is not UNSET:
            field_dict["runtime_status"] = runtime_status
        if llm_status is not UNSET:
            field_dict["llm_status"] = llm_status
        if provisioning_step is not UNSET:
            field_dict["provisioning_step"] = provisioning_step
        if retryable is not UNSET:
            field_dict["retryable"] = retryable

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        instance_id = d.pop("instance_id")

        status = HermesInstanceStatus(d.pop("status"))

        api_key = d.pop("api_key")

        provider = HermesProvider(d.pop("provider"))

        model = d.pop("model")

        def _parse_api_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        api_url = _parse_api_url(d.pop("api_url", UNSET))

        def _parse_dashboard_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        dashboard_url = _parse_dashboard_url(d.pop("dashboard_url", UNSET))

        def _parse_dashboard_username(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        dashboard_username = _parse_dashboard_username(
            d.pop("dashboard_username", UNSET)
        )

        estimated_ready_seconds = d.pop("estimated_ready_seconds", UNSET)

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

        def _parse_provisioning_step(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        provisioning_step = _parse_provisioning_step(d.pop("provisioning_step", UNSET))

        retryable = d.pop("retryable", UNSET)

        hermes_provision_response = cls(
            instance_id=instance_id,
            status=status,
            api_key=api_key,
            provider=provider,
            model=model,
            api_url=api_url,
            dashboard_url=dashboard_url,
            dashboard_username=dashboard_username,
            estimated_ready_seconds=estimated_ready_seconds,
            runtime_status=runtime_status,
            llm_status=llm_status,
            provisioning_step=provisioning_step,
            retryable=retryable,
        )

        hermes_provision_response.additional_properties = d
        return hermes_provision_response

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

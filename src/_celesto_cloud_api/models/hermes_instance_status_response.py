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
import datetime

if TYPE_CHECKING:
    from ..models.hermes_instance_status_response_health_type_0 import (
        HermesInstanceStatusResponseHealthType0,
    )


T = TypeVar("T", bound="HermesInstanceStatusResponse")


@_attrs_define
class HermesInstanceStatusResponse:
    """
    Attributes:
        instance_id (str):
        status (HermesInstanceStatus): Lifecycle status for hosted Hermes instances.
        provider (HermesProvider): Supported API-key LLM providers for Hermes V1.
        model (str):
        created_at (datetime.datetime):
        api_url (None | str | Unset):
        dashboard_url (None | str | Unset):
        dashboard_username (None | str | Unset):
        last_error (None | str | Unset):
        health (HermesInstanceStatusResponseHealthType0 | None | Unset):
        runtime_status (None | str | Unset):
        llm_status (None | str | Unset):
        runtime_error (None | str | Unset):
        llm_error (None | str | Unset):
        provisioning_step (None | str | Unset):
        retryable (bool | Unset):  Default: False.
    """

    instance_id: str
    status: HermesInstanceStatus
    provider: HermesProvider
    model: str
    created_at: datetime.datetime
    api_url: None | str | Unset = UNSET
    dashboard_url: None | str | Unset = UNSET
    dashboard_username: None | str | Unset = UNSET
    last_error: None | str | Unset = UNSET
    health: HermesInstanceStatusResponseHealthType0 | None | Unset = UNSET
    runtime_status: None | str | Unset = UNSET
    llm_status: None | str | Unset = UNSET
    runtime_error: None | str | Unset = UNSET
    llm_error: None | str | Unset = UNSET
    provisioning_step: None | str | Unset = UNSET
    retryable: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.hermes_instance_status_response_health_type_0 import (
            HermesInstanceStatusResponseHealthType0,
        )  # noqa: PLC0415

        instance_id = self.instance_id

        status = self.status.value

        provider = self.provider.value

        model = self.model

        created_at = self.created_at.isoformat()

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

        last_error: None | str | Unset
        if isinstance(self.last_error, Unset):
            last_error = UNSET
        else:
            last_error = self.last_error

        health: dict[str, Any] | None | Unset
        if isinstance(self.health, Unset):
            health = UNSET
        elif isinstance(self.health, HermesInstanceStatusResponseHealthType0):
            health = self.health.to_dict()
        else:
            health = self.health

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
                "provider": provider,
                "model": model,
                "created_at": created_at,
            }
        )
        if api_url is not UNSET:
            field_dict["api_url"] = api_url
        if dashboard_url is not UNSET:
            field_dict["dashboard_url"] = dashboard_url
        if dashboard_username is not UNSET:
            field_dict["dashboard_username"] = dashboard_username
        if last_error is not UNSET:
            field_dict["last_error"] = last_error
        if health is not UNSET:
            field_dict["health"] = health
        if runtime_status is not UNSET:
            field_dict["runtime_status"] = runtime_status
        if llm_status is not UNSET:
            field_dict["llm_status"] = llm_status
        if runtime_error is not UNSET:
            field_dict["runtime_error"] = runtime_error
        if llm_error is not UNSET:
            field_dict["llm_error"] = llm_error
        if provisioning_step is not UNSET:
            field_dict["provisioning_step"] = provisioning_step
        if retryable is not UNSET:
            field_dict["retryable"] = retryable

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.hermes_instance_status_response_health_type_0 import (
            HermesInstanceStatusResponseHealthType0,
        )  # noqa: PLC0415

        d = dict(src_dict)
        instance_id = d.pop("instance_id")

        status = HermesInstanceStatus(d.pop("status"))

        provider = HermesProvider(d.pop("provider"))

        model = d.pop("model")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

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

        def _parse_last_error(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        last_error = _parse_last_error(d.pop("last_error", UNSET))

        def _parse_health(
            data: object,
        ) -> HermesInstanceStatusResponseHealthType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                health_type_0 = HermesInstanceStatusResponseHealthType0.from_dict(data)

                return health_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(HermesInstanceStatusResponseHealthType0 | None | Unset, data)

        health = _parse_health(d.pop("health", UNSET))

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

        def _parse_provisioning_step(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        provisioning_step = _parse_provisioning_step(d.pop("provisioning_step", UNSET))

        retryable = d.pop("retryable", UNSET)

        hermes_instance_status_response = cls(
            instance_id=instance_id,
            status=status,
            provider=provider,
            model=model,
            created_at=created_at,
            api_url=api_url,
            dashboard_url=dashboard_url,
            dashboard_username=dashboard_username,
            last_error=last_error,
            health=health,
            runtime_status=runtime_status,
            llm_status=llm_status,
            runtime_error=runtime_error,
            llm_error=llm_error,
            provisioning_step=provisioning_step,
            retryable=retryable,
        )

        hermes_instance_status_response.additional_properties = d
        return hermes_instance_status_response

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

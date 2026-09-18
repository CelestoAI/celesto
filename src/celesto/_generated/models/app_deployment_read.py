from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.app_deployment_status import AppDeploymentStatus
from ..types import UNSET, Unset
from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.app_deployment_read_config_type_0 import AppDeploymentReadConfigType0


T = TypeVar("T", bound="AppDeploymentRead")


@_attrs_define
class AppDeploymentRead:
    """Response model representing a deployment record.

    Attributes:
        name (str):
        id (str):
        organization_id (str):
        user_id (str):
        status (AppDeploymentStatus): Lifecycle status for a deployed application.
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        description (None | str | Unset):
        last_error (None | str | Unset):
        config (AppDeploymentReadConfigType0 | None | Unset):
        deployed_at (datetime.datetime | None | Unset):
    """

    name: str
    id: str
    organization_id: str
    user_id: str
    status: AppDeploymentStatus
    created_at: datetime.datetime
    updated_at: datetime.datetime
    description: None | str | Unset = UNSET
    last_error: None | str | Unset = UNSET
    config: AppDeploymentReadConfigType0 | None | Unset = UNSET
    deployed_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.app_deployment_read_config_type_0 import (
            AppDeploymentReadConfigType0,
        )  # noqa: PLC0415

        name = self.name

        id = self.id

        organization_id = self.organization_id

        user_id = self.user_id

        status = self.status.value

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        last_error: None | str | Unset
        if isinstance(self.last_error, Unset):
            last_error = UNSET
        else:
            last_error = self.last_error

        config: dict[str, Any] | None | Unset
        if isinstance(self.config, Unset):
            config = UNSET
        elif isinstance(self.config, AppDeploymentReadConfigType0):
            config = self.config.to_dict()
        else:
            config = self.config

        deployed_at: None | str | Unset
        if isinstance(self.deployed_at, Unset):
            deployed_at = UNSET
        elif isinstance(self.deployed_at, datetime.datetime):
            deployed_at = self.deployed_at.isoformat()
        else:
            deployed_at = self.deployed_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "id": id,
                "organization_id": organization_id,
                "user_id": user_id,
                "status": status,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if last_error is not UNSET:
            field_dict["last_error"] = last_error
        if config is not UNSET:
            field_dict["config"] = config
        if deployed_at is not UNSET:
            field_dict["deployed_at"] = deployed_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.app_deployment_read_config_type_0 import (
            AppDeploymentReadConfigType0,
        )  # noqa: PLC0415

        d = dict(src_dict)
        name = d.pop("name")

        id = d.pop("id")

        organization_id = d.pop("organization_id")

        user_id = d.pop("user_id")

        status = AppDeploymentStatus(d.pop("status"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_last_error(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        last_error = _parse_last_error(d.pop("last_error", UNSET))

        def _parse_config(data: object) -> AppDeploymentReadConfigType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                config_type_0 = AppDeploymentReadConfigType0.from_dict(data)

                return config_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AppDeploymentReadConfigType0 | None | Unset, data)

        config = _parse_config(d.pop("config", UNSET))

        def _parse_deployed_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deployed_at_type_0 = datetime.datetime.fromisoformat(data)

                return deployed_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        deployed_at = _parse_deployed_at(d.pop("deployed_at", UNSET))

        app_deployment_read = cls(
            name=name,
            id=id,
            organization_id=organization_id,
            user_id=user_id,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            description=description,
            last_error=last_error,
            config=config,
            deployed_at=deployed_at,
        )

        app_deployment_read.additional_properties = d
        return app_deployment_read

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

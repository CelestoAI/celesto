from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.machine_type import MachineType
    from ..models.recent_sandbox_user_providers import RecentSandboxUserProviders


T = TypeVar("T", bound="RecentSandboxUser")


@_attrs_define
class RecentSandboxUser:
    """
    Attributes:
        user_id (str):
        email (str):
        last_sandbox_created_at (datetime.datetime):
        machines_created (int):
        machine_types (list[MachineType]):
        providers (RecentSandboxUserProviders):
    """

    user_id: str
    email: str
    last_sandbox_created_at: datetime.datetime
    machines_created: int
    machine_types: list[MachineType]
    providers: RecentSandboxUserProviders
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.machine_type import MachineType  # noqa: PLC0415
        from ..models.recent_sandbox_user_providers import RecentSandboxUserProviders  # noqa: PLC0415

        user_id = self.user_id

        email = self.email

        last_sandbox_created_at = self.last_sandbox_created_at.isoformat()

        machines_created = self.machines_created

        machine_types = []
        for machine_types_item_data in self.machine_types:
            machine_types_item = machine_types_item_data.to_dict()
            machine_types.append(machine_types_item)

        providers = self.providers.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
                "email": email,
                "last_sandbox_created_at": last_sandbox_created_at,
                "machines_created": machines_created,
                "machine_types": machine_types,
                "providers": providers,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.machine_type import MachineType  # noqa: PLC0415
        from ..models.recent_sandbox_user_providers import RecentSandboxUserProviders  # noqa: PLC0415

        d = dict(src_dict)
        user_id = d.pop("user_id")

        email = d.pop("email")

        last_sandbox_created_at = datetime.datetime.fromisoformat(
            d.pop("last_sandbox_created_at")
        )

        machines_created = d.pop("machines_created")

        machine_types = []
        _machine_types = d.pop("machine_types")
        for machine_types_item_data in _machine_types:
            machine_types_item = MachineType.from_dict(machine_types_item_data)

            machine_types.append(machine_types_item)

        providers = RecentSandboxUserProviders.from_dict(d.pop("providers"))

        recent_sandbox_user = cls(
            user_id=user_id,
            email=email,
            last_sandbox_created_at=last_sandbox_created_at,
            machines_created=machines_created,
            machine_types=machine_types,
            providers=providers,
        )

        recent_sandbox_user.additional_properties = d
        return recent_sandbox_user

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

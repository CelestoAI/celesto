from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.fleet_host import FleetHost
    from ..models.fleet_provider import FleetProvider


T = TypeVar("T", bound="FleetSnapshot")


@_attrs_define
class FleetSnapshot:
    """
    Attributes:
        observed_at (datetime.datetime):
        providers (list[FleetProvider]):
        hosts (list[FleetHost]):
    """

    observed_at: datetime.datetime
    providers: list[FleetProvider]
    hosts: list[FleetHost]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.fleet_host import FleetHost  # noqa: PLC0415
        from ..models.fleet_provider import FleetProvider  # noqa: PLC0415

        observed_at = self.observed_at.isoformat()

        providers = []
        for providers_item_data in self.providers:
            providers_item = providers_item_data.to_dict()
            providers.append(providers_item)

        hosts = []
        for hosts_item_data in self.hosts:
            hosts_item = hosts_item_data.to_dict()
            hosts.append(hosts_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "observed_at": observed_at,
                "providers": providers,
                "hosts": hosts,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.fleet_host import FleetHost  # noqa: PLC0415
        from ..models.fleet_provider import FleetProvider  # noqa: PLC0415

        d = dict(src_dict)
        observed_at = datetime.datetime.fromisoformat(d.pop("observed_at"))

        providers = []
        _providers = d.pop("providers")
        for providers_item_data in _providers:
            providers_item = FleetProvider.from_dict(providers_item_data)

            providers.append(providers_item)

        hosts = []
        _hosts = d.pop("hosts")
        for hosts_item_data in _hosts:
            hosts_item = FleetHost.from_dict(hosts_item_data)

            hosts.append(hosts_item)

        fleet_snapshot = cls(
            observed_at=observed_at,
            providers=providers,
            hosts=hosts,
        )

        fleet_snapshot.additional_properties = d
        return fleet_snapshot

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

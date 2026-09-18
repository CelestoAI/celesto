from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.computer_connection_info import ComputerConnectionInfo
    from ..models.computer_metrics_summary import ComputerMetricsSummary
    from ..models.computer_published_port_response import ComputerPublishedPortResponse
    from ..models.network_policy import NetworkPolicy


T = TypeVar("T", bound="ComputerResponse")


@_attrs_define
class ComputerResponse:
    """Response for a single compute VM.

    Attributes:
        id (str):
        name (str):
        status (str):
        vcpus (int):
        ram_mb (int):
        disk_size_mb (int):
        image (str):
        created_at (str):
        template_id (str | Unset):  Default: 'scratch'.
        template_version (None | str | Unset):
        network_policy (NetworkPolicy | Unset): Outbound internet access, fixed for the lifetime of a computer.
        external_volume_enabled (bool | Unset):  Default: False.
        connection (ComputerConnectionInfo | None | Unset):
        published_ports (list[ComputerPublishedPortResponse] | Unset):
        metrics (ComputerMetricsSummary | None | Unset):
        last_error (None | str | Unset):
        stopped_at (None | str | Unset):
    """

    id: str
    name: str
    status: str
    vcpus: int
    ram_mb: int
    disk_size_mb: int
    image: str
    created_at: str
    template_id: str | Unset = "scratch"
    template_version: None | str | Unset = UNSET
    network_policy: NetworkPolicy | Unset = UNSET
    external_volume_enabled: bool | Unset = False
    connection: ComputerConnectionInfo | None | Unset = UNSET
    published_ports: list[ComputerPublishedPortResponse] | Unset = UNSET
    metrics: ComputerMetricsSummary | None | Unset = UNSET
    last_error: None | str | Unset = UNSET
    stopped_at: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.computer_connection_info import ComputerConnectionInfo  # noqa: PLC0415
        from ..models.computer_metrics_summary import ComputerMetricsSummary  # noqa: PLC0415
        from ..models.computer_published_port_response import (
            ComputerPublishedPortResponse,
        )  # noqa: PLC0415
        from ..models.network_policy import NetworkPolicy  # noqa: PLC0415

        id = self.id

        name = self.name

        status = self.status

        vcpus = self.vcpus

        ram_mb = self.ram_mb

        disk_size_mb = self.disk_size_mb

        image = self.image

        created_at = self.created_at

        template_id = self.template_id

        template_version: None | str | Unset
        if isinstance(self.template_version, Unset):
            template_version = UNSET
        else:
            template_version = self.template_version

        network_policy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.network_policy, Unset):
            network_policy = self.network_policy.to_dict()

        external_volume_enabled = self.external_volume_enabled

        connection: dict[str, Any] | None | Unset
        if isinstance(self.connection, Unset):
            connection = UNSET
        elif isinstance(self.connection, ComputerConnectionInfo):
            connection = self.connection.to_dict()
        else:
            connection = self.connection

        published_ports: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.published_ports, Unset):
            published_ports = []
            for published_ports_item_data in self.published_ports:
                published_ports_item = published_ports_item_data.to_dict()
                published_ports.append(published_ports_item)

        metrics: dict[str, Any] | None | Unset
        if isinstance(self.metrics, Unset):
            metrics = UNSET
        elif isinstance(self.metrics, ComputerMetricsSummary):
            metrics = self.metrics.to_dict()
        else:
            metrics = self.metrics

        last_error: None | str | Unset
        if isinstance(self.last_error, Unset):
            last_error = UNSET
        else:
            last_error = self.last_error

        stopped_at: None | str | Unset
        if isinstance(self.stopped_at, Unset):
            stopped_at = UNSET
        else:
            stopped_at = self.stopped_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "status": status,
                "vcpus": vcpus,
                "ram_mb": ram_mb,
                "disk_size_mb": disk_size_mb,
                "image": image,
                "created_at": created_at,
            }
        )
        if template_id is not UNSET:
            field_dict["template_id"] = template_id
        if template_version is not UNSET:
            field_dict["template_version"] = template_version
        if network_policy is not UNSET:
            field_dict["network_policy"] = network_policy
        if external_volume_enabled is not UNSET:
            field_dict["external_volume_enabled"] = external_volume_enabled
        if connection is not UNSET:
            field_dict["connection"] = connection
        if published_ports is not UNSET:
            field_dict["published_ports"] = published_ports
        if metrics is not UNSET:
            field_dict["metrics"] = metrics
        if last_error is not UNSET:
            field_dict["last_error"] = last_error
        if stopped_at is not UNSET:
            field_dict["stopped_at"] = stopped_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.computer_connection_info import ComputerConnectionInfo  # noqa: PLC0415
        from ..models.computer_metrics_summary import ComputerMetricsSummary  # noqa: PLC0415
        from ..models.computer_published_port_response import (
            ComputerPublishedPortResponse,
        )  # noqa: PLC0415
        from ..models.network_policy import NetworkPolicy  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        status = d.pop("status")

        vcpus = d.pop("vcpus")

        ram_mb = d.pop("ram_mb")

        disk_size_mb = d.pop("disk_size_mb")

        image = d.pop("image")

        created_at = d.pop("created_at")

        template_id = d.pop("template_id", UNSET)

        def _parse_template_version(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        template_version = _parse_template_version(d.pop("template_version", UNSET))

        _network_policy = d.pop("network_policy", UNSET)
        network_policy: NetworkPolicy | Unset
        if isinstance(_network_policy, Unset):
            network_policy = UNSET
        else:
            network_policy = NetworkPolicy.from_dict(_network_policy)

        external_volume_enabled = d.pop("external_volume_enabled", UNSET)

        def _parse_connection(data: object) -> ComputerConnectionInfo | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                connection_type_0 = ComputerConnectionInfo.from_dict(data)

                return connection_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ComputerConnectionInfo | None | Unset, data)

        connection = _parse_connection(d.pop("connection", UNSET))

        _published_ports = d.pop("published_ports", UNSET)
        published_ports: list[ComputerPublishedPortResponse] | Unset = UNSET
        if _published_ports is not UNSET:
            published_ports = []
            for published_ports_item_data in _published_ports:
                published_ports_item = ComputerPublishedPortResponse.from_dict(
                    published_ports_item_data
                )

                published_ports.append(published_ports_item)

        def _parse_metrics(data: object) -> ComputerMetricsSummary | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metrics_type_0 = ComputerMetricsSummary.from_dict(data)

                return metrics_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(ComputerMetricsSummary | None | Unset, data)

        metrics = _parse_metrics(d.pop("metrics", UNSET))

        def _parse_last_error(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        last_error = _parse_last_error(d.pop("last_error", UNSET))

        def _parse_stopped_at(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        stopped_at = _parse_stopped_at(d.pop("stopped_at", UNSET))

        computer_response = cls(
            id=id,
            name=name,
            status=status,
            vcpus=vcpus,
            ram_mb=ram_mb,
            disk_size_mb=disk_size_mb,
            image=image,
            created_at=created_at,
            template_id=template_id,
            template_version=template_version,
            network_policy=network_policy,
            external_volume_enabled=external_volume_enabled,
            connection=connection,
            published_ports=published_ports,
            metrics=metrics,
            last_error=last_error,
            stopped_at=stopped_at,
        )

        computer_response.additional_properties = d
        return computer_response

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

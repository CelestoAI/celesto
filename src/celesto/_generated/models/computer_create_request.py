from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.network_policy import NetworkPolicy


T = TypeVar("T", bound="ComputerCreateRequest")


@_attrs_define
class ComputerCreateRequest:
    """Request to create a new compute VM.

    Attributes:
        vcpus (int | None | Unset): Number of virtual CPUs
        ram_mb (int | None | Unset): RAM in megabytes
        disk_size_mb (int | None | Unset): Disk size in megabytes (20 GB maximum)
        image (str | Unset):  Default: 'ubuntu-desktop-24.04'.
        template_id (None | str | Unset): Sandbox template id, e.g. scratch or coding-agent
        template_version (None | str | Unset): Optional immutable template version; latest if omitted
        network_policy (NetworkPolicy | Unset): Outbound internet access, fixed for the lifetime of a computer.
        external_volume_enabled (bool | Unset): Attach a persistent external volume at /home/ohm that survives
            stop/restore. Off by default (the sandbox is otherwise ephemeral); cannot be changed after create. Default:
            False.
    """

    vcpus: int | None | Unset = UNSET
    ram_mb: int | None | Unset = UNSET
    disk_size_mb: int | None | Unset = UNSET
    image: str | Unset = "ubuntu-desktop-24.04"
    template_id: None | str | Unset = UNSET
    template_version: None | str | Unset = UNSET
    network_policy: NetworkPolicy | Unset = UNSET
    external_volume_enabled: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.network_policy import NetworkPolicy  # noqa: PLC0415

        vcpus: int | None | Unset
        if isinstance(self.vcpus, Unset):
            vcpus = UNSET
        else:
            vcpus = self.vcpus

        ram_mb: int | None | Unset
        if isinstance(self.ram_mb, Unset):
            ram_mb = UNSET
        else:
            ram_mb = self.ram_mb

        disk_size_mb: int | None | Unset
        if isinstance(self.disk_size_mb, Unset):
            disk_size_mb = UNSET
        else:
            disk_size_mb = self.disk_size_mb

        image = self.image

        template_id: None | str | Unset
        if isinstance(self.template_id, Unset):
            template_id = UNSET
        else:
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

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if vcpus is not UNSET:
            field_dict["vcpus"] = vcpus
        if ram_mb is not UNSET:
            field_dict["ram_mb"] = ram_mb
        if disk_size_mb is not UNSET:
            field_dict["disk_size_mb"] = disk_size_mb
        if image is not UNSET:
            field_dict["image"] = image
        if template_id is not UNSET:
            field_dict["template_id"] = template_id
        if template_version is not UNSET:
            field_dict["template_version"] = template_version
        if network_policy is not UNSET:
            field_dict["network_policy"] = network_policy
        if external_volume_enabled is not UNSET:
            field_dict["external_volume_enabled"] = external_volume_enabled

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.network_policy import NetworkPolicy  # noqa: PLC0415

        d = dict(src_dict)

        def _parse_vcpus(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        vcpus = _parse_vcpus(d.pop("vcpus", UNSET))

        def _parse_ram_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        ram_mb = _parse_ram_mb(d.pop("ram_mb", UNSET))

        def _parse_disk_size_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        disk_size_mb = _parse_disk_size_mb(d.pop("disk_size_mb", UNSET))

        image = d.pop("image", UNSET)

        def _parse_template_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        template_id = _parse_template_id(d.pop("template_id", UNSET))

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

        computer_create_request = cls(
            vcpus=vcpus,
            ram_mb=ram_mb,
            disk_size_mb=disk_size_mb,
            image=image,
            template_id=template_id,
            template_version=template_version,
            network_policy=network_policy,
            external_volume_enabled=external_volume_enabled,
        )

        computer_create_request.additional_properties = d
        return computer_create_request

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

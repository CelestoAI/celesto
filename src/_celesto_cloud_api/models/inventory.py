from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.inventory_computers_item import InventoryComputersItem


T = TypeVar("T", bound="Inventory")


@_attrs_define
class Inventory:
    """
    Attributes:
        kvm_ready (bool | Unset):  Default: False.
        qemu_ready (bool | Unset):  Default: False.
        public_egress_ready (bool | Unset):  Default: False.
        disk_free_mb (int | Unset):  Default: 0.
        disk_total_mb (int | None | Unset):
        computers (list[InventoryComputersItem] | Unset):
        unknown_vm_ids (list[str] | Unset):
        missing_computer_ids (list[str] | Unset):
    """

    kvm_ready: bool | Unset = False
    qemu_ready: bool | Unset = False
    public_egress_ready: bool | Unset = False
    disk_free_mb: int | Unset = 0
    disk_total_mb: int | None | Unset = UNSET
    computers: list[InventoryComputersItem] | Unset = UNSET
    unknown_vm_ids: list[str] | Unset = UNSET
    missing_computer_ids: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.inventory_computers_item import InventoryComputersItem  # noqa: PLC0415

        kvm_ready = self.kvm_ready

        qemu_ready = self.qemu_ready

        public_egress_ready = self.public_egress_ready

        disk_free_mb = self.disk_free_mb

        disk_total_mb: int | None | Unset
        if isinstance(self.disk_total_mb, Unset):
            disk_total_mb = UNSET
        else:
            disk_total_mb = self.disk_total_mb

        computers: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.computers, Unset):
            computers = []
            for computers_item_data in self.computers:
                computers_item = computers_item_data.to_dict()
                computers.append(computers_item)

        unknown_vm_ids: list[str] | Unset = UNSET
        if not isinstance(self.unknown_vm_ids, Unset):
            unknown_vm_ids = self.unknown_vm_ids

        missing_computer_ids: list[str] | Unset = UNSET
        if not isinstance(self.missing_computer_ids, Unset):
            missing_computer_ids = self.missing_computer_ids

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if kvm_ready is not UNSET:
            field_dict["kvm_ready"] = kvm_ready
        if qemu_ready is not UNSET:
            field_dict["qemu_ready"] = qemu_ready
        if public_egress_ready is not UNSET:
            field_dict["public_egress_ready"] = public_egress_ready
        if disk_free_mb is not UNSET:
            field_dict["disk_free_mb"] = disk_free_mb
        if disk_total_mb is not UNSET:
            field_dict["disk_total_mb"] = disk_total_mb
        if computers is not UNSET:
            field_dict["computers"] = computers
        if unknown_vm_ids is not UNSET:
            field_dict["unknown_vm_ids"] = unknown_vm_ids
        if missing_computer_ids is not UNSET:
            field_dict["missing_computer_ids"] = missing_computer_ids

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_computers_item import InventoryComputersItem  # noqa: PLC0415

        d = dict(src_dict)
        kvm_ready = d.pop("kvm_ready", UNSET)

        qemu_ready = d.pop("qemu_ready", UNSET)

        public_egress_ready = d.pop("public_egress_ready", UNSET)

        disk_free_mb = d.pop("disk_free_mb", UNSET)

        def _parse_disk_total_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        disk_total_mb = _parse_disk_total_mb(d.pop("disk_total_mb", UNSET))

        _computers = d.pop("computers", UNSET)
        computers: list[InventoryComputersItem] | Unset = UNSET
        if _computers is not UNSET:
            computers = []
            for computers_item_data in _computers:
                computers_item = InventoryComputersItem.from_dict(computers_item_data)

                computers.append(computers_item)

        unknown_vm_ids = cast(list[str], d.pop("unknown_vm_ids", UNSET))

        missing_computer_ids = cast(list[str], d.pop("missing_computer_ids", UNSET))

        inventory = cls(
            kvm_ready=kvm_ready,
            qemu_ready=qemu_ready,
            public_egress_ready=public_egress_ready,
            disk_free_mb=disk_free_mb,
            disk_total_mb=disk_total_mb,
            computers=computers,
            unknown_vm_ids=unknown_vm_ids,
            missing_computer_ids=missing_computer_ids,
        )

        inventory.additional_properties = d
        return inventory

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

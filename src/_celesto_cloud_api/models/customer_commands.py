from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast

if TYPE_CHECKING:
    from ..models.customer_commands_statuses import CustomerCommandsStatuses
    from ..models.failed_exit_code import FailedExitCode


T = TypeVar("T", bound="CustomerCommands")


@_attrs_define
class CustomerCommands:
    """
    Attributes:
        total (int):
        statuses (CustomerCommandsStatuses):
        failed_exit_codes (list[FailedExitCode]):
    """

    total: int
    statuses: CustomerCommandsStatuses
    failed_exit_codes: list[FailedExitCode]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.customer_commands_statuses import CustomerCommandsStatuses  # noqa: PLC0415
        from ..models.failed_exit_code import FailedExitCode  # noqa: PLC0415

        total = self.total

        statuses = self.statuses.to_dict()

        failed_exit_codes = []
        for failed_exit_codes_item_data in self.failed_exit_codes:
            failed_exit_codes_item = failed_exit_codes_item_data.to_dict()
            failed_exit_codes.append(failed_exit_codes_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total": total,
                "statuses": statuses,
                "failed_exit_codes": failed_exit_codes,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.customer_commands_statuses import CustomerCommandsStatuses  # noqa: PLC0415
        from ..models.failed_exit_code import FailedExitCode  # noqa: PLC0415

        d = dict(src_dict)
        total = d.pop("total")

        statuses = CustomerCommandsStatuses.from_dict(d.pop("statuses"))

        failed_exit_codes = []
        _failed_exit_codes = d.pop("failed_exit_codes")
        for failed_exit_codes_item_data in _failed_exit_codes:
            failed_exit_codes_item = FailedExitCode.from_dict(
                failed_exit_codes_item_data
            )

            failed_exit_codes.append(failed_exit_codes_item)

        customer_commands = cls(
            total=total,
            statuses=statuses,
            failed_exit_codes=failed_exit_codes,
        )

        customer_commands.additional_properties = d
        return customer_commands

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

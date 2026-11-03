from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.operator_billing_report_payments_status import (
    OperatorBillingReportPaymentsStatus,
)
from ..types import UNSET, Unset
from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.organization_billing import OrganizationBilling


T = TypeVar("T", bound="OperatorBillingReport")


@_attrs_define
class OperatorBillingReport:
    """
    Attributes:
        observed_at (datetime.datetime):
        completed_at (datetime.datetime):
        payments_status (OperatorBillingReportPaymentsStatus):
        organizations (list[OrganizationBilling]):
        warnings (list[str] | Unset):
    """

    observed_at: datetime.datetime
    completed_at: datetime.datetime
    payments_status: OperatorBillingReportPaymentsStatus
    organizations: list[OrganizationBilling]
    warnings: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.organization_billing import OrganizationBilling  # noqa: PLC0415

        observed_at = self.observed_at.isoformat()

        completed_at = self.completed_at.isoformat()

        payments_status = self.payments_status.value

        organizations = []
        for organizations_item_data in self.organizations:
            organizations_item = organizations_item_data.to_dict()
            organizations.append(organizations_item)

        warnings: list[str] | Unset = UNSET
        if not isinstance(self.warnings, Unset):
            warnings = self.warnings

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "observed_at": observed_at,
                "completed_at": completed_at,
                "payments_status": payments_status,
                "organizations": organizations,
            }
        )
        if warnings is not UNSET:
            field_dict["warnings"] = warnings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.organization_billing import OrganizationBilling  # noqa: PLC0415

        d = dict(src_dict)
        observed_at = datetime.datetime.fromisoformat(d.pop("observed_at"))

        completed_at = datetime.datetime.fromisoformat(d.pop("completed_at"))

        payments_status = OperatorBillingReportPaymentsStatus(d.pop("payments_status"))

        organizations = []
        _organizations = d.pop("organizations")
        for organizations_item_data in _organizations:
            organizations_item = OrganizationBilling.from_dict(organizations_item_data)

            organizations.append(organizations_item)

        warnings = cast(list[str], d.pop("warnings", UNSET))

        operator_billing_report = cls(
            observed_at=observed_at,
            completed_at=completed_at,
            payments_status=payments_status,
            organizations=organizations,
            warnings=warnings,
        )

        operator_billing_report.additional_properties = d
        return operator_billing_report

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

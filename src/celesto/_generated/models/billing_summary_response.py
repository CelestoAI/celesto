from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast

if TYPE_CHECKING:
    from ..models.billing_plan_entitlements_response import (
        BillingPlanEntitlementsResponse,
    )
    from ..models.resource_limit_summary import ResourceLimitSummary
    from ..models.sandbox_hours_usage_summary import SandboxHoursUsageSummary
    from ..models.usage_summary import UsageSummary


T = TypeVar("T", bound="BillingSummaryResponse")


@_attrs_define
class BillingSummaryResponse:
    """Response schema for billing summary.

    Attributes:
        plan_id (str): Current subscription plan ID
        plan_name (str): Human-readable plan name
        billing_status (str): Billing status (active, depleted, etc)
        entitlements (BillingPlanEntitlementsResponse): Plan entitlements exposed by the billing plans endpoint.
        sandbox_hours (SandboxHoursUsageSummary): Current standard sandbox-hour usage reported by Autumn.
        concurrent_sandboxes (ResourceLimitSummary): Current usage summary for a non-metered resource cap.
        runs (UsageSummary): Usage summary for a single billing unit.
        tool_calls (UsageSummary): Usage summary for a single billing unit.
        openclaw_instances (ResourceLimitSummary): Current usage summary for a non-metered resource cap.
        hermes_instances (ResourceLimitSummary): Current usage summary for a non-metered resource cap.
    """

    plan_id: str
    plan_name: str
    billing_status: str
    entitlements: BillingPlanEntitlementsResponse
    sandbox_hours: SandboxHoursUsageSummary
    concurrent_sandboxes: ResourceLimitSummary
    runs: UsageSummary
    tool_calls: UsageSummary
    openclaw_instances: ResourceLimitSummary
    hermes_instances: ResourceLimitSummary
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.billing_plan_entitlements_response import (
            BillingPlanEntitlementsResponse,
        )  # noqa: PLC0415
        from ..models.resource_limit_summary import ResourceLimitSummary  # noqa: PLC0415
        from ..models.sandbox_hours_usage_summary import SandboxHoursUsageSummary  # noqa: PLC0415
        from ..models.usage_summary import UsageSummary  # noqa: PLC0415

        plan_id = self.plan_id

        plan_name = self.plan_name

        billing_status = self.billing_status

        entitlements = self.entitlements.to_dict()

        sandbox_hours = self.sandbox_hours.to_dict()

        concurrent_sandboxes = self.concurrent_sandboxes.to_dict()

        runs = self.runs.to_dict()

        tool_calls = self.tool_calls.to_dict()

        openclaw_instances = self.openclaw_instances.to_dict()

        hermes_instances = self.hermes_instances.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "plan_id": plan_id,
                "plan_name": plan_name,
                "billing_status": billing_status,
                "entitlements": entitlements,
                "sandbox_hours": sandbox_hours,
                "concurrent_sandboxes": concurrent_sandboxes,
                "runs": runs,
                "tool_calls": tool_calls,
                "openclaw_instances": openclaw_instances,
                "hermes_instances": hermes_instances,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.billing_plan_entitlements_response import (
            BillingPlanEntitlementsResponse,
        )  # noqa: PLC0415
        from ..models.resource_limit_summary import ResourceLimitSummary  # noqa: PLC0415
        from ..models.sandbox_hours_usage_summary import SandboxHoursUsageSummary  # noqa: PLC0415
        from ..models.usage_summary import UsageSummary  # noqa: PLC0415

        d = dict(src_dict)
        plan_id = d.pop("plan_id")

        plan_name = d.pop("plan_name")

        billing_status = d.pop("billing_status")

        entitlements = BillingPlanEntitlementsResponse.from_dict(d.pop("entitlements"))

        sandbox_hours = SandboxHoursUsageSummary.from_dict(d.pop("sandbox_hours"))

        concurrent_sandboxes = ResourceLimitSummary.from_dict(
            d.pop("concurrent_sandboxes")
        )

        runs = UsageSummary.from_dict(d.pop("runs"))

        tool_calls = UsageSummary.from_dict(d.pop("tool_calls"))

        openclaw_instances = ResourceLimitSummary.from_dict(d.pop("openclaw_instances"))

        hermes_instances = ResourceLimitSummary.from_dict(d.pop("hermes_instances"))

        billing_summary_response = cls(
            plan_id=plan_id,
            plan_name=plan_name,
            billing_status=billing_status,
            entitlements=entitlements,
            sandbox_hours=sandbox_hours,
            concurrent_sandboxes=concurrent_sandboxes,
            runs=runs,
            tool_calls=tool_calls,
            openclaw_instances=openclaw_instances,
            hermes_instances=hermes_instances,
        )

        billing_summary_response.additional_properties = d
        return billing_summary_response

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

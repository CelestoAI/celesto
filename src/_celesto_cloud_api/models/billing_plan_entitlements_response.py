from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast

if TYPE_CHECKING:
    from ..models.concurrent_sandboxes_entitlement_response import (
        ConcurrentSandboxesEntitlementResponse,
    )
    from ..models.hermes_instances_entitlement_response import (
        HermesInstancesEntitlementResponse,
    )
    from ..models.open_claw_instances_entitlement_response import (
        OpenClawInstancesEntitlementResponse,
    )
    from ..models.sandbox_capability_response import SandboxCapabilityResponse
    from ..models.sandbox_hours_entitlement_response import (
        SandboxHoursEntitlementResponse,
    )


T = TypeVar("T", bound="BillingPlanEntitlementsResponse")


@_attrs_define
class BillingPlanEntitlementsResponse:
    """Plan entitlements exposed by the billing plans endpoint.

    Attributes:
        sandbox_hours (SandboxHoursEntitlementResponse): Included active sandbox hours and optional overage pricing.
        concurrent_sandboxes (ConcurrentSandboxesEntitlementResponse): Shared active sandbox concurrency limit for a
            plan.
        flexible_sandbox_sizes (SandboxCapabilityResponse): Boolean sandbox capability included with a plan.
        managed_runtimes (SandboxCapabilityResponse): Boolean sandbox capability included with a plan.
        openclaw_instances (OpenClawInstancesEntitlementResponse): OpenClaw instance limit for a plan.
        hermes_instances (HermesInstancesEntitlementResponse): Hermes instance limit for a plan.
    """

    sandbox_hours: SandboxHoursEntitlementResponse
    concurrent_sandboxes: ConcurrentSandboxesEntitlementResponse
    flexible_sandbox_sizes: SandboxCapabilityResponse
    managed_runtimes: SandboxCapabilityResponse
    openclaw_instances: OpenClawInstancesEntitlementResponse
    hermes_instances: HermesInstancesEntitlementResponse
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.concurrent_sandboxes_entitlement_response import (
            ConcurrentSandboxesEntitlementResponse,
        )  # noqa: PLC0415
        from ..models.hermes_instances_entitlement_response import (
            HermesInstancesEntitlementResponse,
        )  # noqa: PLC0415
        from ..models.open_claw_instances_entitlement_response import (
            OpenClawInstancesEntitlementResponse,
        )  # noqa: PLC0415
        from ..models.sandbox_capability_response import SandboxCapabilityResponse  # noqa: PLC0415
        from ..models.sandbox_hours_entitlement_response import (
            SandboxHoursEntitlementResponse,
        )  # noqa: PLC0415

        sandbox_hours = self.sandbox_hours.to_dict()

        concurrent_sandboxes = self.concurrent_sandboxes.to_dict()

        flexible_sandbox_sizes = self.flexible_sandbox_sizes.to_dict()

        managed_runtimes = self.managed_runtimes.to_dict()

        openclaw_instances = self.openclaw_instances.to_dict()

        hermes_instances = self.hermes_instances.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sandbox_hours": sandbox_hours,
                "concurrent_sandboxes": concurrent_sandboxes,
                "flexible_sandbox_sizes": flexible_sandbox_sizes,
                "managed_runtimes": managed_runtimes,
                "openclaw_instances": openclaw_instances,
                "hermes_instances": hermes_instances,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.concurrent_sandboxes_entitlement_response import (
            ConcurrentSandboxesEntitlementResponse,
        )  # noqa: PLC0415
        from ..models.hermes_instances_entitlement_response import (
            HermesInstancesEntitlementResponse,
        )  # noqa: PLC0415
        from ..models.open_claw_instances_entitlement_response import (
            OpenClawInstancesEntitlementResponse,
        )  # noqa: PLC0415
        from ..models.sandbox_capability_response import SandboxCapabilityResponse  # noqa: PLC0415
        from ..models.sandbox_hours_entitlement_response import (
            SandboxHoursEntitlementResponse,
        )  # noqa: PLC0415

        d = dict(src_dict)
        sandbox_hours = SandboxHoursEntitlementResponse.from_dict(
            d.pop("sandbox_hours")
        )

        concurrent_sandboxes = ConcurrentSandboxesEntitlementResponse.from_dict(
            d.pop("concurrent_sandboxes")
        )

        flexible_sandbox_sizes = SandboxCapabilityResponse.from_dict(
            d.pop("flexible_sandbox_sizes")
        )

        managed_runtimes = SandboxCapabilityResponse.from_dict(
            d.pop("managed_runtimes")
        )

        openclaw_instances = OpenClawInstancesEntitlementResponse.from_dict(
            d.pop("openclaw_instances")
        )

        hermes_instances = HermesInstancesEntitlementResponse.from_dict(
            d.pop("hermes_instances")
        )

        billing_plan_entitlements_response = cls(
            sandbox_hours=sandbox_hours,
            concurrent_sandboxes=concurrent_sandboxes,
            flexible_sandbox_sizes=flexible_sandbox_sizes,
            managed_runtimes=managed_runtimes,
            openclaw_instances=openclaw_instances,
            hermes_instances=hermes_instances,
        )

        billing_plan_entitlements_response.additional_properties = d
        return billing_plan_entitlements_response

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

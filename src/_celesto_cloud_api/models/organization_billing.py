from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.organization_billing_balance_status import (
    OrganizationBillingBalanceStatus,
)
from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.billing_payment import BillingPayment
    from ..models.billing_runtime import BillingRuntime
    from ..models.billing_wallet import BillingWallet


T = TypeVar("T", bound="OrganizationBilling")


@_attrs_define
class OrganizationBilling:
    """
    Attributes:
        organization_id (str):
        name (str):
        email (None | str):
        owner_emails (list[str]):
        internal (bool):
        collected_usd (None | str | Unset):
        refunded_usd (None | str | Unset):
        net_collected_usd (None | str | Unset):
        disputed_usd (None | str | Unset): Net value of payments with a dispute flag, not the actual disputed amount;
            disputes may be partial.
        payments (list[BillingPayment] | Unset):
        balance_status (OrganizationBillingBalanceStatus | Unset):  Default:
            OrganizationBillingBalanceStatus.UNAVAILABLE.
        paid_credit_granted_usd (None | str | Unset):
        paid_credit_remaining_usd (None | str | Unset):
        paid_credit_used_estimate_usd (None | str | Unset):
        promotional_wallets (list[BillingWallet] | Unset):
        runtime_by_size (list[BillingRuntime] | Unset):
        warnings (list[str] | Unset):
    """

    organization_id: str
    name: str
    email: None | str
    owner_emails: list[str]
    internal: bool
    collected_usd: None | str | Unset = UNSET
    refunded_usd: None | str | Unset = UNSET
    net_collected_usd: None | str | Unset = UNSET
    disputed_usd: None | str | Unset = UNSET
    payments: list[BillingPayment] | Unset = UNSET
    balance_status: OrganizationBillingBalanceStatus | Unset = (
        OrganizationBillingBalanceStatus.UNAVAILABLE
    )
    paid_credit_granted_usd: None | str | Unset = UNSET
    paid_credit_remaining_usd: None | str | Unset = UNSET
    paid_credit_used_estimate_usd: None | str | Unset = UNSET
    promotional_wallets: list[BillingWallet] | Unset = UNSET
    runtime_by_size: list[BillingRuntime] | Unset = UNSET
    warnings: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.billing_payment import BillingPayment  # noqa: PLC0415
        from ..models.billing_runtime import BillingRuntime  # noqa: PLC0415
        from ..models.billing_wallet import BillingWallet  # noqa: PLC0415

        organization_id = self.organization_id

        name = self.name

        email: None | str
        email = self.email

        owner_emails = self.owner_emails

        internal = self.internal

        collected_usd: None | str | Unset
        if isinstance(self.collected_usd, Unset):
            collected_usd = UNSET
        else:
            collected_usd = self.collected_usd

        refunded_usd: None | str | Unset
        if isinstance(self.refunded_usd, Unset):
            refunded_usd = UNSET
        else:
            refunded_usd = self.refunded_usd

        net_collected_usd: None | str | Unset
        if isinstance(self.net_collected_usd, Unset):
            net_collected_usd = UNSET
        else:
            net_collected_usd = self.net_collected_usd

        disputed_usd: None | str | Unset
        if isinstance(self.disputed_usd, Unset):
            disputed_usd = UNSET
        else:
            disputed_usd = self.disputed_usd

        payments: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.payments, Unset):
            payments = []
            for payments_item_data in self.payments:
                payments_item = payments_item_data.to_dict()
                payments.append(payments_item)

        balance_status: str | Unset = UNSET
        if not isinstance(self.balance_status, Unset):
            balance_status = self.balance_status.value

        paid_credit_granted_usd: None | str | Unset
        if isinstance(self.paid_credit_granted_usd, Unset):
            paid_credit_granted_usd = UNSET
        else:
            paid_credit_granted_usd = self.paid_credit_granted_usd

        paid_credit_remaining_usd: None | str | Unset
        if isinstance(self.paid_credit_remaining_usd, Unset):
            paid_credit_remaining_usd = UNSET
        else:
            paid_credit_remaining_usd = self.paid_credit_remaining_usd

        paid_credit_used_estimate_usd: None | str | Unset
        if isinstance(self.paid_credit_used_estimate_usd, Unset):
            paid_credit_used_estimate_usd = UNSET
        else:
            paid_credit_used_estimate_usd = self.paid_credit_used_estimate_usd

        promotional_wallets: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.promotional_wallets, Unset):
            promotional_wallets = []
            for promotional_wallets_item_data in self.promotional_wallets:
                promotional_wallets_item = promotional_wallets_item_data.to_dict()
                promotional_wallets.append(promotional_wallets_item)

        runtime_by_size: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.runtime_by_size, Unset):
            runtime_by_size = []
            for runtime_by_size_item_data in self.runtime_by_size:
                runtime_by_size_item = runtime_by_size_item_data.to_dict()
                runtime_by_size.append(runtime_by_size_item)

        warnings: list[str] | Unset = UNSET
        if not isinstance(self.warnings, Unset):
            warnings = self.warnings

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "organization_id": organization_id,
                "name": name,
                "email": email,
                "owner_emails": owner_emails,
                "internal": internal,
            }
        )
        if collected_usd is not UNSET:
            field_dict["collected_usd"] = collected_usd
        if refunded_usd is not UNSET:
            field_dict["refunded_usd"] = refunded_usd
        if net_collected_usd is not UNSET:
            field_dict["net_collected_usd"] = net_collected_usd
        if disputed_usd is not UNSET:
            field_dict["disputed_usd"] = disputed_usd
        if payments is not UNSET:
            field_dict["payments"] = payments
        if balance_status is not UNSET:
            field_dict["balance_status"] = balance_status
        if paid_credit_granted_usd is not UNSET:
            field_dict["paid_credit_granted_usd"] = paid_credit_granted_usd
        if paid_credit_remaining_usd is not UNSET:
            field_dict["paid_credit_remaining_usd"] = paid_credit_remaining_usd
        if paid_credit_used_estimate_usd is not UNSET:
            field_dict["paid_credit_used_estimate_usd"] = paid_credit_used_estimate_usd
        if promotional_wallets is not UNSET:
            field_dict["promotional_wallets"] = promotional_wallets
        if runtime_by_size is not UNSET:
            field_dict["runtime_by_size"] = runtime_by_size
        if warnings is not UNSET:
            field_dict["warnings"] = warnings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.billing_payment import BillingPayment  # noqa: PLC0415
        from ..models.billing_runtime import BillingRuntime  # noqa: PLC0415
        from ..models.billing_wallet import BillingWallet  # noqa: PLC0415

        d = dict(src_dict)
        organization_id = d.pop("organization_id")

        name = d.pop("name")

        def _parse_email(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        email = _parse_email(d.pop("email"))

        owner_emails = cast(list[str], d.pop("owner_emails"))

        internal = d.pop("internal")

        def _parse_collected_usd(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        collected_usd = _parse_collected_usd(d.pop("collected_usd", UNSET))

        def _parse_refunded_usd(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        refunded_usd = _parse_refunded_usd(d.pop("refunded_usd", UNSET))

        def _parse_net_collected_usd(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        net_collected_usd = _parse_net_collected_usd(d.pop("net_collected_usd", UNSET))

        def _parse_disputed_usd(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        disputed_usd = _parse_disputed_usd(d.pop("disputed_usd", UNSET))

        _payments = d.pop("payments", UNSET)
        payments: list[BillingPayment] | Unset = UNSET
        if _payments is not UNSET:
            payments = []
            for payments_item_data in _payments:
                payments_item = BillingPayment.from_dict(payments_item_data)

                payments.append(payments_item)

        _balance_status = d.pop("balance_status", UNSET)
        balance_status: OrganizationBillingBalanceStatus | Unset
        if isinstance(_balance_status, Unset):
            balance_status = UNSET
        else:
            balance_status = OrganizationBillingBalanceStatus(_balance_status)

        def _parse_paid_credit_granted_usd(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        paid_credit_granted_usd = _parse_paid_credit_granted_usd(
            d.pop("paid_credit_granted_usd", UNSET)
        )

        def _parse_paid_credit_remaining_usd(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        paid_credit_remaining_usd = _parse_paid_credit_remaining_usd(
            d.pop("paid_credit_remaining_usd", UNSET)
        )

        def _parse_paid_credit_used_estimate_usd(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        paid_credit_used_estimate_usd = _parse_paid_credit_used_estimate_usd(
            d.pop("paid_credit_used_estimate_usd", UNSET)
        )

        _promotional_wallets = d.pop("promotional_wallets", UNSET)
        promotional_wallets: list[BillingWallet] | Unset = UNSET
        if _promotional_wallets is not UNSET:
            promotional_wallets = []
            for promotional_wallets_item_data in _promotional_wallets:
                promotional_wallets_item = BillingWallet.from_dict(
                    promotional_wallets_item_data
                )

                promotional_wallets.append(promotional_wallets_item)

        _runtime_by_size = d.pop("runtime_by_size", UNSET)
        runtime_by_size: list[BillingRuntime] | Unset = UNSET
        if _runtime_by_size is not UNSET:
            runtime_by_size = []
            for runtime_by_size_item_data in _runtime_by_size:
                runtime_by_size_item = BillingRuntime.from_dict(
                    runtime_by_size_item_data
                )

                runtime_by_size.append(runtime_by_size_item)

        warnings = cast(list[str], d.pop("warnings", UNSET))

        organization_billing = cls(
            organization_id=organization_id,
            name=name,
            email=email,
            owner_emails=owner_emails,
            internal=internal,
            collected_usd=collected_usd,
            refunded_usd=refunded_usd,
            net_collected_usd=net_collected_usd,
            disputed_usd=disputed_usd,
            payments=payments,
            balance_status=balance_status,
            paid_credit_granted_usd=paid_credit_granted_usd,
            paid_credit_remaining_usd=paid_credit_remaining_usd,
            paid_credit_used_estimate_usd=paid_credit_used_estimate_usd,
            promotional_wallets=promotional_wallets,
            runtime_by_size=runtime_by_size,
            warnings=warnings,
        )

        organization_billing.additional_properties = d
        return organization_billing

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

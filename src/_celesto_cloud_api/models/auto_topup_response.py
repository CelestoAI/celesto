from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.auto_topup_response_paused_reason_type_0 import (
    AutoTopupResponsePausedReasonType0,
)
from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.auto_topup_charge_response import AutoTopupChargeResponse


T = TypeVar("T", bound="AutoTopupResponse")


@_attrs_define
class AutoTopupResponse:
    """Auto top-up settings and state; defaults when it was never set up.

    Attributes:
        enabled (bool):
        threshold_usd (str):
        amount_usd (str):
        monthly_limit_usd (str):
        month_charged_usd (str):
        monthly_limit_reached (bool):
        payment_method_label (None | str | Unset):
        paused_reason (AutoTopupResponsePausedReasonType0 | None | Unset):
        paused_message (None | str | Unset):
        last_charge (AutoTopupChargeResponse | None | Unset):
    """

    enabled: bool
    threshold_usd: str
    amount_usd: str
    monthly_limit_usd: str
    month_charged_usd: str
    monthly_limit_reached: bool
    payment_method_label: None | str | Unset = UNSET
    paused_reason: AutoTopupResponsePausedReasonType0 | None | Unset = UNSET
    paused_message: None | str | Unset = UNSET
    last_charge: AutoTopupChargeResponse | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.auto_topup_charge_response import AutoTopupChargeResponse  # noqa: PLC0415

        enabled = self.enabled

        threshold_usd = self.threshold_usd

        amount_usd = self.amount_usd

        monthly_limit_usd = self.monthly_limit_usd

        month_charged_usd = self.month_charged_usd

        monthly_limit_reached = self.monthly_limit_reached

        payment_method_label: None | str | Unset
        if isinstance(self.payment_method_label, Unset):
            payment_method_label = UNSET
        else:
            payment_method_label = self.payment_method_label

        paused_reason: None | str | Unset
        if isinstance(self.paused_reason, Unset):
            paused_reason = UNSET
        elif isinstance(self.paused_reason, AutoTopupResponsePausedReasonType0):
            paused_reason = self.paused_reason.value
        else:
            paused_reason = self.paused_reason

        paused_message: None | str | Unset
        if isinstance(self.paused_message, Unset):
            paused_message = UNSET
        else:
            paused_message = self.paused_message

        last_charge: dict[str, Any] | None | Unset
        if isinstance(self.last_charge, Unset):
            last_charge = UNSET
        elif isinstance(self.last_charge, AutoTopupChargeResponse):
            last_charge = self.last_charge.to_dict()
        else:
            last_charge = self.last_charge

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "enabled": enabled,
                "threshold_usd": threshold_usd,
                "amount_usd": amount_usd,
                "monthly_limit_usd": monthly_limit_usd,
                "month_charged_usd": month_charged_usd,
                "monthly_limit_reached": monthly_limit_reached,
            }
        )
        if payment_method_label is not UNSET:
            field_dict["payment_method_label"] = payment_method_label
        if paused_reason is not UNSET:
            field_dict["paused_reason"] = paused_reason
        if paused_message is not UNSET:
            field_dict["paused_message"] = paused_message
        if last_charge is not UNSET:
            field_dict["last_charge"] = last_charge

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.auto_topup_charge_response import AutoTopupChargeResponse  # noqa: PLC0415

        d = dict(src_dict)
        enabled = d.pop("enabled")

        threshold_usd = d.pop("threshold_usd")

        amount_usd = d.pop("amount_usd")

        monthly_limit_usd = d.pop("monthly_limit_usd")

        month_charged_usd = d.pop("month_charged_usd")

        monthly_limit_reached = d.pop("monthly_limit_reached")

        def _parse_payment_method_label(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        payment_method_label = _parse_payment_method_label(
            d.pop("payment_method_label", UNSET)
        )

        def _parse_paused_reason(
            data: object,
        ) -> AutoTopupResponsePausedReasonType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                paused_reason_type_0 = AutoTopupResponsePausedReasonType0(data)

                return paused_reason_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AutoTopupResponsePausedReasonType0 | None | Unset, data)

        paused_reason = _parse_paused_reason(d.pop("paused_reason", UNSET))

        def _parse_paused_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        paused_message = _parse_paused_message(d.pop("paused_message", UNSET))

        def _parse_last_charge(data: object) -> AutoTopupChargeResponse | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                last_charge_type_0 = AutoTopupChargeResponse.from_dict(data)

                return last_charge_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AutoTopupChargeResponse | None | Unset, data)

        last_charge = _parse_last_charge(d.pop("last_charge", UNSET))

        auto_topup_response = cls(
            enabled=enabled,
            threshold_usd=threshold_usd,
            amount_usd=amount_usd,
            monthly_limit_usd=monthly_limit_usd,
            month_charged_usd=month_charged_usd,
            monthly_limit_reached=monthly_limit_reached,
            payment_method_label=payment_method_label,
            paused_reason=paused_reason,
            paused_message=paused_message,
            last_charge=last_charge,
        )

        auto_topup_response.additional_properties = d
        return auto_topup_response

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

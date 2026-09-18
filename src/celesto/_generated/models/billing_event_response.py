from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.billing_event_type import BillingEventType
from ..models.billing_unit import BillingUnit
from ..types import UNSET, Unset
from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.billing_event_response_event_metadata import (
        BillingEventResponseEventMetadata,
    )


T = TypeVar("T", bound="BillingEventResponse")


@_attrs_define
class BillingEventResponse:
    """Response schema for billing events.

    Attributes:
        id (str): Billing event ID
        organization_id (str): Organization ID
        user_id (str): User ID
        event_type (BillingEventType): Types of billable events
        quantity (int): Quantity of units
        amount_usd (str): Amount charged in USD
        balance_before (str): Balance before deduction
        balance_after (str): Balance after deduction
        created_at (datetime.datetime): When the event was created
        unit (BillingUnit | None | Unset): Billing unit (run or tool_call)
        description (None | str | Unset): Event description
        event_metadata (BillingEventResponseEventMetadata | Unset): Event metadata
        request_id (None | str | Unset): Request ID for tracking
    """

    id: str
    organization_id: str
    user_id: str
    event_type: BillingEventType
    quantity: int
    amount_usd: str
    balance_before: str
    balance_after: str
    created_at: datetime.datetime
    unit: BillingUnit | None | Unset = UNSET
    description: None | str | Unset = UNSET
    event_metadata: BillingEventResponseEventMetadata | Unset = UNSET
    request_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.billing_event_response_event_metadata import (
            BillingEventResponseEventMetadata,
        )  # noqa: PLC0415

        id = self.id

        organization_id = self.organization_id

        user_id = self.user_id

        event_type = self.event_type.value

        quantity = self.quantity

        amount_usd = self.amount_usd

        balance_before = self.balance_before

        balance_after = self.balance_after

        created_at = self.created_at.isoformat()

        unit: None | str | Unset
        if isinstance(self.unit, Unset):
            unit = UNSET
        elif isinstance(self.unit, BillingUnit):
            unit = self.unit.value
        else:
            unit = self.unit

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        event_metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.event_metadata, Unset):
            event_metadata = self.event_metadata.to_dict()

        request_id: None | str | Unset
        if isinstance(self.request_id, Unset):
            request_id = UNSET
        else:
            request_id = self.request_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "organization_id": organization_id,
                "user_id": user_id,
                "event_type": event_type,
                "quantity": quantity,
                "amount_usd": amount_usd,
                "balance_before": balance_before,
                "balance_after": balance_after,
                "created_at": created_at,
            }
        )
        if unit is not UNSET:
            field_dict["unit"] = unit
        if description is not UNSET:
            field_dict["description"] = description
        if event_metadata is not UNSET:
            field_dict["event_metadata"] = event_metadata
        if request_id is not UNSET:
            field_dict["request_id"] = request_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.billing_event_response_event_metadata import (
            BillingEventResponseEventMetadata,
        )  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        organization_id = d.pop("organization_id")

        user_id = d.pop("user_id")

        event_type = BillingEventType(d.pop("event_type"))

        quantity = d.pop("quantity")

        amount_usd = d.pop("amount_usd")

        balance_before = d.pop("balance_before")

        balance_after = d.pop("balance_after")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        def _parse_unit(data: object) -> BillingUnit | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                unit_type_0 = BillingUnit(data)

                return unit_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(BillingUnit | None | Unset, data)

        unit = _parse_unit(d.pop("unit", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        _event_metadata = d.pop("event_metadata", UNSET)
        event_metadata: BillingEventResponseEventMetadata | Unset
        if isinstance(_event_metadata, Unset):
            event_metadata = UNSET
        else:
            event_metadata = BillingEventResponseEventMetadata.from_dict(
                _event_metadata
            )

        def _parse_request_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        request_id = _parse_request_id(d.pop("request_id", UNSET))

        billing_event_response = cls(
            id=id,
            organization_id=organization_id,
            user_id=user_id,
            event_type=event_type,
            quantity=quantity,
            amount_usd=amount_usd,
            balance_before=balance_before,
            balance_after=balance_after,
            created_at=created_at,
            unit=unit,
            description=description,
            event_metadata=event_metadata,
            request_id=request_id,
        )

        billing_event_response.additional_properties = d
        return billing_event_response

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

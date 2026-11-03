from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.auto_topup_charge_response_status import AutoTopupChargeResponseStatus
from ..types import UNSET, Unset
from typing import cast
import datetime


T = TypeVar("T", bound="AutoTopupChargeResponse")


@_attrs_define
class AutoTopupChargeResponse:
    """The latest auto top-up attempt.

    Attributes:
        status (AutoTopupChargeResponseStatus):
        amount_usd (str):
        created_at (datetime.datetime):
        failure_message (None | str | Unset):
    """

    status: AutoTopupChargeResponseStatus
    amount_usd: str
    created_at: datetime.datetime
    failure_message: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status = self.status.value

        amount_usd = self.amount_usd

        created_at = self.created_at.isoformat()

        failure_message: None | str | Unset
        if isinstance(self.failure_message, Unset):
            failure_message = UNSET
        else:
            failure_message = self.failure_message

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "status": status,
                "amount_usd": amount_usd,
                "created_at": created_at,
            }
        )
        if failure_message is not UNSET:
            field_dict["failure_message"] = failure_message

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        status = AutoTopupChargeResponseStatus(d.pop("status"))

        amount_usd = d.pop("amount_usd")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        def _parse_failure_message(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        failure_message = _parse_failure_message(d.pop("failure_message", UNSET))

        auto_topup_charge_response = cls(
            status=status,
            amount_usd=amount_usd,
            created_at=created_at,
            failure_message=failure_message,
        )

        auto_topup_charge_response.additional_properties = d
        return auto_topup_charge_response

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

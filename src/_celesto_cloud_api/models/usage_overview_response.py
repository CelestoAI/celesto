from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.usage_overview_response_state import UsageOverviewResponseState
from ..types import UNSET, Unset
from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.usage_by_size_response import UsageBySizeResponse


T = TypeVar("T", bound="UsageOverviewResponse")


@_attrs_define
class UsageOverviewResponse:
    """Organization-scoped usage state for the size-priced billing experience.

    Attributes:
        available (bool):
        state (UsageOverviewResponseState):
        trial_credit_remaining_usd (None | str):
        trial_expires_at (datetime.datetime | None):
        running_count (int):
        running_limit (int):
        retained_count (int):
        month_started_at (datetime.datetime):
        month_to_date_estimated_cost_usd (str):
        usage_by_size (list[UsageBySizeResponse]):
        prepaid_credit_remaining_usd (None | str | Unset):
        promotional_credit_remaining_usd (None | str | Unset):
        promotional_credit_expires_at (datetime.datetime | None | Unset):
        micro_small_promotional_credit_remaining_usd (None | str | Unset):
        micro_small_promotional_credit_expires_at (datetime.datetime | None | Unset):
        up_to_standard_promotional_credit_remaining_usd (None | str | Unset):
        up_to_standard_promotional_credit_expires_at (datetime.datetime | None | Unset):
    """

    available: bool
    state: UsageOverviewResponseState
    trial_credit_remaining_usd: None | str
    trial_expires_at: datetime.datetime | None
    running_count: int
    running_limit: int
    retained_count: int
    month_started_at: datetime.datetime
    month_to_date_estimated_cost_usd: str
    usage_by_size: list[UsageBySizeResponse]
    prepaid_credit_remaining_usd: None | str | Unset = UNSET
    promotional_credit_remaining_usd: None | str | Unset = UNSET
    promotional_credit_expires_at: datetime.datetime | None | Unset = UNSET
    micro_small_promotional_credit_remaining_usd: None | str | Unset = UNSET
    micro_small_promotional_credit_expires_at: datetime.datetime | None | Unset = UNSET
    up_to_standard_promotional_credit_remaining_usd: None | str | Unset = UNSET
    up_to_standard_promotional_credit_expires_at: datetime.datetime | None | Unset = (
        UNSET
    )
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.usage_by_size_response import UsageBySizeResponse  # noqa: PLC0415

        available = self.available

        state = self.state.value

        trial_credit_remaining_usd: None | str
        trial_credit_remaining_usd = self.trial_credit_remaining_usd

        trial_expires_at: None | str
        if isinstance(self.trial_expires_at, datetime.datetime):
            trial_expires_at = self.trial_expires_at.isoformat()
        else:
            trial_expires_at = self.trial_expires_at

        running_count = self.running_count

        running_limit = self.running_limit

        retained_count = self.retained_count

        month_started_at = self.month_started_at.isoformat()

        month_to_date_estimated_cost_usd = self.month_to_date_estimated_cost_usd

        usage_by_size = []
        for usage_by_size_item_data in self.usage_by_size:
            usage_by_size_item = usage_by_size_item_data.to_dict()
            usage_by_size.append(usage_by_size_item)

        prepaid_credit_remaining_usd: None | str | Unset
        if isinstance(self.prepaid_credit_remaining_usd, Unset):
            prepaid_credit_remaining_usd = UNSET
        else:
            prepaid_credit_remaining_usd = self.prepaid_credit_remaining_usd

        promotional_credit_remaining_usd: None | str | Unset
        if isinstance(self.promotional_credit_remaining_usd, Unset):
            promotional_credit_remaining_usd = UNSET
        else:
            promotional_credit_remaining_usd = self.promotional_credit_remaining_usd

        promotional_credit_expires_at: None | str | Unset
        if isinstance(self.promotional_credit_expires_at, Unset):
            promotional_credit_expires_at = UNSET
        elif isinstance(self.promotional_credit_expires_at, datetime.datetime):
            promotional_credit_expires_at = (
                self.promotional_credit_expires_at.isoformat()
            )
        else:
            promotional_credit_expires_at = self.promotional_credit_expires_at

        micro_small_promotional_credit_remaining_usd: None | str | Unset
        if isinstance(self.micro_small_promotional_credit_remaining_usd, Unset):
            micro_small_promotional_credit_remaining_usd = UNSET
        else:
            micro_small_promotional_credit_remaining_usd = (
                self.micro_small_promotional_credit_remaining_usd
            )

        micro_small_promotional_credit_expires_at: None | str | Unset
        if isinstance(self.micro_small_promotional_credit_expires_at, Unset):
            micro_small_promotional_credit_expires_at = UNSET
        elif isinstance(
            self.micro_small_promotional_credit_expires_at, datetime.datetime
        ):
            micro_small_promotional_credit_expires_at = (
                self.micro_small_promotional_credit_expires_at.isoformat()
            )
        else:
            micro_small_promotional_credit_expires_at = (
                self.micro_small_promotional_credit_expires_at
            )

        up_to_standard_promotional_credit_remaining_usd: None | str | Unset
        if isinstance(self.up_to_standard_promotional_credit_remaining_usd, Unset):
            up_to_standard_promotional_credit_remaining_usd = UNSET
        else:
            up_to_standard_promotional_credit_remaining_usd = (
                self.up_to_standard_promotional_credit_remaining_usd
            )

        up_to_standard_promotional_credit_expires_at: None | str | Unset
        if isinstance(self.up_to_standard_promotional_credit_expires_at, Unset):
            up_to_standard_promotional_credit_expires_at = UNSET
        elif isinstance(
            self.up_to_standard_promotional_credit_expires_at, datetime.datetime
        ):
            up_to_standard_promotional_credit_expires_at = (
                self.up_to_standard_promotional_credit_expires_at.isoformat()
            )
        else:
            up_to_standard_promotional_credit_expires_at = (
                self.up_to_standard_promotional_credit_expires_at
            )

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "available": available,
                "state": state,
                "trial_credit_remaining_usd": trial_credit_remaining_usd,
                "trial_expires_at": trial_expires_at,
                "running_count": running_count,
                "running_limit": running_limit,
                "retained_count": retained_count,
                "month_started_at": month_started_at,
                "month_to_date_estimated_cost_usd": month_to_date_estimated_cost_usd,
                "usage_by_size": usage_by_size,
            }
        )
        if prepaid_credit_remaining_usd is not UNSET:
            field_dict["prepaid_credit_remaining_usd"] = prepaid_credit_remaining_usd
        if promotional_credit_remaining_usd is not UNSET:
            field_dict["promotional_credit_remaining_usd"] = (
                promotional_credit_remaining_usd
            )
        if promotional_credit_expires_at is not UNSET:
            field_dict["promotional_credit_expires_at"] = promotional_credit_expires_at
        if micro_small_promotional_credit_remaining_usd is not UNSET:
            field_dict["micro_small_promotional_credit_remaining_usd"] = (
                micro_small_promotional_credit_remaining_usd
            )
        if micro_small_promotional_credit_expires_at is not UNSET:
            field_dict["micro_small_promotional_credit_expires_at"] = (
                micro_small_promotional_credit_expires_at
            )
        if up_to_standard_promotional_credit_remaining_usd is not UNSET:
            field_dict["up_to_standard_promotional_credit_remaining_usd"] = (
                up_to_standard_promotional_credit_remaining_usd
            )
        if up_to_standard_promotional_credit_expires_at is not UNSET:
            field_dict["up_to_standard_promotional_credit_expires_at"] = (
                up_to_standard_promotional_credit_expires_at
            )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.usage_by_size_response import UsageBySizeResponse  # noqa: PLC0415

        d = dict(src_dict)
        available = d.pop("available")

        state = UsageOverviewResponseState(d.pop("state"))

        def _parse_trial_credit_remaining_usd(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        trial_credit_remaining_usd = _parse_trial_credit_remaining_usd(
            d.pop("trial_credit_remaining_usd")
        )

        def _parse_trial_expires_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                trial_expires_at_type_0 = datetime.datetime.fromisoformat(data)

                return trial_expires_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None, data)

        trial_expires_at = _parse_trial_expires_at(d.pop("trial_expires_at"))

        running_count = d.pop("running_count")

        running_limit = d.pop("running_limit")

        retained_count = d.pop("retained_count")

        month_started_at = datetime.datetime.fromisoformat(d.pop("month_started_at"))

        month_to_date_estimated_cost_usd = d.pop("month_to_date_estimated_cost_usd")

        usage_by_size = []
        _usage_by_size = d.pop("usage_by_size")
        for usage_by_size_item_data in _usage_by_size:
            usage_by_size_item = UsageBySizeResponse.from_dict(usage_by_size_item_data)

            usage_by_size.append(usage_by_size_item)

        def _parse_prepaid_credit_remaining_usd(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        prepaid_credit_remaining_usd = _parse_prepaid_credit_remaining_usd(
            d.pop("prepaid_credit_remaining_usd", UNSET)
        )

        def _parse_promotional_credit_remaining_usd(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        promotional_credit_remaining_usd = _parse_promotional_credit_remaining_usd(
            d.pop("promotional_credit_remaining_usd", UNSET)
        )

        def _parse_promotional_credit_expires_at(
            data: object,
        ) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                promotional_credit_expires_at_type_0 = datetime.datetime.fromisoformat(
                    data
                )

                return promotional_credit_expires_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        promotional_credit_expires_at = _parse_promotional_credit_expires_at(
            d.pop("promotional_credit_expires_at", UNSET)
        )

        def _parse_micro_small_promotional_credit_remaining_usd(
            data: object,
        ) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        micro_small_promotional_credit_remaining_usd = (
            _parse_micro_small_promotional_credit_remaining_usd(
                d.pop("micro_small_promotional_credit_remaining_usd", UNSET)
            )
        )

        def _parse_micro_small_promotional_credit_expires_at(
            data: object,
        ) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                micro_small_promotional_credit_expires_at_type_0 = (
                    datetime.datetime.fromisoformat(data)
                )

                return micro_small_promotional_credit_expires_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        micro_small_promotional_credit_expires_at = (
            _parse_micro_small_promotional_credit_expires_at(
                d.pop("micro_small_promotional_credit_expires_at", UNSET)
            )
        )

        def _parse_up_to_standard_promotional_credit_remaining_usd(
            data: object,
        ) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        up_to_standard_promotional_credit_remaining_usd = (
            _parse_up_to_standard_promotional_credit_remaining_usd(
                d.pop("up_to_standard_promotional_credit_remaining_usd", UNSET)
            )
        )

        def _parse_up_to_standard_promotional_credit_expires_at(
            data: object,
        ) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                up_to_standard_promotional_credit_expires_at_type_0 = (
                    datetime.datetime.fromisoformat(data)
                )

                return up_to_standard_promotional_credit_expires_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        up_to_standard_promotional_credit_expires_at = (
            _parse_up_to_standard_promotional_credit_expires_at(
                d.pop("up_to_standard_promotional_credit_expires_at", UNSET)
            )
        )

        usage_overview_response = cls(
            available=available,
            state=state,
            trial_credit_remaining_usd=trial_credit_remaining_usd,
            trial_expires_at=trial_expires_at,
            running_count=running_count,
            running_limit=running_limit,
            retained_count=retained_count,
            month_started_at=month_started_at,
            month_to_date_estimated_cost_usd=month_to_date_estimated_cost_usd,
            usage_by_size=usage_by_size,
            prepaid_credit_remaining_usd=prepaid_credit_remaining_usd,
            promotional_credit_remaining_usd=promotional_credit_remaining_usd,
            promotional_credit_expires_at=promotional_credit_expires_at,
            micro_small_promotional_credit_remaining_usd=micro_small_promotional_credit_remaining_usd,
            micro_small_promotional_credit_expires_at=micro_small_promotional_credit_expires_at,
            up_to_standard_promotional_credit_remaining_usd=up_to_standard_promotional_credit_remaining_usd,
            up_to_standard_promotional_credit_expires_at=up_to_standard_promotional_credit_expires_at,
        )

        usage_overview_response.additional_properties = d
        return usage_overview_response

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.end_user_update_request_metadata_type_0 import (
        EndUserUpdateRequestMetadataType0,
    )


T = TypeVar("T", bound="EndUserUpdateRequest")


@_attrs_define
class EndUserUpdateRequest:
    """PUT semantics with field-presence: ``budget_cap_usd: null`` clears the
    override, omitting it leaves it alone (checked via model_fields_set).

        Attributes:
            budget_cap_usd (None | str | Unset):
            metadata (EndUserUpdateRequestMetadataType0 | None | Unset):
    """

    budget_cap_usd: None | str | Unset = UNSET
    metadata: EndUserUpdateRequestMetadataType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.end_user_update_request_metadata_type_0 import (
            EndUserUpdateRequestMetadataType0,
        )  # noqa: PLC0415

        budget_cap_usd: None | str | Unset
        if isinstance(self.budget_cap_usd, Unset):
            budget_cap_usd = UNSET
        else:
            budget_cap_usd = self.budget_cap_usd

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, EndUserUpdateRequestMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if budget_cap_usd is not UNSET:
            field_dict["budget_cap_usd"] = budget_cap_usd
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.end_user_update_request_metadata_type_0 import (
            EndUserUpdateRequestMetadataType0,
        )  # noqa: PLC0415

        d = dict(src_dict)

        def _parse_budget_cap_usd(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        budget_cap_usd = _parse_budget_cap_usd(d.pop("budget_cap_usd", UNSET))

        def _parse_metadata(
            data: object,
        ) -> EndUserUpdateRequestMetadataType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = EndUserUpdateRequestMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(EndUserUpdateRequestMetadataType0 | None | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        end_user_update_request = cls(
            budget_cap_usd=budget_cap_usd,
            metadata=metadata,
        )

        end_user_update_request.additional_properties = d
        return end_user_update_request

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

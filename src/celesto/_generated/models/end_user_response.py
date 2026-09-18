from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.end_user_budget import EndUserBudget
    from ..models.end_user_response_metadata_type_0 import EndUserResponseMetadataType0


T = TypeVar("T", bound="EndUserResponse")


@_attrs_define
class EndUserResponse:
    """
    Attributes:
        end_user_id (str):
        first_activity_at (datetime.datetime):
        budget (EndUserBudget):
        created_at (datetime.datetime):
        object_ (str | Unset):  Default: 'end_user'.
        metadata (EndUserResponseMetadataType0 | None | Unset):
    """

    end_user_id: str
    first_activity_at: datetime.datetime
    budget: EndUserBudget
    created_at: datetime.datetime
    object_: str | Unset = "end_user"
    metadata: EndUserResponseMetadataType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.end_user_budget import EndUserBudget  # noqa: PLC0415
        from ..models.end_user_response_metadata_type_0 import (
            EndUserResponseMetadataType0,
        )  # noqa: PLC0415

        end_user_id = self.end_user_id

        first_activity_at = self.first_activity_at.isoformat()

        budget = self.budget.to_dict()

        created_at = self.created_at.isoformat()

        object_ = self.object_

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, EndUserResponseMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "end_user_id": end_user_id,
                "first_activity_at": first_activity_at,
                "budget": budget,
                "created_at": created_at,
            }
        )
        if object_ is not UNSET:
            field_dict["object"] = object_
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.end_user_budget import EndUserBudget  # noqa: PLC0415
        from ..models.end_user_response_metadata_type_0 import (
            EndUserResponseMetadataType0,
        )  # noqa: PLC0415

        d = dict(src_dict)
        end_user_id = d.pop("end_user_id")

        first_activity_at = datetime.datetime.fromisoformat(d.pop("first_activity_at"))

        budget = EndUserBudget.from_dict(d.pop("budget"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        object_ = d.pop("object", UNSET)

        def _parse_metadata(
            data: object,
        ) -> EndUserResponseMetadataType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = EndUserResponseMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(EndUserResponseMetadataType0 | None | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        end_user_response = cls(
            end_user_id=end_user_id,
            first_activity_at=first_activity_at,
            budget=budget,
            created_at=created_at,
            object_=object_,
            metadata=metadata,
        )

        end_user_response.additional_properties = d
        return end_user_response

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
import datetime


T = TypeVar("T", bound="TraceShareInfo")


@_attrs_define
class TraceShareInfo:
    """Basic metadata for a shared trace (public view).

    Attributes:
        created_at (datetime.datetime):
        expires_at (datetime.datetime):
        workflow_name (None | str | Unset):
    """

    created_at: datetime.datetime
    expires_at: datetime.datetime
    workflow_name: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        created_at = self.created_at.isoformat()

        expires_at = self.expires_at.isoformat()

        workflow_name: None | str | Unset
        if isinstance(self.workflow_name, Unset):
            workflow_name = UNSET
        else:
            workflow_name = self.workflow_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "created_at": created_at,
                "expires_at": expires_at,
            }
        )
        if workflow_name is not UNSET:
            field_dict["workflow_name"] = workflow_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        expires_at = datetime.datetime.fromisoformat(d.pop("expires_at"))

        def _parse_workflow_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        workflow_name = _parse_workflow_name(d.pop("workflow_name", UNSET))

        trace_share_info = cls(
            created_at=created_at,
            expires_at=expires_at,
            workflow_name=workflow_name,
        )

        trace_share_info.additional_properties = d
        return trace_share_info

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

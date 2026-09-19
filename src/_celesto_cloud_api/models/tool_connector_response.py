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
    from ..models.tool_connector_response_metadata_type_0 import (
        ToolConnectorResponseMetadataType0,
    )


T = TypeVar("T", bound="ToolConnectorResponse")


@_attrs_define
class ToolConnectorResponse:
    """
    Attributes:
        id (str):
        tool_id (str):
        tool_key (str):
        tool_name (str):
        auth_type (str):
        status (str):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        metadata (None | ToolConnectorResponseMetadataType0 | Unset):
    """

    id: str
    tool_id: str
    tool_key: str
    tool_name: str
    auth_type: str
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    metadata: None | ToolConnectorResponseMetadataType0 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.tool_connector_response_metadata_type_0 import (
            ToolConnectorResponseMetadataType0,
        )  # noqa: PLC0415

        id = self.id

        tool_id = self.tool_id

        tool_key = self.tool_key

        tool_name = self.tool_name

        auth_type = self.auth_type

        status = self.status

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, ToolConnectorResponseMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "tool_id": tool_id,
                "tool_key": tool_key,
                "tool_name": tool_name,
                "auth_type": auth_type,
                "status": status,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.tool_connector_response_metadata_type_0 import (
            ToolConnectorResponseMetadataType0,
        )  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        tool_id = d.pop("tool_id")

        tool_key = d.pop("tool_key")

        tool_name = d.pop("tool_name")

        auth_type = d.pop("auth_type")

        status = d.pop("status")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        def _parse_metadata(
            data: object,
        ) -> None | ToolConnectorResponseMetadataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = ToolConnectorResponseMetadataType0.from_dict(data)

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ToolConnectorResponseMetadataType0 | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        tool_connector_response = cls(
            id=id,
            tool_id=tool_id,
            tool_key=tool_key,
            tool_name=tool_name,
            auth_type=auth_type,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            metadata=metadata,
        )

        tool_connector_response.additional_properties = d
        return tool_connector_response

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

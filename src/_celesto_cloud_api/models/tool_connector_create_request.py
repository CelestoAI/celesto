from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.tool_connector_create_request_metadata_type_0 import (
        ToolConnectorCreateRequestMetadataType0,
    )


T = TypeVar("T", bound="ToolConnectorCreateRequest")


@_attrs_define
class ToolConnectorCreateRequest:
    """
    Attributes:
        tool_key (str):
        api_key (str):
        metadata (None | ToolConnectorCreateRequestMetadataType0 | Unset):
        project_id (None | str | Unset):
    """

    tool_key: str
    api_key: str
    metadata: None | ToolConnectorCreateRequestMetadataType0 | Unset = UNSET
    project_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.tool_connector_create_request_metadata_type_0 import (
            ToolConnectorCreateRequestMetadataType0,
        )  # noqa: PLC0415

        tool_key = self.tool_key

        api_key = self.api_key

        metadata: dict[str, Any] | None | Unset
        if isinstance(self.metadata, Unset):
            metadata = UNSET
        elif isinstance(self.metadata, ToolConnectorCreateRequestMetadataType0):
            metadata = self.metadata.to_dict()
        else:
            metadata = self.metadata

        project_id: None | str | Unset
        if isinstance(self.project_id, Unset):
            project_id = UNSET
        else:
            project_id = self.project_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tool_key": tool_key,
                "api_key": api_key,
            }
        )
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if project_id is not UNSET:
            field_dict["project_id"] = project_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.tool_connector_create_request_metadata_type_0 import (
            ToolConnectorCreateRequestMetadataType0,
        )  # noqa: PLC0415

        d = dict(src_dict)
        tool_key = d.pop("tool_key")

        api_key = d.pop("api_key")

        def _parse_metadata(
            data: object,
        ) -> None | ToolConnectorCreateRequestMetadataType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                metadata_type_0 = ToolConnectorCreateRequestMetadataType0.from_dict(
                    data
                )

                return metadata_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ToolConnectorCreateRequestMetadataType0 | Unset, data)

        metadata = _parse_metadata(d.pop("metadata", UNSET))

        def _parse_project_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        project_id = _parse_project_id(d.pop("project_id", UNSET))

        tool_connector_create_request = cls(
            tool_key=tool_key,
            api_key=api_key,
            metadata=metadata,
            project_id=project_id,
        )

        tool_connector_create_request.additional_properties = d
        return tool_connector_create_request

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

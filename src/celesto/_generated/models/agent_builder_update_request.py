from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.agent_builder_update_request_config_data_type_0 import (
        AgentBuilderUpdateRequestConfigDataType0,
    )


T = TypeVar("T", bound="AgentBuilderUpdateRequest")


@_attrs_define
class AgentBuilderUpdateRequest:
    """Request schema for updating an existing agent config.

    Only name and config_data can be updated. Description is set at creation
    time and cannot be modified afterwards (by design - descriptions serve as
    immutable documentation of the config's original purpose).

        Attributes:
            name (None | str | Unset): New name for the config
            config_data (AgentBuilderUpdateRequestConfigDataType0 | None | Unset): New config data (replaces existing)
    """

    name: None | str | Unset = UNSET
    config_data: AgentBuilderUpdateRequestConfigDataType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.agent_builder_update_request_config_data_type_0 import (
            AgentBuilderUpdateRequestConfigDataType0,
        )  # noqa: PLC0415

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        config_data: dict[str, Any] | None | Unset
        if isinstance(self.config_data, Unset):
            config_data = UNSET
        elif isinstance(self.config_data, AgentBuilderUpdateRequestConfigDataType0):
            config_data = self.config_data.to_dict()
        else:
            config_data = self.config_data

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if config_data is not UNSET:
            field_dict["config_data"] = config_data

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.agent_builder_update_request_config_data_type_0 import (
            AgentBuilderUpdateRequestConfigDataType0,
        )  # noqa: PLC0415

        d = dict(src_dict)

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_config_data(
            data: object,
        ) -> AgentBuilderUpdateRequestConfigDataType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                config_data_type_0 = AgentBuilderUpdateRequestConfigDataType0.from_dict(
                    data
                )

                return config_data_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AgentBuilderUpdateRequestConfigDataType0 | None | Unset, data)

        config_data = _parse_config_data(d.pop("config_data", UNSET))

        agent_builder_update_request = cls(
            name=name,
            config_data=config_data,
        )

        agent_builder_update_request.additional_properties = d
        return agent_builder_update_request

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

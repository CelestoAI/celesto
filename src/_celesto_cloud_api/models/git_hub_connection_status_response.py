from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.git_hub_connection_response import GitHubConnectionResponse


T = TypeVar("T", bound="GitHubConnectionStatusResponse")


@_attrs_define
class GitHubConnectionStatusResponse:
    """
    Attributes:
        connected (bool):
        connection (GitHubConnectionResponse | None | Unset):
        required_scopes (list[str] | Unset):
        missing_scopes (list[str] | Unset):
    """

    connected: bool
    connection: GitHubConnectionResponse | None | Unset = UNSET
    required_scopes: list[str] | Unset = UNSET
    missing_scopes: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.git_hub_connection_response import GitHubConnectionResponse  # noqa: PLC0415

        connected = self.connected

        connection: dict[str, Any] | None | Unset
        if isinstance(self.connection, Unset):
            connection = UNSET
        elif isinstance(self.connection, GitHubConnectionResponse):
            connection = self.connection.to_dict()
        else:
            connection = self.connection

        required_scopes: list[str] | Unset = UNSET
        if not isinstance(self.required_scopes, Unset):
            required_scopes = self.required_scopes

        missing_scopes: list[str] | Unset = UNSET
        if not isinstance(self.missing_scopes, Unset):
            missing_scopes = self.missing_scopes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "connected": connected,
            }
        )
        if connection is not UNSET:
            field_dict["connection"] = connection
        if required_scopes is not UNSET:
            field_dict["required_scopes"] = required_scopes
        if missing_scopes is not UNSET:
            field_dict["missing_scopes"] = missing_scopes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.git_hub_connection_response import GitHubConnectionResponse  # noqa: PLC0415

        d = dict(src_dict)
        connected = d.pop("connected")

        def _parse_connection(data: object) -> GitHubConnectionResponse | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                connection_type_0 = GitHubConnectionResponse.from_dict(data)

                return connection_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(GitHubConnectionResponse | None | Unset, data)

        connection = _parse_connection(d.pop("connection", UNSET))

        required_scopes = cast(list[str], d.pop("required_scopes", UNSET))

        missing_scopes = cast(list[str], d.pop("missing_scopes", UNSET))

        git_hub_connection_status_response = cls(
            connected=connected,
            connection=connection,
            required_scopes=required_scopes,
            missing_scopes=missing_scopes,
        )

        git_hub_connection_status_response.additional_properties = d
        return git_hub_connection_status_response

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

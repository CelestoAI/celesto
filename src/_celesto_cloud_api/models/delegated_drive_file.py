from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="DelegatedDriveFile")


@_attrs_define
class DelegatedDriveFile:
    """Represents a Google Drive file metadata snapshot.

    Attributes:
        id (str):
        name (None | str | Unset):
        mime_type (None | str | Unset):
        size (int | None | Unset):
        modified_time (None | str | Unset):
        created_time (None | str | Unset):
        web_view_link (None | str | Unset):
        icon_link (None | str | Unset):
        thumbnail_link (None | str | Unset):
        parents (list[str] | None | Unset):
        drive_id (None | str | Unset):
        shared (bool | None | Unset):
        owned_by_me (bool | None | Unset):
    """

    id: str
    name: None | str | Unset = UNSET
    mime_type: None | str | Unset = UNSET
    size: int | None | Unset = UNSET
    modified_time: None | str | Unset = UNSET
    created_time: None | str | Unset = UNSET
    web_view_link: None | str | Unset = UNSET
    icon_link: None | str | Unset = UNSET
    thumbnail_link: None | str | Unset = UNSET
    parents: list[str] | None | Unset = UNSET
    drive_id: None | str | Unset = UNSET
    shared: bool | None | Unset = UNSET
    owned_by_me: bool | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        mime_type: None | str | Unset
        if isinstance(self.mime_type, Unset):
            mime_type = UNSET
        else:
            mime_type = self.mime_type

        size: int | None | Unset
        if isinstance(self.size, Unset):
            size = UNSET
        else:
            size = self.size

        modified_time: None | str | Unset
        if isinstance(self.modified_time, Unset):
            modified_time = UNSET
        else:
            modified_time = self.modified_time

        created_time: None | str | Unset
        if isinstance(self.created_time, Unset):
            created_time = UNSET
        else:
            created_time = self.created_time

        web_view_link: None | str | Unset
        if isinstance(self.web_view_link, Unset):
            web_view_link = UNSET
        else:
            web_view_link = self.web_view_link

        icon_link: None | str | Unset
        if isinstance(self.icon_link, Unset):
            icon_link = UNSET
        else:
            icon_link = self.icon_link

        thumbnail_link: None | str | Unset
        if isinstance(self.thumbnail_link, Unset):
            thumbnail_link = UNSET
        else:
            thumbnail_link = self.thumbnail_link

        parents: list[str] | None | Unset
        if isinstance(self.parents, Unset):
            parents = UNSET
        elif isinstance(self.parents, list):
            parents = self.parents

        else:
            parents = self.parents

        drive_id: None | str | Unset
        if isinstance(self.drive_id, Unset):
            drive_id = UNSET
        else:
            drive_id = self.drive_id

        shared: bool | None | Unset
        if isinstance(self.shared, Unset):
            shared = UNSET
        else:
            shared = self.shared

        owned_by_me: bool | None | Unset
        if isinstance(self.owned_by_me, Unset):
            owned_by_me = UNSET
        else:
            owned_by_me = self.owned_by_me

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if mime_type is not UNSET:
            field_dict["mime_type"] = mime_type
        if size is not UNSET:
            field_dict["size"] = size
        if modified_time is not UNSET:
            field_dict["modified_time"] = modified_time
        if created_time is not UNSET:
            field_dict["created_time"] = created_time
        if web_view_link is not UNSET:
            field_dict["web_view_link"] = web_view_link
        if icon_link is not UNSET:
            field_dict["icon_link"] = icon_link
        if thumbnail_link is not UNSET:
            field_dict["thumbnail_link"] = thumbnail_link
        if parents is not UNSET:
            field_dict["parents"] = parents
        if drive_id is not UNSET:
            field_dict["drive_id"] = drive_id
        if shared is not UNSET:
            field_dict["shared"] = shared
        if owned_by_me is not UNSET:
            field_dict["owned_by_me"] = owned_by_me

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        def _parse_mime_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        mime_type = _parse_mime_type(d.pop("mime_type", UNSET))

        def _parse_size(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        size = _parse_size(d.pop("size", UNSET))

        def _parse_modified_time(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        modified_time = _parse_modified_time(d.pop("modified_time", UNSET))

        def _parse_created_time(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        created_time = _parse_created_time(d.pop("created_time", UNSET))

        def _parse_web_view_link(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        web_view_link = _parse_web_view_link(d.pop("web_view_link", UNSET))

        def _parse_icon_link(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        icon_link = _parse_icon_link(d.pop("icon_link", UNSET))

        def _parse_thumbnail_link(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        thumbnail_link = _parse_thumbnail_link(d.pop("thumbnail_link", UNSET))

        def _parse_parents(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                parents_type_0 = cast(list[str], data)

                return parents_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        parents = _parse_parents(d.pop("parents", UNSET))

        def _parse_drive_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        drive_id = _parse_drive_id(d.pop("drive_id", UNSET))

        def _parse_shared(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        shared = _parse_shared(d.pop("shared", UNSET))

        def _parse_owned_by_me(data: object) -> bool | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(bool | None | Unset, data)

        owned_by_me = _parse_owned_by_me(d.pop("owned_by_me", UNSET))

        delegated_drive_file = cls(
            id=id,
            name=name,
            mime_type=mime_type,
            size=size,
            modified_time=modified_time,
            created_time=created_time,
            web_view_link=web_view_link,
            icon_link=icon_link,
            thumbnail_link=thumbnail_link,
            parents=parents,
            drive_id=drive_id,
            shared=shared,
            owned_by_me=owned_by_me,
        )

        delegated_drive_file.additional_properties = d
        return delegated_drive_file

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

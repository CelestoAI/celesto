from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
from uuid import UUID

if TYPE_CHECKING:
    from ..models.user_public_extra_info_type_0 import UserPublicExtraInfoType0


T = TypeVar("T", bound="UserPublic")


@_attrs_define
class UserPublic:
    """
    Attributes:
        id (UUID):
        first_name (str):
        email (str):
        access_suspended (bool):
        onboarding_completed (bool):
        last_name (None | str | Unset):
        phone (None | str | Unset):
        country (None | str | Unset):
        address (None | str | Unset):
        occupation (None | str | Unset):
        user_type (None | str | Unset):
        extra_info (None | Unset | UserPublicExtraInfoType0):
    """

    id: UUID
    first_name: str
    email: str
    access_suspended: bool
    onboarding_completed: bool
    last_name: None | str | Unset = UNSET
    phone: None | str | Unset = UNSET
    country: None | str | Unset = UNSET
    address: None | str | Unset = UNSET
    occupation: None | str | Unset = UNSET
    user_type: None | str | Unset = UNSET
    extra_info: None | Unset | UserPublicExtraInfoType0 = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.user_public_extra_info_type_0 import UserPublicExtraInfoType0  # noqa: PLC0415

        id = str(self.id)

        first_name = self.first_name

        email = self.email

        access_suspended = self.access_suspended

        onboarding_completed = self.onboarding_completed

        last_name: None | str | Unset
        if isinstance(self.last_name, Unset):
            last_name = UNSET
        else:
            last_name = self.last_name

        phone: None | str | Unset
        if isinstance(self.phone, Unset):
            phone = UNSET
        else:
            phone = self.phone

        country: None | str | Unset
        if isinstance(self.country, Unset):
            country = UNSET
        else:
            country = self.country

        address: None | str | Unset
        if isinstance(self.address, Unset):
            address = UNSET
        else:
            address = self.address

        occupation: None | str | Unset
        if isinstance(self.occupation, Unset):
            occupation = UNSET
        else:
            occupation = self.occupation

        user_type: None | str | Unset
        if isinstance(self.user_type, Unset):
            user_type = UNSET
        else:
            user_type = self.user_type

        extra_info: dict[str, Any] | None | Unset
        if isinstance(self.extra_info, Unset):
            extra_info = UNSET
        elif isinstance(self.extra_info, UserPublicExtraInfoType0):
            extra_info = self.extra_info.to_dict()
        else:
            extra_info = self.extra_info

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "first_name": first_name,
                "email": email,
                "access_suspended": access_suspended,
                "onboarding_completed": onboarding_completed,
            }
        )
        if last_name is not UNSET:
            field_dict["last_name"] = last_name
        if phone is not UNSET:
            field_dict["phone"] = phone
        if country is not UNSET:
            field_dict["country"] = country
        if address is not UNSET:
            field_dict["address"] = address
        if occupation is not UNSET:
            field_dict["occupation"] = occupation
        if user_type is not UNSET:
            field_dict["user_type"] = user_type
        if extra_info is not UNSET:
            field_dict["extra_info"] = extra_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.user_public_extra_info_type_0 import UserPublicExtraInfoType0  # noqa: PLC0415

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        first_name = d.pop("first_name")

        email = d.pop("email")

        access_suspended = d.pop("access_suspended")

        onboarding_completed = d.pop("onboarding_completed")

        def _parse_last_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        last_name = _parse_last_name(d.pop("last_name", UNSET))

        def _parse_phone(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        phone = _parse_phone(d.pop("phone", UNSET))

        def _parse_country(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        country = _parse_country(d.pop("country", UNSET))

        def _parse_address(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        address = _parse_address(d.pop("address", UNSET))

        def _parse_occupation(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        occupation = _parse_occupation(d.pop("occupation", UNSET))

        def _parse_user_type(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        user_type = _parse_user_type(d.pop("user_type", UNSET))

        def _parse_extra_info(data: object) -> None | Unset | UserPublicExtraInfoType0:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                extra_info_type_0 = UserPublicExtraInfoType0.from_dict(data)

                return extra_info_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | Unset | UserPublicExtraInfoType0, data)

        extra_info = _parse_extra_info(d.pop("extra_info", UNSET))

        user_public = cls(
            id=id,
            first_name=first_name,
            email=email,
            access_suspended=access_suspended,
            onboarding_completed=onboarding_completed,
            last_name=last_name,
            phone=phone,
            country=country,
            address=address,
            occupation=occupation,
            user_type=user_type,
            extra_info=extra_info,
        )

        user_public.additional_properties = d
        return user_public

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

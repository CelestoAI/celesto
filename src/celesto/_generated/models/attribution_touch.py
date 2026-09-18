from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="AttributionTouch")


@_attrs_define
class AttributionTouch:
    """
    Attributes:
        utm_source (None | str | Unset):
        utm_medium (None | str | Unset):
        utm_campaign (None | str | Unset):
        utm_term (None | str | Unset):
        utm_content (None | str | Unset):
        landing_path (None | str | Unset):
        referring_domain (None | str | Unset):
    """

    utm_source: None | str | Unset = UNSET
    utm_medium: None | str | Unset = UNSET
    utm_campaign: None | str | Unset = UNSET
    utm_term: None | str | Unset = UNSET
    utm_content: None | str | Unset = UNSET
    landing_path: None | str | Unset = UNSET
    referring_domain: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        utm_source: None | str | Unset
        if isinstance(self.utm_source, Unset):
            utm_source = UNSET
        else:
            utm_source = self.utm_source

        utm_medium: None | str | Unset
        if isinstance(self.utm_medium, Unset):
            utm_medium = UNSET
        else:
            utm_medium = self.utm_medium

        utm_campaign: None | str | Unset
        if isinstance(self.utm_campaign, Unset):
            utm_campaign = UNSET
        else:
            utm_campaign = self.utm_campaign

        utm_term: None | str | Unset
        if isinstance(self.utm_term, Unset):
            utm_term = UNSET
        else:
            utm_term = self.utm_term

        utm_content: None | str | Unset
        if isinstance(self.utm_content, Unset):
            utm_content = UNSET
        else:
            utm_content = self.utm_content

        landing_path: None | str | Unset
        if isinstance(self.landing_path, Unset):
            landing_path = UNSET
        else:
            landing_path = self.landing_path

        referring_domain: None | str | Unset
        if isinstance(self.referring_domain, Unset):
            referring_domain = UNSET
        else:
            referring_domain = self.referring_domain

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if utm_source is not UNSET:
            field_dict["utm_source"] = utm_source
        if utm_medium is not UNSET:
            field_dict["utm_medium"] = utm_medium
        if utm_campaign is not UNSET:
            field_dict["utm_campaign"] = utm_campaign
        if utm_term is not UNSET:
            field_dict["utm_term"] = utm_term
        if utm_content is not UNSET:
            field_dict["utm_content"] = utm_content
        if landing_path is not UNSET:
            field_dict["landing_path"] = landing_path
        if referring_domain is not UNSET:
            field_dict["referring_domain"] = referring_domain

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_utm_source(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        utm_source = _parse_utm_source(d.pop("utm_source", UNSET))

        def _parse_utm_medium(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        utm_medium = _parse_utm_medium(d.pop("utm_medium", UNSET))

        def _parse_utm_campaign(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        utm_campaign = _parse_utm_campaign(d.pop("utm_campaign", UNSET))

        def _parse_utm_term(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        utm_term = _parse_utm_term(d.pop("utm_term", UNSET))

        def _parse_utm_content(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        utm_content = _parse_utm_content(d.pop("utm_content", UNSET))

        def _parse_landing_path(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        landing_path = _parse_landing_path(d.pop("landing_path", UNSET))

        def _parse_referring_domain(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        referring_domain = _parse_referring_domain(d.pop("referring_domain", UNSET))

        attribution_touch = cls(
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
            utm_term=utm_term,
            utm_content=utm_content,
            landing_path=landing_path,
            referring_domain=referring_domain,
        )

        return attribution_touch

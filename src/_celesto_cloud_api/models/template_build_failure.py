from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="TemplateBuildFailure")


@_attrs_define
class TemplateBuildFailure:
    """Why the last build failed, when its script exited non-zero.

    ``line`` and ``line_number`` point into the build script; both are null
    when the failure came from a build step outside it (for example the base
    download). ``hint`` is set for known failures.

        Attributes:
            line (None | str | Unset):
            line_number (int | None | Unset):
            exit_code (int | None | Unset):
            hint (None | str | Unset):
    """

    line: None | str | Unset = UNSET
    line_number: int | None | Unset = UNSET
    exit_code: int | None | Unset = UNSET
    hint: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        line: None | str | Unset
        if isinstance(self.line, Unset):
            line = UNSET
        else:
            line = self.line

        line_number: int | None | Unset
        if isinstance(self.line_number, Unset):
            line_number = UNSET
        else:
            line_number = self.line_number

        exit_code: int | None | Unset
        if isinstance(self.exit_code, Unset):
            exit_code = UNSET
        else:
            exit_code = self.exit_code

        hint: None | str | Unset
        if isinstance(self.hint, Unset):
            hint = UNSET
        else:
            hint = self.hint

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if line is not UNSET:
            field_dict["line"] = line
        if line_number is not UNSET:
            field_dict["line_number"] = line_number
        if exit_code is not UNSET:
            field_dict["exit_code"] = exit_code
        if hint is not UNSET:
            field_dict["hint"] = hint

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_line(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        line = _parse_line(d.pop("line", UNSET))

        def _parse_line_number(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        line_number = _parse_line_number(d.pop("line_number", UNSET))

        def _parse_exit_code(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        exit_code = _parse_exit_code(d.pop("exit_code", UNSET))

        def _parse_hint(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        hint = _parse_hint(d.pop("hint", UNSET))

        template_build_failure = cls(
            line=line,
            line_number=line_number,
            exit_code=exit_code,
            hint=hint,
        )

        template_build_failure.additional_properties = d
        return template_build_failure

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

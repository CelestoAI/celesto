from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="RunCreateRequest")


@_attrs_define
class RunCreateRequest:
    """
    Attributes:
        input_ (str):
        end_user_id (str):
        session_id (None | str | Unset):
        stream (bool | Unset):  Default: False.
        max_turns (int | None | Unset):
    """

    input_: str
    end_user_id: str
    session_id: None | str | Unset = UNSET
    stream: bool | Unset = False
    max_turns: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        input_ = self.input_

        end_user_id = self.end_user_id

        session_id: None | str | Unset
        if isinstance(self.session_id, Unset):
            session_id = UNSET
        else:
            session_id = self.session_id

        stream = self.stream

        max_turns: int | None | Unset
        if isinstance(self.max_turns, Unset):
            max_turns = UNSET
        else:
            max_turns = self.max_turns

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "input": input_,
                "end_user_id": end_user_id,
            }
        )
        if session_id is not UNSET:
            field_dict["session_id"] = session_id
        if stream is not UNSET:
            field_dict["stream"] = stream
        if max_turns is not UNSET:
            field_dict["max_turns"] = max_turns

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        input_ = d.pop("input")

        end_user_id = d.pop("end_user_id")

        def _parse_session_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        session_id = _parse_session_id(d.pop("session_id", UNSET))

        stream = d.pop("stream", UNSET)

        def _parse_max_turns(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        max_turns = _parse_max_turns(d.pop("max_turns", UNSET))

        run_create_request = cls(
            input_=input_,
            end_user_id=end_user_id,
            session_id=session_id,
            stream=stream,
            max_turns=max_turns,
        )

        run_create_request.additional_properties = d
        return run_create_request

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

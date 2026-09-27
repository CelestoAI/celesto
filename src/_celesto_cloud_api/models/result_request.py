from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
    from ..models.result_request_result_type_0 import ResultRequestResultType0


T = TypeVar("T", bound="ResultRequest")


@_attrs_define
class ResultRequest:
    """
    Attributes:
        epoch (int):
        state_id (str):
        ok (bool):
        result (None | ResultRequestResultType0 | Unset):
        error (None | str | Unset):
    """

    epoch: int
    state_id: str
    ok: bool
    result: None | ResultRequestResultType0 | Unset = UNSET
    error: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.result_request_result_type_0 import ResultRequestResultType0  # noqa: PLC0415

        epoch = self.epoch

        state_id = self.state_id

        ok = self.ok

        result: dict[str, Any] | None | Unset
        if isinstance(self.result, Unset):
            result = UNSET
        elif isinstance(self.result, ResultRequestResultType0):
            result = self.result.to_dict()
        else:
            result = self.result

        error: None | str | Unset
        if isinstance(self.error, Unset):
            error = UNSET
        else:
            error = self.error

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "epoch": epoch,
                "state_id": state_id,
                "ok": ok,
            }
        )
        if result is not UNSET:
            field_dict["result"] = result
        if error is not UNSET:
            field_dict["error"] = error

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.result_request_result_type_0 import ResultRequestResultType0  # noqa: PLC0415

        d = dict(src_dict)
        epoch = d.pop("epoch")

        state_id = d.pop("state_id")

        ok = d.pop("ok")

        def _parse_result(data: object) -> None | ResultRequestResultType0 | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                result_type_0 = ResultRequestResultType0.from_dict(data)

                return result_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | ResultRequestResultType0 | Unset, data)

        result = _parse_result(d.pop("result", UNSET))

        def _parse_error(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error = _parse_error(d.pop("error", UNSET))

        result_request = cls(
            epoch=epoch,
            state_id=state_id,
            ok=ok,
            result=result,
            error=error,
        )

        result_request.additional_properties = d
        return result_request

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.pool_bootstrap_request_kind import PoolBootstrapRequestKind
from ..types import UNSET, Unset
from typing import cast


T = TypeVar("T", bound="PoolBootstrapRequest")


@_attrs_define
class PoolBootstrapRequest:
    """A host asks for a booted CI computer's runner start command, or reports its result (plan A).

    Attributes:
        epoch (int):
        state_id (str):
        kind (PoolBootstrapRequestKind | Unset):  Default: PoolBootstrapRequestKind.COMMAND.
        exit_code (int | None | Unset):
    """

    epoch: int
    state_id: str
    kind: PoolBootstrapRequestKind | Unset = PoolBootstrapRequestKind.COMMAND
    exit_code: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        epoch = self.epoch

        state_id = self.state_id

        kind: str | Unset = UNSET
        if not isinstance(self.kind, Unset):
            kind = self.kind.value

        exit_code: int | None | Unset
        if isinstance(self.exit_code, Unset):
            exit_code = UNSET
        else:
            exit_code = self.exit_code

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "epoch": epoch,
                "state_id": state_id,
            }
        )
        if kind is not UNSET:
            field_dict["kind"] = kind
        if exit_code is not UNSET:
            field_dict["exit_code"] = exit_code

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        epoch = d.pop("epoch")

        state_id = d.pop("state_id")

        _kind = d.pop("kind", UNSET)
        kind: PoolBootstrapRequestKind | Unset
        if isinstance(_kind, Unset):
            kind = UNSET
        else:
            kind = PoolBootstrapRequestKind(_kind)

        def _parse_exit_code(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        exit_code = _parse_exit_code(d.pop("exit_code", UNSET))

        pool_bootstrap_request = cls(
            epoch=epoch,
            state_id=state_id,
            kind=kind,
            exit_code=exit_code,
        )

        pool_bootstrap_request.additional_properties = d
        return pool_bootstrap_request

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

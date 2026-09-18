from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast
from typing import Literal, cast

if TYPE_CHECKING:
    from ..models.computer_validation_error_response_errors_item import (
        ComputerValidationErrorResponseErrorsItem,
    )


T = TypeVar("T", bound="ComputerValidationErrorResponse")


@_attrs_define
class ComputerValidationErrorResponse:
    """Validation error envelope returned by the application exception handler.

    Attributes:
        detail (Literal['Validation error']):
        errors (list[ComputerValidationErrorResponseErrorsItem]):
        status_code (Literal[422]):
    """

    detail: Literal["Validation error"]
    errors: list[ComputerValidationErrorResponseErrorsItem]
    status_code: Literal[422]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.computer_validation_error_response_errors_item import (
            ComputerValidationErrorResponseErrorsItem,
        )  # noqa: PLC0415

        detail = self.detail

        errors = []
        for errors_item_data in self.errors:
            errors_item = errors_item_data.to_dict()
            errors.append(errors_item)

        status_code = self.status_code

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "detail": detail,
                "errors": errors,
                "status_code": status_code,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.computer_validation_error_response_errors_item import (
            ComputerValidationErrorResponseErrorsItem,
        )  # noqa: PLC0415

        d = dict(src_dict)
        detail = cast(Literal["Validation error"], d.pop("detail"))
        if detail != "Validation error":
            raise ValueError(
                f"detail must match const 'Validation error', got '{detail}'"
            )

        errors = []
        _errors = d.pop("errors")
        for errors_item_data in _errors:
            errors_item = ComputerValidationErrorResponseErrorsItem.from_dict(
                errors_item_data
            )

            errors.append(errors_item)

        status_code = cast(Literal[422], d.pop("status_code"))
        if status_code != 422:
            raise ValueError(f"status_code must match const 422, got '{status_code}'")

        computer_validation_error_response = cls(
            detail=detail,
            errors=errors,
            status_code=status_code,
        )

        computer_validation_error_response.additional_properties = d
        return computer_validation_error_response

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

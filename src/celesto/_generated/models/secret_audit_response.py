from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from typing import cast

if TYPE_CHECKING:
    from ..models.audit_log_item import AuditLogItem


T = TypeVar("T", bound="SecretAuditResponse")


@_attrs_define
class SecretAuditResponse:
    """Audit trail for a secret

    Attributes:
        secret_id (str):
        audit_trail (list[AuditLogItem]):
    """

    secret_id: str
    audit_trail: list[AuditLogItem]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.audit_log_item import AuditLogItem  # noqa: PLC0415

        secret_id = self.secret_id

        audit_trail = []
        for audit_trail_item_data in self.audit_trail:
            audit_trail_item = audit_trail_item_data.to_dict()
            audit_trail.append(audit_trail_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "secret_id": secret_id,
                "audit_trail": audit_trail,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.audit_log_item import AuditLogItem  # noqa: PLC0415

        d = dict(src_dict)
        secret_id = d.pop("secret_id")

        audit_trail = []
        _audit_trail = d.pop("audit_trail")
        for audit_trail_item_data in _audit_trail:
            audit_trail_item = AuditLogItem.from_dict(audit_trail_item_data)

            audit_trail.append(audit_trail_item)

        secret_audit_response = cls(
            secret_id=secret_id,
            audit_trail=audit_trail,
        )

        secret_audit_response.additional_properties = d
        return secret_audit_response

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

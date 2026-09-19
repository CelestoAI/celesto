from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.secret_action import SecretAction
from ..types import UNSET, Unset
from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.audit_log_item_changes_type_0 import AuditLogItemChangesType0
    from ..models.performed_by_user import PerformedByUser


T = TypeVar("T", bound="AuditLogItem")


@_attrs_define
class AuditLogItem:
    """Individual audit log entry

    Attributes:
        action (SecretAction): Audit action types for secrets
        performed_by (PerformedByUser): User DTO for audit trail - minimal user info for display
        performed_at (datetime.datetime):
        ip_address (None | str | Unset):
        user_agent (None | str | Unset):
        changes (AuditLogItemChangesType0 | None | Unset):
    """

    action: SecretAction
    performed_by: PerformedByUser
    performed_at: datetime.datetime
    ip_address: None | str | Unset = UNSET
    user_agent: None | str | Unset = UNSET
    changes: AuditLogItemChangesType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.audit_log_item_changes_type_0 import AuditLogItemChangesType0  # noqa: PLC0415
        from ..models.performed_by_user import PerformedByUser  # noqa: PLC0415

        action = self.action.value

        performed_by = self.performed_by.to_dict()

        performed_at = self.performed_at.isoformat()

        ip_address: None | str | Unset
        if isinstance(self.ip_address, Unset):
            ip_address = UNSET
        else:
            ip_address = self.ip_address

        user_agent: None | str | Unset
        if isinstance(self.user_agent, Unset):
            user_agent = UNSET
        else:
            user_agent = self.user_agent

        changes: dict[str, Any] | None | Unset
        if isinstance(self.changes, Unset):
            changes = UNSET
        elif isinstance(self.changes, AuditLogItemChangesType0):
            changes = self.changes.to_dict()
        else:
            changes = self.changes

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "action": action,
                "performed_by": performed_by,
                "performed_at": performed_at,
            }
        )
        if ip_address is not UNSET:
            field_dict["ip_address"] = ip_address
        if user_agent is not UNSET:
            field_dict["user_agent"] = user_agent
        if changes is not UNSET:
            field_dict["changes"] = changes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.audit_log_item_changes_type_0 import AuditLogItemChangesType0  # noqa: PLC0415
        from ..models.performed_by_user import PerformedByUser  # noqa: PLC0415

        d = dict(src_dict)
        action = SecretAction(d.pop("action"))

        performed_by = PerformedByUser.from_dict(d.pop("performed_by"))

        performed_at = datetime.datetime.fromisoformat(d.pop("performed_at"))

        def _parse_ip_address(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        ip_address = _parse_ip_address(d.pop("ip_address", UNSET))

        def _parse_user_agent(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        user_agent = _parse_user_agent(d.pop("user_agent", UNSET))

        def _parse_changes(data: object) -> AuditLogItemChangesType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                changes_type_0 = AuditLogItemChangesType0.from_dict(data)

                return changes_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(AuditLogItemChangesType0 | None | Unset, data)

        changes = _parse_changes(d.pop("changes", UNSET))

        audit_log_item = cls(
            action=action,
            performed_by=performed_by,
            performed_at=performed_at,
            ip_address=ip_address,
            user_agent=user_agent,
            changes=changes,
        )

        audit_log_item.additional_properties = d
        return audit_log_item

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

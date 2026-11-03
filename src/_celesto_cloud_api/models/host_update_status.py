from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.host_update_status_state import HostUpdateStatusState
from ..types import UNSET, Unset
from typing import cast
import datetime


T = TypeVar("T", bound="HostUpdateStatus")


@_attrs_define
class HostUpdateStatus:
    """What the host's update job is doing, as the agent reads it from `update.json`.

    The control plane only stores it and shows it on the fleet dashboard
    (docs/designs/host-pull-release.md D-09); it never acts on it.

        Attributes:
            state (HostUpdateStatusState):
            target (None | str | Unset):
            since (datetime.datetime | None | Unset):
            tries (int | Unset):  Default: 0.
            reason (None | str | Unset):
    """

    state: HostUpdateStatusState
    target: None | str | Unset = UNSET
    since: datetime.datetime | None | Unset = UNSET
    tries: int | Unset = 0
    reason: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        state = self.state.value

        target: None | str | Unset
        if isinstance(self.target, Unset):
            target = UNSET
        else:
            target = self.target

        since: None | str | Unset
        if isinstance(self.since, Unset):
            since = UNSET
        elif isinstance(self.since, datetime.datetime):
            since = self.since.isoformat()
        else:
            since = self.since

        tries = self.tries

        reason: None | str | Unset
        if isinstance(self.reason, Unset):
            reason = UNSET
        else:
            reason = self.reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "state": state,
            }
        )
        if target is not UNSET:
            field_dict["target"] = target
        if since is not UNSET:
            field_dict["since"] = since
        if tries is not UNSET:
            field_dict["tries"] = tries
        if reason is not UNSET:
            field_dict["reason"] = reason

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        state = HostUpdateStatusState(d.pop("state"))

        def _parse_target(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        target = _parse_target(d.pop("target", UNSET))

        def _parse_since(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                since_type_0 = datetime.datetime.fromisoformat(data)

                return since_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        since = _parse_since(d.pop("since", UNSET))

        tries = d.pop("tries", UNSET)

        def _parse_reason(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        reason = _parse_reason(d.pop("reason", UNSET))

        host_update_status = cls(
            state=state,
            target=target,
            since=since,
            tries=tries,
            reason=reason,
        )

        host_update_status.additional_properties = d
        return host_update_status

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

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.run_usage import RunUsage


T = TypeVar("T", bound="RunListItem")


@_attrs_define
class RunListItem:
    """One row of the org's run ledger — the envelope minus its bulky
    fields. ``output`` and ``error`` stay on GET /runs/{id}: a page of fifty
    list rows must not carry fifty final outputs over the wire.

        Attributes:
            run_id (str):
            status (str):
            agent_id (str):
            agent_version_id (str):
            session_id (str):
            end_user_id (str):
            usage (RunUsage):
            created_at (datetime.datetime):
            object_ (str | Unset):  Default: 'run'.
            error_code (None | str | Unset):
            turn_count (int | None | Unset):
            started_at (datetime.datetime | None | Unset):
            ended_at (datetime.datetime | None | Unset):
    """

    run_id: str
    status: str
    agent_id: str
    agent_version_id: str
    session_id: str
    end_user_id: str
    usage: RunUsage
    created_at: datetime.datetime
    object_: str | Unset = "run"
    error_code: None | str | Unset = UNSET
    turn_count: int | None | Unset = UNSET
    started_at: datetime.datetime | None | Unset = UNSET
    ended_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.run_usage import RunUsage  # noqa: PLC0415

        run_id = self.run_id

        status = self.status

        agent_id = self.agent_id

        agent_version_id = self.agent_version_id

        session_id = self.session_id

        end_user_id = self.end_user_id

        usage = self.usage.to_dict()

        created_at = self.created_at.isoformat()

        object_ = self.object_

        error_code: None | str | Unset
        if isinstance(self.error_code, Unset):
            error_code = UNSET
        else:
            error_code = self.error_code

        turn_count: int | None | Unset
        if isinstance(self.turn_count, Unset):
            turn_count = UNSET
        else:
            turn_count = self.turn_count

        started_at: None | str | Unset
        if isinstance(self.started_at, Unset):
            started_at = UNSET
        elif isinstance(self.started_at, datetime.datetime):
            started_at = self.started_at.isoformat()
        else:
            started_at = self.started_at

        ended_at: None | str | Unset
        if isinstance(self.ended_at, Unset):
            ended_at = UNSET
        elif isinstance(self.ended_at, datetime.datetime):
            ended_at = self.ended_at.isoformat()
        else:
            ended_at = self.ended_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "run_id": run_id,
                "status": status,
                "agent_id": agent_id,
                "agent_version_id": agent_version_id,
                "session_id": session_id,
                "end_user_id": end_user_id,
                "usage": usage,
                "created_at": created_at,
            }
        )
        if object_ is not UNSET:
            field_dict["object"] = object_
        if error_code is not UNSET:
            field_dict["error_code"] = error_code
        if turn_count is not UNSET:
            field_dict["turn_count"] = turn_count
        if started_at is not UNSET:
            field_dict["started_at"] = started_at
        if ended_at is not UNSET:
            field_dict["ended_at"] = ended_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.run_usage import RunUsage  # noqa: PLC0415

        d = dict(src_dict)
        run_id = d.pop("run_id")

        status = d.pop("status")

        agent_id = d.pop("agent_id")

        agent_version_id = d.pop("agent_version_id")

        session_id = d.pop("session_id")

        end_user_id = d.pop("end_user_id")

        usage = RunUsage.from_dict(d.pop("usage"))

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        object_ = d.pop("object", UNSET)

        def _parse_error_code(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error_code = _parse_error_code(d.pop("error_code", UNSET))

        def _parse_turn_count(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        turn_count = _parse_turn_count(d.pop("turn_count", UNSET))

        def _parse_started_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                started_at_type_0 = datetime.datetime.fromisoformat(data)

                return started_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        started_at = _parse_started_at(d.pop("started_at", UNSET))

        def _parse_ended_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                ended_at_type_0 = datetime.datetime.fromisoformat(data)

                return ended_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        ended_at = _parse_ended_at(d.pop("ended_at", UNSET))

        run_list_item = cls(
            run_id=run_id,
            status=status,
            agent_id=agent_id,
            agent_version_id=agent_version_id,
            session_id=session_id,
            end_user_id=end_user_id,
            usage=usage,
            created_at=created_at,
            object_=object_,
            error_code=error_code,
            turn_count=turn_count,
            started_at=started_at,
            ended_at=ended_at,
        )

        run_list_item.additional_properties = d
        return run_list_item

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

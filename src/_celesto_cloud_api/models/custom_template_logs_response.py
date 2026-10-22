from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.custom_template_status import CustomTemplateStatus
from ..types import UNSET, Unset


T = TypeVar("T", bound="CustomTemplateLogsResponse")


@_attrs_define
class CustomTemplateLogsResponse:
    """The end of the latest build's log.

    ``log`` is empty until the build worker has copied the first bytes.
    It holds at most the last 256 KB: ``offset`` is the byte position in the
    whole log where ``log`` starts, and ``truncated`` is True when earlier
    bytes were left out. ``size`` is how many log bytes are stored; send it
    back as ``known_size`` and, while it has not changed, the answer is
    ``unchanged: true`` with an empty ``log`` (keep showing the last one).

        Attributes:
            template_id (str):
            status (CustomTemplateStatus): Build state of a custom template.

                ``ready`` means the artifact columns hold a usable build. A rebuild moves
                the row back to ``queued``/``building`` but keeps the previous artifact
                columns until the new build succeeds.
            log (str | Unset):  Default: ''.
            offset (int | Unset):  Default: 0.
            truncated (bool | Unset):  Default: False.
            size (int | Unset):  Default: 0.
            unchanged (bool | Unset):  Default: False.
    """

    template_id: str
    status: CustomTemplateStatus
    log: str | Unset = ""
    offset: int | Unset = 0
    truncated: bool | Unset = False
    size: int | Unset = 0
    unchanged: bool | Unset = False
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        template_id = self.template_id

        status = self.status.value

        log = self.log

        offset = self.offset

        truncated = self.truncated

        size = self.size

        unchanged = self.unchanged

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "template_id": template_id,
                "status": status,
            }
        )
        if log is not UNSET:
            field_dict["log"] = log
        if offset is not UNSET:
            field_dict["offset"] = offset
        if truncated is not UNSET:
            field_dict["truncated"] = truncated
        if size is not UNSET:
            field_dict["size"] = size
        if unchanged is not UNSET:
            field_dict["unchanged"] = unchanged

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        template_id = d.pop("template_id")

        status = CustomTemplateStatus(d.pop("status"))

        log = d.pop("log", UNSET)

        offset = d.pop("offset", UNSET)

        truncated = d.pop("truncated", UNSET)

        size = d.pop("size", UNSET)

        unchanged = d.pop("unchanged", UNSET)

        custom_template_logs_response = cls(
            template_id=template_id,
            status=status,
            log=log,
            offset=offset,
            truncated=truncated,
            size=size,
            unchanged=unchanged,
        )

        custom_template_logs_response.additional_properties = d
        return custom_template_logs_response

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

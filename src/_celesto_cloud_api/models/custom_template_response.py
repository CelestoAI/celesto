from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.custom_template_status import CustomTemplateStatus
from ..types import UNSET, Unset
from typing import cast
import datetime

if TYPE_CHECKING:
    from ..models.lint_warning import LintWarning
    from ..models.template_build_failure import TemplateBuildFailure


T = TypeVar("T", bound="CustomTemplateResponse")


@_attrs_define
class CustomTemplateResponse:
    """A custom template. ``warnings`` is filled only on create and update.

    Attributes:
        id (str):
        name (str):
        organization_id (str):
        created_by (str):
        base_template_id (str):
        base_template_version (str):
        build_script (str):
        status (CustomTemplateStatus): Build state of a custom template.

            ``ready`` means the artifact columns hold a usable build. A rebuild moves
            the row back to ``queued``/``building`` but keeps the previous artifact
            columns until the new build succeeds.
        default_vcpus (int):
        default_ram_mb (int):
        default_disk_size_mb (int):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        project_id (None | str | Unset):
        error (None | str | Unset):
        failure (None | TemplateBuildFailure | Unset):
        rootfs_size_mb (int | None | Unset):
        warnings (list[LintWarning] | Unset):
    """

    id: str
    name: str
    organization_id: str
    created_by: str
    base_template_id: str
    base_template_version: str
    build_script: str
    status: CustomTemplateStatus
    default_vcpus: int
    default_ram_mb: int
    default_disk_size_mb: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    project_id: None | str | Unset = UNSET
    error: None | str | Unset = UNSET
    failure: None | TemplateBuildFailure | Unset = UNSET
    rootfs_size_mb: int | None | Unset = UNSET
    warnings: list[LintWarning] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.lint_warning import LintWarning  # noqa: PLC0415
        from ..models.template_build_failure import TemplateBuildFailure  # noqa: PLC0415

        id = self.id

        name = self.name

        organization_id = self.organization_id

        created_by = self.created_by

        base_template_id = self.base_template_id

        base_template_version = self.base_template_version

        build_script = self.build_script

        status = self.status.value

        default_vcpus = self.default_vcpus

        default_ram_mb = self.default_ram_mb

        default_disk_size_mb = self.default_disk_size_mb

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        project_id: None | str | Unset
        if isinstance(self.project_id, Unset):
            project_id = UNSET
        else:
            project_id = self.project_id

        error: None | str | Unset
        if isinstance(self.error, Unset):
            error = UNSET
        else:
            error = self.error

        failure: dict[str, Any] | None | Unset
        if isinstance(self.failure, Unset):
            failure = UNSET
        elif isinstance(self.failure, TemplateBuildFailure):
            failure = self.failure.to_dict()
        else:
            failure = self.failure

        rootfs_size_mb: int | None | Unset
        if isinstance(self.rootfs_size_mb, Unset):
            rootfs_size_mb = UNSET
        else:
            rootfs_size_mb = self.rootfs_size_mb

        warnings: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.warnings, Unset):
            warnings = []
            for warnings_item_data in self.warnings:
                warnings_item = warnings_item_data.to_dict()
                warnings.append(warnings_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "organization_id": organization_id,
                "created_by": created_by,
                "base_template_id": base_template_id,
                "base_template_version": base_template_version,
                "build_script": build_script,
                "status": status,
                "default_vcpus": default_vcpus,
                "default_ram_mb": default_ram_mb,
                "default_disk_size_mb": default_disk_size_mb,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )
        if project_id is not UNSET:
            field_dict["project_id"] = project_id
        if error is not UNSET:
            field_dict["error"] = error
        if failure is not UNSET:
            field_dict["failure"] = failure
        if rootfs_size_mb is not UNSET:
            field_dict["rootfs_size_mb"] = rootfs_size_mb
        if warnings is not UNSET:
            field_dict["warnings"] = warnings

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.lint_warning import LintWarning  # noqa: PLC0415
        from ..models.template_build_failure import TemplateBuildFailure  # noqa: PLC0415

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        organization_id = d.pop("organization_id")

        created_by = d.pop("created_by")

        base_template_id = d.pop("base_template_id")

        base_template_version = d.pop("base_template_version")

        build_script = d.pop("build_script")

        status = CustomTemplateStatus(d.pop("status"))

        default_vcpus = d.pop("default_vcpus")

        default_ram_mb = d.pop("default_ram_mb")

        default_disk_size_mb = d.pop("default_disk_size_mb")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))

        def _parse_project_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        project_id = _parse_project_id(d.pop("project_id", UNSET))

        def _parse_error(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        error = _parse_error(d.pop("error", UNSET))

        def _parse_failure(data: object) -> None | TemplateBuildFailure | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                failure_type_0 = TemplateBuildFailure.from_dict(data)

                return failure_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(None | TemplateBuildFailure | Unset, data)

        failure = _parse_failure(d.pop("failure", UNSET))

        def _parse_rootfs_size_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        rootfs_size_mb = _parse_rootfs_size_mb(d.pop("rootfs_size_mb", UNSET))

        _warnings = d.pop("warnings", UNSET)
        warnings: list[LintWarning] | Unset = UNSET
        if _warnings is not UNSET:
            warnings = []
            for warnings_item_data in _warnings:
                warnings_item = LintWarning.from_dict(warnings_item_data)

                warnings.append(warnings_item)

        custom_template_response = cls(
            id=id,
            name=name,
            organization_id=organization_id,
            created_by=created_by,
            base_template_id=base_template_id,
            base_template_version=base_template_version,
            build_script=build_script,
            status=status,
            default_vcpus=default_vcpus,
            default_ram_mb=default_ram_mb,
            default_disk_size_mb=default_disk_size_mb,
            created_at=created_at,
            updated_at=updated_at,
            project_id=project_id,
            error=error,
            failure=failure,
            rootfs_size_mb=rootfs_size_mb,
            warnings=warnings,
        )

        custom_template_response.additional_properties = d
        return custom_template_response

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

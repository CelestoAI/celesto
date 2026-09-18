from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..models.computer_snapshot_report_request_artifact_kind_type_0 import (
    ComputerSnapshotReportRequestArtifactKindType0,
)
from ..models.computer_snapshot_report_request_consistency_type_0 import (
    ComputerSnapshotReportRequestConsistencyType0,
)
from ..models.computer_snapshot_report_request_disk_format_type_0 import (
    ComputerSnapshotReportRequestDiskFormatType0,
)
from ..types import UNSET, Unset
from typing import cast
from typing import Literal, cast
import datetime


T = TypeVar("T", bound="ComputerSnapshotReportRequest")


@_attrs_define
class ComputerSnapshotReportRequest:
    """Host agent reports a disk snapshot it uploaded to S3 for a VM.

    Attributes:
        vm_id (str):
        s3_uri (str):
        snapshot_at (datetime.datetime | None | Unset): When the snapshot was taken (UTC). Server time used if omitted.
        snapshot_id (None | str | Unset):
        source_host_boot_id (None | str | Unset):
        manifest_s3_uri (None | str | Unset):
        object_version_id (None | str | Unset):
        artifact_kind (ComputerSnapshotReportRequestArtifactKindType0 | None | Unset):
        parent_snapshot_id (None | str | Unset):
        chain_id (None | str | Unset):
        chain_depth (int | None | Unset):
        virtual_size_bytes (int | None | Unset):
        changed_bytes (int | None | Unset):
        bitmap_granularity_bytes (int | None | Unset):
        checksum_sha256 (None | str | Unset):
        size_bytes (int | None | Unset):
        disk_format (ComputerSnapshotReportRequestDiskFormatType0 | None | Unset):
        backend (None | str | Unset):
        consistency (ComputerSnapshotReportRequestConsistencyType0 | None | Unset):
        home_consistency (Literal['independent'] | None | Unset):
        captured_at (datetime.datetime | None | Unset):
        uploaded_at (datetime.datetime | None | Unset):
    """

    vm_id: str
    s3_uri: str
    snapshot_at: datetime.datetime | None | Unset = UNSET
    snapshot_id: None | str | Unset = UNSET
    source_host_boot_id: None | str | Unset = UNSET
    manifest_s3_uri: None | str | Unset = UNSET
    object_version_id: None | str | Unset = UNSET
    artifact_kind: ComputerSnapshotReportRequestArtifactKindType0 | None | Unset = UNSET
    parent_snapshot_id: None | str | Unset = UNSET
    chain_id: None | str | Unset = UNSET
    chain_depth: int | None | Unset = UNSET
    virtual_size_bytes: int | None | Unset = UNSET
    changed_bytes: int | None | Unset = UNSET
    bitmap_granularity_bytes: int | None | Unset = UNSET
    checksum_sha256: None | str | Unset = UNSET
    size_bytes: int | None | Unset = UNSET
    disk_format: ComputerSnapshotReportRequestDiskFormatType0 | None | Unset = UNSET
    backend: None | str | Unset = UNSET
    consistency: ComputerSnapshotReportRequestConsistencyType0 | None | Unset = UNSET
    home_consistency: Literal["independent"] | None | Unset = UNSET
    captured_at: datetime.datetime | None | Unset = UNSET
    uploaded_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        vm_id = self.vm_id

        s3_uri = self.s3_uri

        snapshot_at: None | str | Unset
        if isinstance(self.snapshot_at, Unset):
            snapshot_at = UNSET
        elif isinstance(self.snapshot_at, datetime.datetime):
            snapshot_at = self.snapshot_at.isoformat()
        else:
            snapshot_at = self.snapshot_at

        snapshot_id: None | str | Unset
        if isinstance(self.snapshot_id, Unset):
            snapshot_id = UNSET
        else:
            snapshot_id = self.snapshot_id

        source_host_boot_id: None | str | Unset
        if isinstance(self.source_host_boot_id, Unset):
            source_host_boot_id = UNSET
        else:
            source_host_boot_id = self.source_host_boot_id

        manifest_s3_uri: None | str | Unset
        if isinstance(self.manifest_s3_uri, Unset):
            manifest_s3_uri = UNSET
        else:
            manifest_s3_uri = self.manifest_s3_uri

        object_version_id: None | str | Unset
        if isinstance(self.object_version_id, Unset):
            object_version_id = UNSET
        else:
            object_version_id = self.object_version_id

        artifact_kind: None | str | Unset
        if isinstance(self.artifact_kind, Unset):
            artifact_kind = UNSET
        elif isinstance(
            self.artifact_kind, ComputerSnapshotReportRequestArtifactKindType0
        ):
            artifact_kind = self.artifact_kind.value
        else:
            artifact_kind = self.artifact_kind

        parent_snapshot_id: None | str | Unset
        if isinstance(self.parent_snapshot_id, Unset):
            parent_snapshot_id = UNSET
        else:
            parent_snapshot_id = self.parent_snapshot_id

        chain_id: None | str | Unset
        if isinstance(self.chain_id, Unset):
            chain_id = UNSET
        else:
            chain_id = self.chain_id

        chain_depth: int | None | Unset
        if isinstance(self.chain_depth, Unset):
            chain_depth = UNSET
        else:
            chain_depth = self.chain_depth

        virtual_size_bytes: int | None | Unset
        if isinstance(self.virtual_size_bytes, Unset):
            virtual_size_bytes = UNSET
        else:
            virtual_size_bytes = self.virtual_size_bytes

        changed_bytes: int | None | Unset
        if isinstance(self.changed_bytes, Unset):
            changed_bytes = UNSET
        else:
            changed_bytes = self.changed_bytes

        bitmap_granularity_bytes: int | None | Unset
        if isinstance(self.bitmap_granularity_bytes, Unset):
            bitmap_granularity_bytes = UNSET
        else:
            bitmap_granularity_bytes = self.bitmap_granularity_bytes

        checksum_sha256: None | str | Unset
        if isinstance(self.checksum_sha256, Unset):
            checksum_sha256 = UNSET
        else:
            checksum_sha256 = self.checksum_sha256

        size_bytes: int | None | Unset
        if isinstance(self.size_bytes, Unset):
            size_bytes = UNSET
        else:
            size_bytes = self.size_bytes

        disk_format: None | str | Unset
        if isinstance(self.disk_format, Unset):
            disk_format = UNSET
        elif isinstance(self.disk_format, ComputerSnapshotReportRequestDiskFormatType0):
            disk_format = self.disk_format.value
        else:
            disk_format = self.disk_format

        backend: None | str | Unset
        if isinstance(self.backend, Unset):
            backend = UNSET
        else:
            backend = self.backend

        consistency: None | str | Unset
        if isinstance(self.consistency, Unset):
            consistency = UNSET
        elif isinstance(
            self.consistency, ComputerSnapshotReportRequestConsistencyType0
        ):
            consistency = self.consistency.value
        else:
            consistency = self.consistency

        home_consistency: Literal["independent"] | None | Unset
        if isinstance(self.home_consistency, Unset):
            home_consistency = UNSET
        else:
            home_consistency = self.home_consistency

        captured_at: None | str | Unset
        if isinstance(self.captured_at, Unset):
            captured_at = UNSET
        elif isinstance(self.captured_at, datetime.datetime):
            captured_at = self.captured_at.isoformat()
        else:
            captured_at = self.captured_at

        uploaded_at: None | str | Unset
        if isinstance(self.uploaded_at, Unset):
            uploaded_at = UNSET
        elif isinstance(self.uploaded_at, datetime.datetime):
            uploaded_at = self.uploaded_at.isoformat()
        else:
            uploaded_at = self.uploaded_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "vm_id": vm_id,
                "s3_uri": s3_uri,
            }
        )
        if snapshot_at is not UNSET:
            field_dict["snapshot_at"] = snapshot_at
        if snapshot_id is not UNSET:
            field_dict["snapshot_id"] = snapshot_id
        if source_host_boot_id is not UNSET:
            field_dict["source_host_boot_id"] = source_host_boot_id
        if manifest_s3_uri is not UNSET:
            field_dict["manifest_s3_uri"] = manifest_s3_uri
        if object_version_id is not UNSET:
            field_dict["object_version_id"] = object_version_id
        if artifact_kind is not UNSET:
            field_dict["artifact_kind"] = artifact_kind
        if parent_snapshot_id is not UNSET:
            field_dict["parent_snapshot_id"] = parent_snapshot_id
        if chain_id is not UNSET:
            field_dict["chain_id"] = chain_id
        if chain_depth is not UNSET:
            field_dict["chain_depth"] = chain_depth
        if virtual_size_bytes is not UNSET:
            field_dict["virtual_size_bytes"] = virtual_size_bytes
        if changed_bytes is not UNSET:
            field_dict["changed_bytes"] = changed_bytes
        if bitmap_granularity_bytes is not UNSET:
            field_dict["bitmap_granularity_bytes"] = bitmap_granularity_bytes
        if checksum_sha256 is not UNSET:
            field_dict["checksum_sha256"] = checksum_sha256
        if size_bytes is not UNSET:
            field_dict["size_bytes"] = size_bytes
        if disk_format is not UNSET:
            field_dict["disk_format"] = disk_format
        if backend is not UNSET:
            field_dict["backend"] = backend
        if consistency is not UNSET:
            field_dict["consistency"] = consistency
        if home_consistency is not UNSET:
            field_dict["home_consistency"] = home_consistency
        if captured_at is not UNSET:
            field_dict["captured_at"] = captured_at
        if uploaded_at is not UNSET:
            field_dict["uploaded_at"] = uploaded_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        vm_id = d.pop("vm_id")

        s3_uri = d.pop("s3_uri")

        def _parse_snapshot_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                snapshot_at_type_0 = datetime.datetime.fromisoformat(data)

                return snapshot_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        snapshot_at = _parse_snapshot_at(d.pop("snapshot_at", UNSET))

        def _parse_snapshot_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        snapshot_id = _parse_snapshot_id(d.pop("snapshot_id", UNSET))

        def _parse_source_host_boot_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        source_host_boot_id = _parse_source_host_boot_id(
            d.pop("source_host_boot_id", UNSET)
        )

        def _parse_manifest_s3_uri(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        manifest_s3_uri = _parse_manifest_s3_uri(d.pop("manifest_s3_uri", UNSET))

        def _parse_object_version_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        object_version_id = _parse_object_version_id(d.pop("object_version_id", UNSET))

        def _parse_artifact_kind(
            data: object,
        ) -> ComputerSnapshotReportRequestArtifactKindType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                artifact_kind_type_0 = ComputerSnapshotReportRequestArtifactKindType0(
                    data
                )

                return artifact_kind_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                ComputerSnapshotReportRequestArtifactKindType0 | None | Unset, data
            )

        artifact_kind = _parse_artifact_kind(d.pop("artifact_kind", UNSET))

        def _parse_parent_snapshot_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        parent_snapshot_id = _parse_parent_snapshot_id(
            d.pop("parent_snapshot_id", UNSET)
        )

        def _parse_chain_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        chain_id = _parse_chain_id(d.pop("chain_id", UNSET))

        def _parse_chain_depth(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        chain_depth = _parse_chain_depth(d.pop("chain_depth", UNSET))

        def _parse_virtual_size_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        virtual_size_bytes = _parse_virtual_size_bytes(
            d.pop("virtual_size_bytes", UNSET)
        )

        def _parse_changed_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        changed_bytes = _parse_changed_bytes(d.pop("changed_bytes", UNSET))

        def _parse_bitmap_granularity_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        bitmap_granularity_bytes = _parse_bitmap_granularity_bytes(
            d.pop("bitmap_granularity_bytes", UNSET)
        )

        def _parse_checksum_sha256(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        checksum_sha256 = _parse_checksum_sha256(d.pop("checksum_sha256", UNSET))

        def _parse_size_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        size_bytes = _parse_size_bytes(d.pop("size_bytes", UNSET))

        def _parse_disk_format(
            data: object,
        ) -> ComputerSnapshotReportRequestDiskFormatType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                disk_format_type_0 = ComputerSnapshotReportRequestDiskFormatType0(data)

                return disk_format_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                ComputerSnapshotReportRequestDiskFormatType0 | None | Unset, data
            )

        disk_format = _parse_disk_format(d.pop("disk_format", UNSET))

        def _parse_backend(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        backend = _parse_backend(d.pop("backend", UNSET))

        def _parse_consistency(
            data: object,
        ) -> ComputerSnapshotReportRequestConsistencyType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                consistency_type_0 = ComputerSnapshotReportRequestConsistencyType0(data)

                return consistency_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                ComputerSnapshotReportRequestConsistencyType0 | None | Unset, data
            )

        consistency = _parse_consistency(d.pop("consistency", UNSET))

        def _parse_home_consistency(
            data: object,
        ) -> Literal["independent"] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            home_consistency_type_0 = cast(Literal["independent"], data)
            if home_consistency_type_0 != "independent":
                raise ValueError(
                    f"home_consistency_type_0 must match const 'independent', got '{home_consistency_type_0}'"
                )
            return home_consistency_type_0
            return cast(Literal["independent"] | None | Unset, data)

        home_consistency = _parse_home_consistency(d.pop("home_consistency", UNSET))

        def _parse_captured_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                captured_at_type_0 = datetime.datetime.fromisoformat(data)

                return captured_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        captured_at = _parse_captured_at(d.pop("captured_at", UNSET))

        def _parse_uploaded_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                uploaded_at_type_0 = datetime.datetime.fromisoformat(data)

                return uploaded_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        uploaded_at = _parse_uploaded_at(d.pop("uploaded_at", UNSET))

        computer_snapshot_report_request = cls(
            vm_id=vm_id,
            s3_uri=s3_uri,
            snapshot_at=snapshot_at,
            snapshot_id=snapshot_id,
            source_host_boot_id=source_host_boot_id,
            manifest_s3_uri=manifest_s3_uri,
            object_version_id=object_version_id,
            artifact_kind=artifact_kind,
            parent_snapshot_id=parent_snapshot_id,
            chain_id=chain_id,
            chain_depth=chain_depth,
            virtual_size_bytes=virtual_size_bytes,
            changed_bytes=changed_bytes,
            bitmap_granularity_bytes=bitmap_granularity_bytes,
            checksum_sha256=checksum_sha256,
            size_bytes=size_bytes,
            disk_format=disk_format,
            backend=backend,
            consistency=consistency,
            home_consistency=home_consistency,
            captured_at=captured_at,
            uploaded_at=uploaded_at,
        )

        computer_snapshot_report_request.additional_properties = d
        return computer_snapshot_report_request

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

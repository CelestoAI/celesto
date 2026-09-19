from enum import StrEnum


class ComputerSnapshotReportRequestDiskFormatType0(StrEnum):
    EXT4 = "ext4"
    QCOW2 = "qcow2"

    def __str__(self) -> str:
        return str(self.value)

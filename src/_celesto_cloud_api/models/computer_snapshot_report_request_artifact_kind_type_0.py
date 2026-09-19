from enum import StrEnum


class ComputerSnapshotReportRequestArtifactKindType0(StrEnum):
    FULL = "full"
    INCREMENTAL = "incremental"

    def __str__(self) -> str:
        return str(self.value)

from enum import StrEnum


class ComputerSnapshotReportRequestConsistencyType0(StrEnum):
    CRASH = "crash"
    FILESYSTEM = "filesystem"

    def __str__(self) -> str:
        return str(self.value)

from enum import StrEnum


class CustomTemplateStatus(StrEnum):
    BUILDING = "building"
    FAILED = "failed"
    NEEDS_REBUILD = "needs_rebuild"
    QUEUED = "queued"
    READY = "ready"

    def __str__(self) -> str:
        return str(self.value)

from enum import StrEnum


class AppDeploymentStatus(StrEnum):
    BUILDING = "BUILDING"
    ENQUEUED = "ENQUEUED"
    FAILED = "FAILED"
    PENDING = "PENDING"
    READY = "READY"
    STOPPED = "STOPPED"

    def __str__(self) -> str:
        return str(self.value)

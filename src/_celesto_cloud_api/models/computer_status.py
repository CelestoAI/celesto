from enum import StrEnum


class ComputerStatus(StrEnum):
    CREATING = "creating"
    DELETED = "deleted"
    DELETING = "deleting"
    ERROR = "error"
    RESTORABLE = "restorable"
    RESTORING = "restoring"
    RUNNING = "running"
    STARTING = "starting"
    STOPPED = "stopped"
    STOPPING = "stopping"

    def __str__(self) -> str:
        return str(self.value)

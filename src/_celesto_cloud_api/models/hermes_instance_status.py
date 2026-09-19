from enum import StrEnum


class HermesInstanceStatus(StrEnum):
    DELETED = "deleted"
    DELETING = "deleting"
    FAILED = "failed"
    PENDING = "pending"
    PROVISIONING = "provisioning"
    RECOVERING = "recovering"
    RUNNING = "running"
    STARTING = "starting"
    STOPPED = "stopped"
    STOPPING = "stopping"

    def __str__(self) -> str:
        return str(self.value)

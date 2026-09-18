from enum import StrEnum


class Status(StrEnum):
    DONE = "DONE"
    FAILED = "FAILED"
    PENDING = "PENDING"
    STARTED = "STARTED"

    def __str__(self) -> str:
        return str(self.value)

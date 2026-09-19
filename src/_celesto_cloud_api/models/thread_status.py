from enum import StrEnum


class ThreadStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"

    def __str__(self) -> str:
        return str(self.value)

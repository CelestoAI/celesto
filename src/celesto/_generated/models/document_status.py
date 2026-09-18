from enum import StrEnum


class DocumentStatus(StrEnum):
    FAILED = "FAILED"
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    PROCESSING = "PROCESSING"

    def __str__(self) -> str:
        return str(self.value)

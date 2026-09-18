from enum import StrEnum


class ComputerDisplayConnectionRequestMode(StrEnum):
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"

    def __str__(self) -> str:
        return str(self.value)

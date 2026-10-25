from enum import IntEnum


class SandboxActivityWindowDays(IntEnum):
    VALUE_1 = 1
    VALUE_7 = 7
    VALUE_30 = 30

    def __str__(self) -> str:
        return str(self.value)

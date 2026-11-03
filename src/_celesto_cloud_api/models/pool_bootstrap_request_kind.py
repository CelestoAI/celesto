from enum import StrEnum


class PoolBootstrapRequestKind(StrEnum):
    COMMAND = "command"
    RESULT = "result"

    def __str__(self) -> str:
        return str(self.value)

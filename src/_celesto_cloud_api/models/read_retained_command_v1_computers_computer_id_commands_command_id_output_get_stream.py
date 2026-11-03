from enum import StrEnum


class ReadRetainedCommandV1ComputersComputerIdCommandsCommandIdOutputGetStream(StrEnum):
    STDERR = "stderr"
    STDOUT = "stdout"

    def __str__(self) -> str:
        return str(self.value)

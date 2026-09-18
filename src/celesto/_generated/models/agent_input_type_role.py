from enum import StrEnum


class AgentInputTypeRole(StrEnum):
    ASSISTANT = "assistant"
    SYSTEM = "system"
    USER = "user"

    def __str__(self) -> str:
        return str(self.value)

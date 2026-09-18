from enum import StrEnum


class TelegramBotStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"

    def __str__(self) -> str:
        return str(self.value)

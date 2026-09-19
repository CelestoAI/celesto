from enum import StrEnum


class OutboundGenerationResponseChannel(StrEnum):
    EMAIL = "email"
    LINKEDIN = "linkedin"

    def __str__(self) -> str:
        return str(self.value)

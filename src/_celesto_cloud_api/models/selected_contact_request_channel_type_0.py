from enum import StrEnum


class SelectedContactRequestChannelType0(StrEnum):
    EMAIL = "email"
    LINKEDIN = "linkedin"

    def __str__(self) -> str:
        return str(self.value)

from enum import StrEnum


class OpenClawProvider(StrEnum):
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OPENAI = "openai"
    OPENROUTER = "openrouter"

    def __str__(self) -> str:
        return str(self.value)

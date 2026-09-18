from enum import StrEnum


class HermesProvider(StrEnum):
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OPENAI_API = "openai-api"
    OPENROUTER = "openrouter"

    def __str__(self) -> str:
        return str(self.value)

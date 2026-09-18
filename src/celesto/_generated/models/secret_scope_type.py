from enum import StrEnum


class SecretScopeType(StrEnum):
    ORGANIZATION = "organization"
    PROJECT = "project"

    def __str__(self) -> str:
        return str(self.value)

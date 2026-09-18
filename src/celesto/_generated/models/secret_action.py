from enum import StrEnum


class SecretAction(StrEnum):
    CREATED = "created"
    DELETED = "deleted"
    READ = "read"
    UPDATED = "updated"

    def __str__(self) -> str:
        return str(self.value)

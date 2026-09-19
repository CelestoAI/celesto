from enum import StrEnum


class MembershipStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    REMOVED = "REMOVED"

    def __str__(self) -> str:
        return str(self.value)

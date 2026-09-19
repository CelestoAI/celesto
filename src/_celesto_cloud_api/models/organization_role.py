from enum import StrEnum


class OrganizationRole(StrEnum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    OWNER = "OWNER"
    VIEWER = "VIEWER"

    def __str__(self) -> str:
        return str(self.value)

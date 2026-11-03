from enum import StrEnum


class OrganizationBillingBalanceStatus(StrEnum):
    AVAILABLE = "available"
    NO_ACCOUNT = "no_account"
    UNAVAILABLE = "unavailable"

    def __str__(self) -> str:
        return str(self.value)

from enum import StrEnum


class OperatorBillingReportPaymentsStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"

    def __str__(self) -> str:
        return str(self.value)

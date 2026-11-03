from enum import StrEnum


class AutoTopupChargeResponseStatus(StrEnum):
    FAILED = "failed"
    GRANTED = "granted"
    PAID = "paid"
    PENDING = "pending"
    REVERSED = "reversed"

    def __str__(self) -> str:
        return str(self.value)

from enum import StrEnum


class UsageAccessResponseState(StrEnum):
    CHECKOUT_PENDING = "checkout_pending"
    NONE = "none"
    PAID = "paid"
    PAYMENT_FAILED = "payment_failed"
    PREPAID_REQUIRED = "prepaid_required"
    PROMOTIONAL = "promotional"
    TRIAL = "trial"
    TRIAL_EXPIRED = "trial_expired"

    def __str__(self) -> str:
        return str(self.value)

from enum import StrEnum


class AutoTopupResponsePausedReasonType0(StrEnum):
    AUTHENTICATION_REQUIRED = "authentication_required"
    CARD_DECLINED = "card_declined"
    CREDIT_DELAYED = "credit_delayed"
    INVOICE_MISMATCH = "invoice_mismatch"
    PAYMENT_METHOD_UNAVAILABLE = "payment_method_unavailable"
    PAYMENT_REVERSED = "payment_reversed"

    def __str__(self) -> str:
        return str(self.value)

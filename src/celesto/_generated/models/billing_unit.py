from enum import StrEnum


class BillingUnit(StrEnum):
    RUN = "run"
    TOOL_CALL = "tool_call"
    TRACE = "trace"

    def __str__(self) -> str:
        return str(self.value)

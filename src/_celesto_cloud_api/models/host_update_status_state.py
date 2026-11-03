from enum import StrEnum


class HostUpdateStatusState(StrEnum):
    DEFERRED = "deferred"
    FAILED = "failed"
    PAUSED = "paused"
    ROLLED_BACK = "rolled_back"
    STAGED = "staged"
    STUCK_DEFERRED = "stuck_deferred"
    SWITCHED = "switched"
    UP_TO_DATE = "up_to_date"
    WATCHING = "watching"

    def __str__(self) -> str:
        return str(self.value)

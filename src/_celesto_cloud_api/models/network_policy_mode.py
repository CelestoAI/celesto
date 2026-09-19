from enum import StrEnum


class NetworkPolicyMode(StrEnum):
    OFF = "off"
    OPEN = "open"

    def __str__(self) -> str:
        return str(self.value)

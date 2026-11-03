from enum import IntEnum


class CiMinutesSeriesDays(IntEnum):
    VALUE_1 = 1
    VALUE_7 = 7
    VALUE_30 = 30
    VALUE_90 = 90

    def __str__(self) -> str:
        return str(self.value)

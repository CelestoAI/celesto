from enum import StrEnum


class GetSandboxSizesV1BillingSizesGetPriceVersion(StrEnum):
    USAGE_V1 = "usage-v1"
    USAGE_V2 = "usage-v2"

    def __str__(self) -> str:
        return str(self.value)

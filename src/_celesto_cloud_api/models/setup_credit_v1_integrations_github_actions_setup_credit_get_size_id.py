from enum import StrEnum


class SetupCreditV1IntegrationsGithubActionsSetupCreditGetSizeId(StrEnum):
    LARGE = "large"
    MEMORY = "memory"
    MICRO = "micro"
    SMALL = "small"
    STANDARD = "standard"
    XL = "xl"

    def __str__(self) -> str:
        return str(self.value)

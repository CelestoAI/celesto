from enum import StrEnum


class LintWarningCode(StrEnum):
    APT_WITHOUT_YES = "apt_without_yes"
    FILE_REFERENCE = "file_reference"

    def __str__(self) -> str:
        return str(self.value)

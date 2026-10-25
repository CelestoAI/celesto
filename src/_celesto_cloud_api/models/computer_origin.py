from enum import StrEnum


class ComputerOrigin(StrEnum):
    GITHUB_CI = "github_ci"
    MCP = "mcp"
    SDK = "sdk"
    TEMPLATE_BUILD = "template_build"
    UI = "ui"

    def __str__(self) -> str:
        return str(self.value)

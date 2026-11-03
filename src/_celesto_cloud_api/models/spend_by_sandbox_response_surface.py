from enum import StrEnum


class SpendBySandboxResponseSurface(StrEnum):
    CLI = "cli"
    GITHUB_CI = "github_ci"
    MCP = "mcp"
    SDK = "sdk"
    TEMPLATE_BUILD = "template_build"
    UI = "ui"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return str(self.value)

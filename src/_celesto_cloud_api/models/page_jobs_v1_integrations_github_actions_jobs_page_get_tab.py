from enum import StrEnum


class PageJobsV1IntegrationsGithubActionsJobsPageGetTab(StrEnum):
    ALL = "all"
    COMPLETED = "completed"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    NEEDS_ACTION = "needs_action"
    PASSED = "passed"

    def __str__(self) -> str:
        return str(self.value)

# Copyright 2026 Celesto AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Exception hierarchy for Celesto SDK."""

from typing import Literal

_MAX_CLOUD_ERROR_DETAIL_LENGTH = 500


class CelestoError(Exception):
    """Base exception for all Celesto errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class CloudAPIError(CelestoError):
    """A cloud API request failed with an HTTP error status."""

    def __init__(
        self,
        status_code: int,
        *,
        detail: str | None = None,
        recovery: str | None = None,
    ) -> None:
        self.status_code = int(status_code)
        if recovery is None:
            recovery = (
                "Check your API key and organization access."
                if status_code in (401, 403)
                else "Check the request and cloud dashboard before retrying."
            )
        # Only the documented bad-request detail is retained, never the raw body.
        details = (
            {"detail": detail[:_MAX_CLOUD_ERROR_DETAIL_LENGTH]}
            if status_code == 400 and isinstance(detail, str)
            else {}
        )
        super().__init__(f"Cloud API returned HTTP {status_code}. {recovery}", details=details)


class ValidationError(CelestoError):
    """Raised when input validation fails."""

    pass


class VMAlreadyExistsError(CelestoError):
    """Raised when attempting to create a VM with an existing ID."""

    def __init__(self, vm_id: str) -> None:
        super().__init__(f"VM '{vm_id}' already exists", {"vm_id": vm_id})
        self.vm_id = vm_id


class VMNotFoundError(CelestoError):
    """Raised when a VM is not found."""

    def __init__(self, vm_id: str) -> None:
        super().__init__(f"VM '{vm_id}' not found", {"vm_id": vm_id})
        self.vm_id = vm_id


class SnapshotAlreadyExistsError(CelestoError):
    """Raised when attempting to create a snapshot with an existing ID."""

    def __init__(self, snapshot_id: str) -> None:
        super().__init__(
            f"Snapshot '{snapshot_id}' already exists",
            {"snapshot_id": snapshot_id},
        )
        self.snapshot_id = snapshot_id


class SnapshotNotFoundError(CelestoError):
    """Raised when a snapshot is not found."""

    def __init__(self, snapshot_id: str) -> None:
        super().__init__(
            f"Snapshot '{snapshot_id}' not found",
            {"snapshot_id": snapshot_id},
        )
        self.snapshot_id = snapshot_id


class QemuDirtyBitmapStateError(CelestoError):
    """Raised when a named QEMU dirty bitmap cannot serve its requested operation."""

    def __init__(
        self,
        vm_id: str,
        bitmap_name: str,
        reason: Literal[
            "missing",
            "exists",
            "busy",
            "disabled",
            "non-persistent",
            "inconsistent",
        ],
        *,
        details: dict | None = None,
        recovery_command: str | None = None,
    ) -> None:
        state_details = {
            **(details or {}),
            "vm_id": vm_id,
            "bitmap_name": bitmap_name,
            "reason": reason,
        }
        if recovery_command is not None:
            state_details["recovery_command"] = recovery_command
        description = {
            "missing": "is missing",
            "exists": "already exists",
            "busy": "is busy",
            "disabled": "is disabled",
            "non-persistent": "is not persistent",
            "inconsistent": "is inconsistent",
        }[reason]
        message = f"The dirty bitmap '{bitmap_name}' for sandbox '{vm_id}' {description}"
        if recovery_command is not None:
            message = f"{message}; recover with '{recovery_command}'."
        super().__init__(message, state_details)
        self.vm_id = vm_id
        self.bitmap_name = bitmap_name
        self.reason = reason
        self.recovery_command = recovery_command


class BrowserSessionAlreadyExistsError(CelestoError):
    """Raised when attempting to create a browser session with an existing ID."""

    def __init__(self, session_id: str) -> None:
        super().__init__(
            f"Browser session '{session_id}' already exists",
            {"session_id": session_id},
        )
        self.session_id = session_id


class BrowserSessionNotFoundError(CelestoError):
    """Raised when a browser session is not found."""

    def __init__(self, session_id: str) -> None:
        super().__init__(
            f"Browser session '{session_id}' not found",
            {"session_id": session_id},
        )
        self.session_id = session_id


class NetworkError(CelestoError):
    """Raised when network operations fail (TAP, NAT, IP allocation)."""

    pass


class BridgeTapOwnershipError(NetworkError):
    """Raised when an existing interface is not owned by the expected sandbox."""

    pass


class HostError(CelestoError):
    """Raised when host environment checks fail (KVM, dependencies, Firecracker)."""

    pass


class ImageError(CelestoError):
    """Raised when image operations fail (download, checksum, cache)."""

    pass


class FirecrackerAPIError(CelestoError):
    """Raised when Firecracker API calls fail."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message, {"status_code": status_code})
        self.status_code = status_code


class OperationTimeoutError(CelestoError):
    """Raised when an operation times out."""

    def __init__(
        self,
        operation: str,
        timeout_seconds: float,
        *,
        recovery_command: str | None = None,
    ) -> None:
        details = {"operation": operation, "timeout_seconds": timeout_seconds}
        if recovery_command is None:
            message = f"Operation '{operation}' timed out after {timeout_seconds}s"
        else:
            message = (
                f"{operation} timed out after {timeout_seconds}s; retry with "
                f"'{recovery_command}' to allow a brief pause."
            )
            details["recovery_command"] = recovery_command
        super().__init__(message, details)
        self.operation = operation
        self.timeout_seconds = timeout_seconds


class CommandExecutionUnavailableError(CelestoError):
    """Raised when command execution is not available for a VM profile."""

    def __init__(
        self,
        vm_id: str,
        reason: str,
        remediation: str | None = None,
    ) -> None:
        message = f"Cannot run command in VM '{vm_id}': {reason}"
        if remediation:
            message = f"{message}\n{remediation}"
        super().__init__(message, {"vm_id": vm_id, "reason": reason})
        self.vm_id = vm_id
        self.reason = reason
        self.remediation = remediation

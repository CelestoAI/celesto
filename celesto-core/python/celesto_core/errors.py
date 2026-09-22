"""Public error types raised by celesto-core wrapper modules."""

from __future__ import annotations

from typing import Any


class CelestoCoreError(Exception):
    """Base class for celesto-core library errors."""


class CoreUnavailableError(CelestoCoreError):
    """Raised when a requested native helper is not available."""


class QMPError(CelestoCoreError):
    """Raised when QEMU monitor control fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class FirecrackerAPIError(CelestoCoreError):
    """Raised when the Firecracker API returns an error response."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


__all__ = [
    "CoreUnavailableError",
    "FirecrackerAPIError",
    "QMPError",
    "CelestoCoreError",
]

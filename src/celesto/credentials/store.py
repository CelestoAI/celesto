# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""Per-computer credential-protection version kept in the host state DB.

Real values are never stored (D-09); they are re-read from their source on
every start. User secrets keep their own definitions and placeholders
(``celesto.credentials.user_secrets``).

The state managers (``cli/_sqlite.py``, ``storage/_memory.py``) implement:

- ``get_credential_protection(vm_id) -> int`` (0 = created before this release)
- ``set_credential_protection(vm_id, version) -> None``
"""

from __future__ import annotations

from typing import Any

PROTECTION_VERSION = 1
"""Credential-protection version recorded on computers created by this release.

Computers from earlier releases read as 0 and get the D-21 cleanup on their
first start.
"""


def protection_version(state: Any, sandbox_id: str) -> int:
    """Return the computer's credential-protection version (0 if unknown)."""
    getter = getattr(state, "get_credential_protection", None)
    if getter is None:
        return PROTECTION_VERSION
    return int(getter(sandbox_id))


def mark_protected(state: Any, sandbox_id: str) -> None:
    """Record that the computer runs under the current protection version."""
    setter = getattr(state, "set_credential_protection", None)
    if setter is not None:
        setter(sandbox_id, PROTECTION_VERSION)


__all__ = ["PROTECTION_VERSION", "mark_protected", "protection_version"]

# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""Per-sandbox credential state kept in the host state DB.

Only placeholders and a protection version are stored. Placeholders are not
secrets on their own (D-05): the proxy injects a real value only for the
placeholder's own sandbox and bound hosts. Real values are never stored
(D-09); they are re-read from their source on every start.

The state managers (``cli/_sqlite.py``, ``storage/_memory.py``) implement:

- ``get_credential_placeholders(vm_id) -> dict[str, str]``
- ``save_credential_placeholders(vm_id, placeholders) -> None`` (merge)
- ``get_credential_protection(vm_id) -> int`` (0 = created before this release)
- ``set_credential_protection(vm_id, version) -> None``
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

PROTECTION_VERSION = 1
"""Credential-protection version recorded on sandboxes created by this release.

Sandboxes from earlier releases read as 0 and get the D-17 cleanup on their
first start.
"""


class PlaceholderBook:
    """Get-or-create placeholders for one sandbox, saved in one write.

    Passed to the login planners (``celesto.credentials.logins``) as
    ``placeholders=``. Call :meth:`get` with a stable key and a factory; the
    factory runs only when the sandbox has no placeholder for that key yet.
    :meth:`flush` persists new placeholders.
    """

    def __init__(self, state: Any, sandbox_id: str) -> None:
        self._state = state
        self._sandbox_id = sandbox_id
        self._known: dict[str, str] = dict(_load(state, sandbox_id))
        self._new: dict[str, str] = {}

    def get(self, key: str, factory: Callable[[], str]) -> str:
        """Return the sandbox's placeholder for *key*, creating it once."""
        if key in self._known:
            return self._known[key]
        value = factory()
        self._known[key] = value
        self._new[key] = value
        return value

    def peek(self, key: str) -> str | None:
        """Return the placeholder for *key* without creating one."""
        return self._known.get(key)

    def flush(self) -> None:
        """Persist placeholders created since the last flush."""
        if self._new and self._state is not None:
            self._state.save_credential_placeholders(self._sandbox_id, dict(self._new))
        self._new.clear()


def _load(state: Any, sandbox_id: str) -> dict[str, str]:
    if state is None:
        return {}
    getter = getattr(state, "get_credential_placeholders", None)
    if getter is None:
        return {}
    return dict(getter(sandbox_id))


def protection_version(state: Any, sandbox_id: str) -> int:
    """Return the sandbox's credential-protection version (0 if unknown)."""
    getter = getattr(state, "get_credential_protection", None)
    if getter is None:
        return PROTECTION_VERSION
    return int(getter(sandbox_id))


def mark_protected(state: Any, sandbox_id: str) -> None:
    """Record that the sandbox runs under the current protection version."""
    setter = getattr(state, "set_credential_protection", None)
    if setter is not None:
        setter(sandbox_id, PROTECTION_VERSION)


__all__ = ["PROTECTION_VERSION", "PlaceholderBook", "mark_protected", "protection_version"]

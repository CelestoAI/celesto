# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""Shared types for keeping real credentials out of sandboxes.

The guest only ever sees placeholders. A per-sandbox proxy on the host swaps a
placeholder for its real value on requests to the hosts it is bound to.
See docs/designs/sandbox-credential-injection.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

HeaderForm = Literal["bearer", "raw", "basic_password", "token"]
"""How a placeholder appears in a header.

- ``bearer``: ``Bearer <placeholder>``
- ``raw``: ``<placeholder>``
- ``basic_password``: ``Basic base64(user:<placeholder>)``
- ``token``: ``token <placeholder>``, as the gh CLI sends it (D-24)
"""


@dataclass(frozen=True)
class HeaderRule:
    header: str
    """Lowercase header name, e.g. ``authorization`` or ``x-api-key``."""
    form: HeaderForm


@dataclass(frozen=True)
class Binding:
    """One placeholder the guest may send, and where its real value may go."""

    name: str
    """Credential name shown to users, e.g. ``OPENAI_API_KEY``."""
    placeholder: str
    """Exact string the guest holds. Random per sandbox."""
    hosts: tuple[str, ...]
    """Exact host names the real value may be sent to."""
    headers: tuple[HeaderRule, ...]
    source: str = ""
    """Where the real value comes from, e.g. ``env:OPENAI_API_KEY``."""


@dataclass(frozen=True)
class LocalRoute:
    """A request the proxy answers itself and never forwards."""

    host: str
    path: str
    handler: str
    """Registered handler id."""


@dataclass(frozen=True)
class GuestFile:
    """A file holding only placeholders, written into the guest."""

    path: str
    content: bytes
    mode: int = 0o600


@dataclass
class CredentialPlan:
    """Everything one sandbox start needs to protect its credentials."""

    bindings: list[Binding] = field(default_factory=list)
    local_routes: list[LocalRoute] = field(default_factory=list)
    guest_env: dict[str, str] = field(default_factory=dict)
    """Env var name -> placeholder, written to the guest's managed env."""
    guest_files: list[GuestFile] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    """User-facing warnings for credentials that were not available."""
    real_values: dict[str, str] = field(default_factory=dict, repr=False)
    """Binding name -> real value. Never sent to the guest, logged, or stored."""

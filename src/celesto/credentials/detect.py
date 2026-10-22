# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""Refuse secret-looking values on the plain environment-variable paths (D-12).

Plain env vars are copied into the sandbox, where any process can read them.
Secrets belong in host-bound secrets instead (D-11), so every plain env path
(CLI ``env set``, SDK ``env_vars``, the SDK bridge ``exec`` env) runs this one
detector first. Detection is best-effort; ``not_secret`` is the escape hatch.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Literal

from celesto.exceptions import ValidationError

Surface = Literal["cli", "python", "typescript", "typescript_no_secrets"]
"""Which interface the user is on, so the recovery names a command they can run."""

_NAME_SUFFIXES = ("_KEY", "_TOKEN", "_SECRET")
_NAME_BARE = frozenset({"KEY", "TOKEN", "SECRET", "APIKEY"})
_NAME_FRAGMENTS = ("PASSWORD", "CREDENTIAL")

# Each pattern needs a body long enough that short look-alikes such as
# ``sk-learn`` do not match. ``(?<![A-Za-z0-9])`` keeps a prefix from matching
# in the middle of another word.
_VALUE_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{16,}",
        r"(?<![A-Za-z0-9])gh[pousr]_[A-Za-z0-9]{20,}",
        r"(?<![A-Za-z0-9])github_pat_[A-Za-z0-9_]{20,}",
        r"(?<![A-Za-z0-9])xox[abposr]-[A-Za-z0-9-]{10,}",
        r"(?<![A-Za-z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Za-z0-9])",
        r"(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}",
    )
)

# Hosts for the well-known API keys (D-19), so the recovery command is complete.
KNOWN_SECRET_HOSTS: dict[str, str] = {
    "OPENAI_API_KEY": "api.openai.com",
    "ANTHROPIC_API_KEY": "api.anthropic.com",
    "OPENROUTER_API_KEY": "openrouter.ai",
    "GOOGLE_API_KEY": "generativelanguage.googleapis.com",
    "GEMINI_API_KEY": "generativelanguage.googleapis.com",
    "HF_TOKEN": "huggingface.co",
    "GITHUB_TOKEN": "api.github.com",
    "GH_TOKEN": "api.github.com",
}
_UNKNOWN_HOST = "<the API's host name>"


class SecretRefusedError(ValidationError):
    """A secret-looking value was passed where Celesto would copy it into the sandbox."""

    def __init__(self, message: str, *, name: str) -> None:
        super().__init__(message, {"name": name})
        self.name = name


def _name_looks_secret(name: str) -> bool:
    upper = name.upper()
    if upper in _NAME_BARE:
        return True
    if upper.endswith(_NAME_SUFFIXES):
        return True
    return any(fragment in upper for fragment in _NAME_FRAGMENTS)


def _value_looks_secret(value: str) -> bool:
    return any(pattern.search(value) for pattern in _VALUE_PATTERNS)


def looks_like_secret(name: str, value: str) -> bool:
    """Return whether *name*/*value* looks like a credential.

    An empty value carries nothing secret, so it is never refused.
    """
    if not value.strip():
        return False
    return _name_looks_secret(name) or _value_looks_secret(value)


def refusal_message(name: str, *, sandbox: str, surface: Surface = "cli") -> str:
    """Return the user-facing refusal for *name*, with a recovery for *surface*."""
    host = KNOWN_SECRET_HOSTS.get(name.upper(), _UNKNOWN_HOST)
    lead = f"{name} looks like a secret, so Celesto won't place it inside the computer."
    if surface == "python":
        return f'{lead} Pass secrets={{"{name}": Secret(host="{host}")}} instead.'
    if surface == "typescript_no_secrets":
        return (
            f"{lead} TypeScript computers and browser sessions can't hold secrets yet; "
            f'if it isn\'t one, pass notSecret: ["{name}"].'
        )
    if surface == "typescript":
        return (
            f'{lead} Create the computer with secrets: {{ {name}: {{ host: "{host}" }} }} instead.'
        )
    return f"{lead} Run 'celesto computer secret set {sandbox} {name} --host {host}' instead."


def check_env(
    env: Mapping[str, str],
    *,
    sandbox: str,
    not_secret: Iterable[str] = (),
    surface: Surface = "cli",
) -> None:
    """Raise :class:`SecretRefusedError` for the first secret-looking entry.

    Names listed in *not_secret* are allowed through unchanged.
    """
    allowed = set(not_secret)
    for name in sorted(env):
        if name in allowed:
            continue
        if looks_like_secret(name, env[name]):
            raise SecretRefusedError(
                refusal_message(name, sandbox=sandbox, surface=surface), name=name
            )


__all__ = [
    "KNOWN_SECRET_HOSTS",
    "SecretRefusedError",
    "Surface",
    "check_env",
    "looks_like_secret",
    "refusal_message",
]

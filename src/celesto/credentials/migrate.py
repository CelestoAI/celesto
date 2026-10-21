# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""Remove keys the old presets copied into a computer (D-21).

Computers created by a preset before this release (their stored record
still carries ``preset``) may hold real keys: API keys in the guest's env
file, login and token files, ``~/.git-credentials``, gh's token file, and
``~/.ssh`` private keys. On their first start after upgrade,
:func:`migrate_on_start` deletes exactly that fixed list. Nothing replaces
them: no proxy binding exists for them any more, so users re-add what they
need with ``celesto computer secret set``. The stored credential-protection
version makes this run once.
"""

from __future__ import annotations

import logging
import shlex
from typing import Any

from celesto.credentials.store import mark_protected, protection_version
from celesto.env import ENV_FILE
from celesto.exceptions import CelestoError

logger = logging.getLogger(__name__)

# Env vars the old presets copied into the guest.
COPIED_ENV_VARS: tuple[str, ...] = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENROUTER_API_KEY",
    "GOOGLE_API_KEY",
    "GEMINI_API_KEY",
    "HF_TOKEN",
    "OPENCLAW_GATEWAY_TOKEN",
    "OPENCLAW_GATEWAY_PASSWORD",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
)

# Login and token files the old presets copied in.
COPIED_SECRET_FILES: tuple[str, ...] = (
    "/root/.codex/auth.json",
    "/root/.claude/.credentials.json",
    "/root/.local/share/opencode/auth.json",
    "/root/.pi/agent/auth.json",
    "/root/.hermes/.env",
    "/root/.hermes/auth.json",
    "/root/.git-credentials",
    "/root/.config/gh/hosts.yml",
)

_MARKER = "CELESTO_REMOVED "
_ENV_LINE = "^export (" + "|".join(COPIED_ENV_VARS) + ")="


def cleanup_script() -> str:
    """Return the guest shell script that deletes copied secrets.

    Prints one ``CELESTO_REMOVED <path>`` line per file it deleted. Private
    keys are found by content under ``/root/.ssh`` (any name), so a key the
    user renamed is still removed; ``authorized_keys`` and public keys stay.
    """
    files = " ".join(shlex.quote(path) for path in COPIED_SECRET_FILES)
    return "\n".join(
        [
            "set -u",
            f"for f in {files}; do",
            '  if [ -e "$f" ]; then rm -f -- "$f" && echo "' + _MARKER + '$f"; fi',
            "done",
            "if [ -d /root/.ssh ]; then",
            "  find /root/.ssh -type f ! -name 'authorized_keys*' ! -name '*.pub' "
            "-exec grep -l -e 'PRIVATE KEY-----' {} + 2>/dev/null | while read -r f; do",
            '    rm -f -- "$f" && echo "' + _MARKER + '$f"',
            "  done",
            "fi",
            # Older guests kept forwarded keys in the login-profile env file.
            f"env_file={shlex.quote(ENV_FILE)}",
            'if [ -f "$env_file" ]; then',
            f'  if grep -q -E {shlex.quote(_ENV_LINE)} "$env_file"; then',
            f'    grep -v -E {shlex.quote(_ENV_LINE)} "$env_file" > "$env_file.tmp" || true',
            '    mv -f -- "$env_file.tmp" "$env_file" && echo "' + _MARKER + '$env_file"',
            "  fi",
            "fi",
            "exit 0",
        ]
    )


def migration_message(sandbox_id: str) -> str:
    """Return the one-time D-21 message for *sandbox_id*."""
    return (
        f"Celesto removed copied keys from {sandbox_id}. If an agent may have copied"
        " them elsewhere in the computer, rotate them or recreate the computer."
    )


def needs_migration(state: Any, sandbox_id: str) -> bool:
    """Return True when the computer was created before credential protection."""
    from celesto.credentials.store import PROTECTION_VERSION

    return protection_version(state, sandbox_id) < PROTECTION_VERSION


def migrate_if_needed(vm: Any, *, state: Any) -> str | None:
    """Delete the keys the old presets copied into a running computer.

    *vm* is a running :class:`celesto.Celesto` whose guest accepts commands.
    Returns the one-time message when anything was removed, else None.
    Marks the computer as protected either way, so this runs once.
    """
    sandbox_id = vm.vm_id
    if not needs_migration(state, sandbox_id):
        return None
    removed_env = _remove_env(vm)
    result = vm.run(f"bash -c {shlex.quote(cleanup_script())}", timeout=60)
    if not getattr(result, "ok", False):
        raise CelestoError(
            f"Celesto couldn't remove old keys from {sandbox_id}. Run"
            f" 'celesto computer stop {sandbox_id}' and 'celesto computer start"
            f" {sandbox_id}' to try again.",
            {"vm_id": sandbox_id, "exit_code": getattr(result, "exit_code", None)},
        )
    removed_files = [
        line[len(_MARKER) :]
        for line in (getattr(result, "stdout", "") or "").splitlines()
        if line.startswith(_MARKER)
    ]
    logger.info(
        "Credential cleanup for %s: %d env var(s), %d file(s)",
        sandbox_id,
        len(removed_env),
        len(removed_files),
    )
    mark_protected(state, sandbox_id)
    if removed_env or removed_files:
        return migration_message(sandbox_id)
    return None


def migrate_on_start(vm: Any) -> str | None:
    """Run :func:`migrate_if_needed` for a just-started computer, when it applies.

    Only computers made by a preset, on Linux guests that accept commands,
    had keys copied in. Others are just marked protected. A failed cleanup is
    raised as :class:`CelestoError` and leaves the computer unmarked, so the
    next start tries again.
    """
    state = vm._sdk.state
    if not needs_migration(state, vm.vm_id):
        return None
    config = vm.info.config
    os_name = str(getattr(getattr(config, "guest_os", None), "value", "linux"))
    if not config.preset or os_name in {"macos", "windows"} or not vm.can_run_commands():
        mark_protected(state, vm.vm_id)
        return None
    return migrate_if_needed(vm, state=state)


def _remove_env(vm: Any) -> list[str]:
    """Remove copied env vars from the guest; return only their names."""
    removed = vm.unset_env_vars(list(COPIED_ENV_VARS))
    # The removed mapping holds the old (real) values; keep names only.
    return sorted(removed)


__all__ = [
    "COPIED_ENV_VARS",
    "COPIED_SECRET_FILES",
    "cleanup_script",
    "migrate_if_needed",
    "migrate_on_start",
    "migration_message",
    "needs_migration",
]

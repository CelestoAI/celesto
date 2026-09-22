"""Compatibility helpers for installations created before the Celesto rename.

Celesto is the canonical name for configuration and on-disk state. These
helpers only read retired SmolVM locations; new state is always Celesto-named.
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path


def apply_legacy_environment_aliases() -> None:
    """Map an unset ``CELESTO_*`` setting to its deprecated predecessor."""
    for name, value in tuple(os.environ.items()):
        if not name.startswith("SMOLVM_"):
            continue
        canonical = f"CELESTO_{name.removeprefix('SMOLVM_')}"
        if canonical in os.environ:
            continue
        os.environ[canonical] = value
        warnings.warn(
            f"{name} is deprecated; use {canonical} instead.",
            DeprecationWarning,
            stacklevel=3,
        )


def existing_legacy_path(canonical: Path, legacy: Path) -> Path:
    """Use existing legacy state until a canonical location is created."""
    return canonical if canonical.exists() or not legacy.exists() else legacy

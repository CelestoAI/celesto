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

"""Results, names and messages for forking a sandbox (internal).

A fork copies one sandbox (the source) into new, independent sandboxes (the
children). The orchestration lives in :class:`celesto.facade.Celesto`
(``_fork_many``), because the guest flush runs through the facade's control
channel. This module holds the parts that don't need a running sandbox: the
result types, the child names, the identity check, and every user-facing
message (decision log D1b, ``docs/designs/sandbox-fork-decisions.md``), so
the CLI and SDK can show exactly the same words.

Only :class:`ForkBatch` and :class:`ForkResult` are public (exported from
``celesto``); everything else here is internal.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from celesto.guest_identity import GuestIdentityReport
from celesto.types import VMIdentity, VMState

if TYPE_CHECKING:
    from celesto.facade import Celesto

MAX_FORK_COUNT = 10
DEFAULT_FORK_PARALLEL = 4

# Same rule as sandbox names (``VMConfig.vm_id``).
_SANDBOX_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}[a-z0-9]$|^[a-z0-9]$")
_SANDBOX_NAME_LIMIT = 64
# Generations are snapshots named ``fork-<source>-<unix time>-<random>``.
GENERATION_PREFIX = "fork-"


@dataclass(frozen=True, slots=True)
class ForkResult:
    """What happened to one requested child.

    Attributes:
        name: The child's sandbox name.
        ok: Whether the child was created, started and confirmed its own
            identity.
        sandbox: The started child when ``ok``; ``None`` otherwise. A failed
            child is removed.
        error: Why the child failed, in the words the CLI shows; ``None``
            when ``ok``.
    """

    name: str
    ok: bool
    sandbox: Celesto | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class ForkBatch:
    """The outcome of one fork request.

    Attributes:
        children: One result per requested child, in name order.
        warnings: Problems that did not fail the fork, such as the source
            staying paused (D8).
        source_state: The source's state after the fork, or None if the source
            was deleted while the fork finished.
    """

    children: tuple[ForkResult, ...]
    warnings: tuple[str, ...]
    source_state: VMState | None


# ----------------------------------------------------------------------
# Messages (D1b). Numbers match the decision log.
# ----------------------------------------------------------------------


def paused_message(source: str) -> str:
    """1. The source is paused (D7)."""
    return f"Sandbox '{source}' is paused. Run 'celesto sandbox resume {source}', then fork again."


def error_state_message(source: str) -> str:
    """2. The source is in an error state (D7)."""
    return (
        f"Sandbox '{source}' is in an error state and can't be forked. "
        f"Run 'celesto sandbox logs {source}' to see what went wrong."
    )


def older_image_message(source: str) -> str:
    """3. The source was created from an image without instance IDs (D17)."""
    return (
        f"Sandbox '{source}' was created from an older image and can't be forked. "
        "Run 'celesto image pull --all', then create a new sandbox with "
        "'celesto sandbox create' and fork that one."
    )


def cloud_message() -> str:
    """7. The source is a cloud sandbox (D4)."""
    return (
        "Fork works only on sandboxes on this machine for now. "
        "Run 'celesto sandbox create --local' to create one."
    )


def count_message(source: str, count: int) -> str:
    """8. The child count is outside 1 to 10 (D23)."""
    suggested = 1 if count < 1 else MAX_FORK_COUNT
    return (
        f"You can fork 1 to {MAX_FORK_COUNT} sandboxes at a time; you asked for {count}. "
        f"Run 'celesto sandbox fork {source} --count {suggested}'."
    )


def name_taken_message(name: str) -> str:
    """9. A child name is taken (D23, D26)."""
    return (
        f"A sandbox named '{name}' already exists. Choose another name with '--name', "
        f"or run 'celesto sandbox delete {name}'."
    )


def disk_space_message(source: str, count: int, needed_bytes: int, free_bytes: int) -> str:
    """10. Not enough disk space for the generation and every child (D23)."""
    times = "once" if count == 1 else f"{count} times"
    return (
        f"Forking '{source}' {times} needs about {_gigabytes(needed_bytes)}, but only "
        f"{_gigabytes(free_bytes)} is free. Free up space or use a smaller '--count'."
    )


def ports_message(count: int) -> str:
    """11. Not enough free ports for every child (D23)."""
    sandboxes = "1 new sandbox" if count == 1 else f"{count} new sandboxes"
    return (
        f"Not enough free ports for {sandboxes}. "
        "Run 'celesto sandbox list' to find sandboxes you can delete."
    )


def flush_failed_message(source: str) -> str:
    """12. The guest did not answer the flush, or the identity read (D5)."""
    return (
        f"Sandbox '{source}' didn't respond when saving its files. "
        f"Run 'celesto sandbox stop {source}', then fork again."
    )


def boot_timeout_message(child: str, boot_timeout: float) -> str:
    """13. A child did not start in time; it was removed."""
    return (
        f"Sandbox '{child}' didn't start within {_seconds(boot_timeout)} seconds and was "
        f"removed. Run the fork again with '--boot-timeout {_seconds(boot_timeout * 2)}'."
    )


def identity_not_confirmed_message(child: str) -> str:
    """14. A child could not confirm its own identity; it was removed (D18)."""
    return (
        f"Sandbox '{child}' couldn't confirm it has its own identity and was removed. "
        "Run the fork again."
    )


def child_failed_message(child: str) -> str:
    """A child failed for another reason; it was removed."""
    return f"Sandbox '{child}' couldn't be created and was removed. Run the fork again."


def stayed_paused_message(source: str) -> str:
    """15. Warning: the source stayed paused after the copy (D8)."""
    return (
        f"Sandbox '{source}' stayed paused after the fork. "
        f"Run 'celesto sandbox resume {source}' to continue it."
    )


def live_copy_failed_message(source: str) -> str:
    """16. QEMU couldn't copy the running source without pausing it (D5)."""
    return (
        f"Sandbox '{source}' couldn't be copied while running. "
        f"Run 'celesto sandbox stop {source}', then fork again."
    )


def first_start_message(source: str) -> str:
    """17. The source has no recorded identity yet and isn't running (D17, D18)."""
    return (
        f"Sandbox '{source}' hasn't finished its first start, so it can't be forked yet. "
        f"Run 'celesto sandbox start {source}', then fork again."
    )


def pausing_notice(source: str) -> str:
    """Notice while a Firecracker source is paused for the copy (D9)."""
    return f"Pausing {source} while its files are copied…"


def waiting_notice(source: str) -> str:
    """Notice while the fork waits for a snapshot or fork of the source (D6)."""
    return f"Waiting for the current snapshot or fork of {source} to finish…"


def invalid_name_message(name: str) -> str:
    """A requested child name can't be a sandbox name."""
    return (
        f"'{name}' can't be used as a sandbox name. Use up to 64 lowercase letters, "
        "numbers, hyphens or underscores, starting and ending with a letter or number."
    )


def name_too_long_message(source: str) -> str:
    """Numbered child names would exceed the sandbox name limit."""
    return (
        f"Sandbox '{source}' has a name too long to number its forks. "
        "Choose a shorter name with '--name'."
    )


def requested_name_too_long_message(name: str, count: int) -> str:
    """A valid requested name is too long to add ``-1`` to ``-N`` to it."""
    longest = _SANDBOX_NAME_LIMIT - len(f"-{count}")
    return (
        f"'{name}' is too long to number {count} forks. "
        f"Choose a name of up to {longest} characters with '--name'."
    )


def _gigabytes(size: int) -> str:
    return f"{size / 1e9:.1f} GB"


def _seconds(value: float) -> str:
    return f"{value:g}"


# ----------------------------------------------------------------------
# Names and identity
# ----------------------------------------------------------------------


class ForkNameError(ValueError):
    """A child name can't be used; ``str()`` is the user-facing message."""


def child_names(source: str, count: int, name: str | None, taken: Iterable[str]) -> list[str]:
    """Return the names for *count* children (D26).

    Without *name*, children continue the numbering after the source's
    name: ``sbx-einstein-1``, ``sbx-einstein-2``, then ``-3`` on the next
    fork, skipping numbers that are taken. With *name*, one child takes
    exactly *name* and several take ``name-1`` to ``name-N``; a taken name
    is refused rather than skipped, so a retried request can't make extra
    children (D25).

    Args:
        source: The source sandbox's name.
        count: How many children, already checked to be 1 to 10.
        name: The requested name, if any.
        taken: Names that can't be used: existing sandboxes and saved disks.

    Raises:
        ForkNameError: If a requested name is taken, isn't a valid name, or
            is too long to number the children.
    """
    used = set(taken)
    if name is not None:
        names = [name] if count == 1 else [f"{name}-{index}" for index in range(1, count + 1)]
        if not _SANDBOX_NAME.fullmatch(name):
            raise ForkNameError(invalid_name_message(name))
        for candidate in names:
            if not _SANDBOX_NAME.fullmatch(candidate):
                # The name is valid, so only the added number makes it too long.
                raise ForkNameError(requested_name_too_long_message(name, count))
        for candidate in names:
            if candidate in used:
                raise ForkNameError(name_taken_message(candidate))
        return names

    numbered = re.compile(rf"^{re.escape(source)}-(\d+)$")
    highest = max(
        (int(match.group(1)) for item in used if (match := numbered.fullmatch(item))),
        default=0,
    )
    names = []
    number = highest + 1
    while len(names) < count:
        candidate = f"{source}-{number}"
        if not _SANDBOX_NAME.fullmatch(candidate):
            raise ForkNameError(name_too_long_message(source))
        if candidate not in used:
            names.append(candidate)
        number += 1
    return names


def identity_confirmed(
    report: GuestIdentityReport | None,
    *,
    instance_id: str | None,
    source: VMIdentity,
) -> bool:
    """Whether a child proved it has its own identity (D18).

    The child must report the new instance ID it was booted with, and both
    its SSH host key fingerprint and machine ID must differ from the
    source's *recorded* identity. Missing values never pass.
    """
    if report is None or not report.supports_instance_id or instance_id is None:
        return False
    if report.instance_id != instance_id:
        return False
    if report.ssh_host_key_fingerprint is None or report.machine_id is None:
        return False
    return (
        report.ssh_host_key_fingerprint != source.ssh_host_key_fingerprint
        and report.machine_id != source.machine_id
    )

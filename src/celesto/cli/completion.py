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

"""One-shot installation of shell tab-completion for the celesto CLI.

fish autoloads per-command completion files from its completions
directory, so a single file write is enough there. bash and zsh do have
autoload mechanisms too (bash-completion's drop-in directory, zsh's
``fpath``), but both only work when the machine has them set up, so for
a setup that works everywhere we write the script under
``~/.celesto/completions`` and manage one marker-tagged ``source`` line
in the shell's startup file instead.
"""

from __future__ import annotations

import os
import platform
import shlex
from contextlib import suppress
from pathlib import Path

from celesto.cli.output import console_stdout, render_error

# Trailing tag on the rc line this tool manages. Install looks for this
# marker to find (and replace) its own line without touching lines the
# user wrote themselves.
_MARKER = "# celesto tab completion"

# zsh's `compdef` only exists after `compinit` has run; a minimal .zshrc
# never runs it, so the installed script initializes completion first.
_ZSH_COMPINIT_GUARD = (
    "# Ensure zsh's completion system is initialized before compdef is used.\n"
    "if ! command -v compdef > /dev/null 2>&1; then\n"
    "  autoload -Uz compinit\n"
    "  compinit\n"
    "fi\n"
    "\n"
)


def _user_home() -> Path:
    """Return the invoking user's home, resolving through sudo.

    Under ``sudo`` a bare ``Path.home()`` is root's home, which would
    install completion where the real user's shell never sees it.
    """
    from celesto.vm import _get_sudo_user_info

    sudo_user = _get_sudo_user_info()
    if sudo_user is not None:
        return Path(sudo_user.pw_dir)
    return Path.home()


def _with_ancestors_below(path: Path, stop: Path) -> list[Path]:
    """Return ``path`` plus every ancestor strictly below ``stop``.

    ``mkdir(parents=True)`` may create a whole chain of directories (a
    custom ``XDG_CONFIG_HOME`` or ``ZDOTDIR`` several levels deep), so
    ownership fixes must cover the full chain, not a fixed number of
    parent levels. For a path outside ``stop`` only the path itself is
    returned.
    """
    targets = [path]
    current = path.parent
    while current != stop and current != current.parent and current.is_relative_to(stop):
        targets.append(current)
        current = current.parent
    return targets


def _chown_to_sudo_user(paths: list[Path]) -> None:
    """Give files created while running under sudo back to the real user."""
    from celesto.vm import _get_sudo_user_info

    sudo_user = _get_sudo_user_info()
    if sudo_user is None:
        return
    for path in paths:
        with suppress(OSError):
            os.chown(path, sudo_user.pw_uid, sudo_user.pw_gid)


def _rc_path(shell: str) -> Path:
    """Return the shell startup file completion should be sourced from."""
    home = _user_home()
    if shell == "zsh":
        zdotdir = os.environ.get("ZDOTDIR")
        base = Path(zdotdir).expanduser() if zdotdir else home
        return base / ".zshrc"
    if platform.system() == "Darwin":
        # macOS terminals start login shells, which read ~/.bash_profile
        # (never ~/.bashrc). Prefer an existing file, else create the
        # login-shell one.
        for name in (".bash_profile", ".bashrc"):
            candidate = home / name
            if candidate.exists():
                return candidate
        return home / ".bash_profile"
    return home / ".bashrc"


def _fish_completions_dir() -> Path:
    """Return fish's user completions directory (autoloaded by fish)."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    config_home = Path(xdg).expanduser() if xdg else _user_home() / ".config"
    return config_home / "fish" / "completions"


def _read_rc(rc_path: Path) -> str:
    """Read a startup file, round-tripping non-UTF-8 bytes losslessly."""
    if not rc_path.exists():
        return ""
    return rc_path.read_text(encoding="utf-8", errors="surrogateescape")


def _write_rc(rc_path: Path, lines: list[str]) -> None:
    """Write a startup file back, preserving undecodable bytes."""
    while lines and lines[-1] == "":
        lines = lines[:-1]
    text = "\n".join(lines)
    if text and not text.endswith("\n"):
        text += "\n"
    rc_path.write_text(text, encoding="utf-8", errors="surrogateescape")


def _install_rc_line(shell: str, rc_path: Path, script_path: Path) -> str:
    """Ensure exactly one active managed source line in ``rc_path``.

    Returns a short human message describing what happened. Marker-tagged
    lines from previous installs (stale paths, duplicates, commented-out
    copies) are replaced by one fresh line; lines the user wrote
    themselves are never modified.
    """
    managed_line = f"source {shlex.quote(str(script_path))}  {_MARKER}"
    rc_content = _read_rc(rc_path)
    lines = rc_content.split("\n") if rc_content else []

    kept = [line for line in lines if _MARKER not in line]
    marker_lines = [line for line in lines if _MARKER in line]
    user_written = any(
        f"completions/celesto.{shell}" in line and not line.lstrip().startswith("#")
        for line in kept
    )

    # Exact-list comparison so duplicated copies of the current line still
    # fall through to the rewrite below and get collapsed to one.
    if marker_lines == [managed_line]:
        return (
            f"Tab completion for {shell} is already set up in '{rc_path}'. "
            "Open a new shell if it isn't active."
        )

    if user_written:
        if marker_lines:
            # The user's own line loads the script; ours are redundant.
            _write_rc(rc_path, kept)
        return (
            f"Tab completion for {shell} is already loaded by a line you added "
            f"to '{rc_path}'. Open a new shell if it isn't active."
        )

    if not marker_lines:
        # Nothing of ours in the file: append without rewriting it.
        rc_path.parent.mkdir(parents=True, exist_ok=True)
        with rc_path.open("a", encoding="utf-8", errors="surrogateescape") as handle:
            if rc_content and not rc_content.endswith("\n"):
                handle.write("\n")
            handle.write(f"{managed_line}\n")
        return (
            f"Tab completion for {shell} is set up: added one line to '{rc_path}'. "
            "Open a new shell to use it."
        )

    # Stale, duplicated, or commented-out managed lines: replace them all
    # with one fresh line.
    _write_rc(rc_path, [*kept, managed_line])
    return (
        f"Tab completion for {shell} is set up: updated the celesto line in "
        f"'{rc_path}'. Open a new shell to use it."
    )


def run_completion_install(shell: str, script: str) -> int:
    """Install the completion ``script`` for ``shell`` so new shells load it.

    Idempotent: re-running refreshes the script file and repairs the
    managed startup-file line without duplicating it.
    """
    console = console_stdout()
    try:
        home = _user_home()
        if shell == "fish":
            target = _fish_completions_dir() / "celesto.fish"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(script, encoding="utf-8")
            _chown_to_sudo_user(_with_ancestors_below(target, home))
            console.print(
                f"Tab completion for fish is set up at '{target}'. Open a new shell to use it."
            )
            return 0

        if shell == "zsh":
            script = _ZSH_COMPINIT_GUARD + script

        script_path = home / ".celesto" / "completions" / f"celesto.{shell}"
        script_path.parent.mkdir(parents=True, exist_ok=True)
        script_path.write_text(script, encoding="utf-8")

        rc_path = _rc_path(shell)
        rc_existed = rc_path.exists()
        message = _install_rc_line(shell, rc_path, script_path)

        chown_targets = _with_ancestors_below(script_path, home)
        if not rc_existed and rc_path.exists():
            chown_targets.extend(_with_ancestors_below(rc_path, home))
        _chown_to_sudo_user(chown_targets)

        console.print(message)
        return 0
    except (OSError, UnicodeError) as exc:
        detail = str(exc)
        if isinstance(exc, OSError) and exc.strerror:
            detail = exc.strerror.lower()
            if exc.filename:
                detail += f" for '{exc.filename}'"
        render_error(
            f"Could not set up tab completion: {detail}. "
            f"Run 'celesto completion {shell}' and add the printed script "
            "to your shell yourself."
        )
        return 1

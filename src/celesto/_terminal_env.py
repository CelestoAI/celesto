"""Terminal compatibility for minimal guest images."""

import os


def guest_terminal_type() -> str:
    """Use the xterm baseline for terminals absent from our guest terminfo.

    Direct OpenSSH execution bypasses Ghostty's and Kitty's shell wrappers
    that would normally install their remote terminal definitions. Without
    those definitions Bash disables bracketed paste and degrades editing.
    Keep other terminal types (including tmux/screen and dumb) unchanged.
    """
    term = os.environ.get("TERM") or "xterm-256color"
    if term in {"xterm-ghostty", "xterm-kitty"}:
        return "xterm-256color"
    return term

"""Keep the relative links in the documentation pointing at real files.

The ``tests/`` tree was reorganised into per-area subdirectories while the
"Implementation notes" footers kept pointing at the old flat ``tests/test_*.py``
paths, so every one of those links 404s both on GitHub and on the rendered docs
site. No CI job inspects markdown links, so the rot went unnoticed.

This is a repository-level check rather than a per-area behaviour test, so it
lives beside the other repository-level guard in ``tests/test_release_workflows.py``
instead of inside one of the ``tests/`` subdirectories.
"""

import re
from pathlib import Path

_REPOSITORY = Path(__file__).resolve().parents[1]
_DOCS = _REPOSITORY / "docs"

# Inline links and images, e.g. [label](target). The docs use no reference-style
# links, and inline scanning keeps this fast enough for every test run.
_LINK = re.compile(r"\[[^\]]*\]\(\s*(<[^>]*>|[^)\s]+)")

# Targets the repository does not own, so they cannot be resolved on disk.
_EXTERNAL = ("http://", "https://", "mailto:")


def _relative_targets(document: Path) -> list[tuple[int, str]]:
    """Return the ``(line, target)`` of every repo-relative link in ``document``."""
    text = document.read_text(encoding="utf-8")
    targets = []
    for match in _LINK.finditer(text):
        target = match.group(1)
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        if target.lower().startswith(_EXTERNAL):
            continue
        # Strip the "#anchor" and "?query" parts. A pure anchor leaves nothing to check.
        path = target.split("#", 1)[0].split("?", 1)[0]
        if path:
            targets.append((text.count("\n", 0, match.start()) + 1, path))
    return targets


def test_documentation_relative_links_resolve() -> None:
    broken = [
        f"{document.relative_to(_REPOSITORY).as_posix()}:{line}: {target}"
        for document in sorted(_DOCS.rglob("*.md"))
        for line, target in _relative_targets(document)
        if not (document.parent / target).exists()
    ]

    assert not broken, "Documentation links point at missing files:\n" + "\n".join(broken)

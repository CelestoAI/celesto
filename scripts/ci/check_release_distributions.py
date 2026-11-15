"""Check release artifact names before uploading them to PyPI."""

import tomllib
from pathlib import Path

project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]
version = project["version"]
dist = Path("dist")
actual = (
    {path.name for path in dist.iterdir() if path.is_file() and not path.name.startswith(".")}
    if dist.is_dir()
    else set()
)
expected = {
    f"celesto-{version}-py3-none-any.whl",
    f"celesto-{version}.tar.gz",
}

if actual != expected:
    raise SystemExit(
        f"pyproject.toml version {version!r} does not match built files {sorted(actual)!r}; "
        f"expected {sorted(expected)!r}. Use the built version in pyproject.toml and "
        "the matching release tag, then rebuild before publishing."
    )

print(f"Release package filenames match pyproject.toml version {version}: {sorted(actual)!r}.")

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

"""Celesto image-cache pruning — remove stale version directories."""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

from celesto import __version__
from celesto.cli.output import console_stdout, emit_json
from celesto.images.manager import resolve_image_dir


def _size_on_disk(st: os.stat_result) -> int:
    """Bytes a file actually occupies — sparse-aware where the OS reports it."""
    blocks = getattr(st, "st_blocks", None)
    return blocks * 512 if blocks is not None else st.st_size


def _total_size(path: Path) -> int:
    """Recursively sum on-disk usage under *path*.

    Uses allocated blocks rather than apparent size so sparse rootfs
    images (deliberately decompressed with holes) report what deleting
    them would actually free. Tolerates files vanishing mid-walk.
    """
    total = 0
    try:
        if path.is_file():
            return _size_on_disk(path.stat())
        for f in path.rglob("*"):
            try:
                if f.is_file():
                    total += _size_on_disk(f.stat())
            except OSError:
                continue
    except OSError:
        pass
    return total


def _format_bytes(n: int) -> str:
    value = float(n)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if abs(value) < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TiB"


# One version fragment shared by every parser of cache-dir names (this
# module and cli/image.py). Covers plain semver, compact pre-releases
# ("0.0.14a0"), and dotted suffixes actually shipped ("0.0.24.post3").
_VERSION_PATTERN = r"\d+\.\d+\.\d+[a-z0-9]*(?:\.[a-z0-9]+)*"

_VERSION_RE = re.compile(rf"-v({_VERSION_PATTERN})-")


def find_stale_caches(
    cache_dir: Path | None = None,
    current_version: str = __version__,
) -> list[Path]:
    """Return cache directories that belong to older Celesto versions.

    Directories whose name contains ``-v<version>-`` where ``<version>``
    differs from ``current_version`` are considered stale. Unversioned
    directories (e.g. ``s3/``) and the current version are left alone.
    """
    root = resolve_image_dir(cache_dir)
    if not root.is_dir():
        return []
    stale: list[Path] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        m = _VERSION_RE.search(child.name)
        if m and m.group(1) != current_version:
            stale.append(child)
    return stale


def run_prune(
    *,
    dry_run: bool = False,
    json_output: bool = False,
    cache_dir: str | None = None,
    command_name: str = "prune",
) -> int:
    """Execute ``celesto prune`` (also exposed as ``celesto image prune``)."""
    cache_root = Path(cache_dir) if cache_dir else None
    stale = find_stale_caches(cache_dir=cache_root)

    if not stale:
        if json_output:
            emit_json(command_name, 0, data={"removed": [], "freed_bytes": 0})
        else:
            console = console_stdout()
            console.print("Nothing to prune — cache is clean.")
        return 0

    entries: list[dict[str, str | int]] = []
    total_bytes = 0
    for path in stale:
        size = _total_size(path)
        total_bytes += size
        entries.append({"path": str(path), "size_bytes": size})

    if dry_run:
        if json_output:
            emit_json(
                command_name,
                0,
                data={
                    "dry_run": True,
                    "would_remove": entries,
                    "would_free_bytes": total_bytes,
                },
            )
        else:
            console = console_stdout()
            console.print(
                f"[bold]Would remove {len(entries)} stale cache(s) "
                f"({_format_bytes(total_bytes)}):[/bold]"
            )
            for e in entries:
                size_bytes = e["size_bytes"]
                assert isinstance(size_bytes, int)
                console.print(f"  {e['path']}  ({_format_bytes(size_bytes)})")
        return 0

    for path in stale:
        # A stale-named entry may be a symlink; remove the link itself
        # rather than following it (rmtree refuses symlinks anyway).
        if path.is_symlink():
            path.unlink()
        else:
            shutil.rmtree(path)

    if json_output:
        emit_json(
            command_name,
            0,
            data={
                "removed": [str(p) for p in stale],
                "freed_bytes": total_bytes,
            },
        )
    else:
        console = console_stdout()
        console.print(f"Removed {len(stale)} stale cache(s), freed {_format_bytes(total_bytes)}.")
    return 0

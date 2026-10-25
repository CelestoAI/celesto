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

"""``celesto image save`` / ``celesto image load`` — move images between machines.

The archive is a plain tar containing exactly one ``manifest.json``
(schema_version 1) that describes every ``files/<path>`` member: its
encoding (``raw`` bytes or a ``zstd`` stream), its decoded size, and the
SHA-256 digest of the stored bytes, all verified on load. Member names
never carry encoding suffixes, so sibling files like ``x`` and ``x.zst``
can't collide. Large files travel as zstd streams so sparse
rootfs images stay small; files that are already ``.zst`` always travel
raw (never re-compressed), so their manifest digest is also the digest of
the installed file. The ``rootfs.ext4.from-sha256`` sidecar is never
saved, and the decompressed ``rootfs.ext4`` is omitted whenever the
compressed ``rootfs.ext4.zst`` is present; load recreates both from the
digest of the ``.zst`` it installed, byte-compatible with what
``ensure_published_image`` expects, so an archive can never assert which
pinned bytes a rootfs came from.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shlex
import shutil
import tarfile
import tempfile
import unicodedata
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypedDict

from celesto import __version__
from celesto.cli.image import (
    _IMAGE_DIR_NAME_RE,
    _brief_error,
    _entry_kind,
    _expand_custom_entries,
    _fail,
    _non_default_dir_warnings,
    _normalize_rm_name,
    _resolve_entries,
    _valid_entry_name,
)
from celesto.cli.output import console_stdout, emit_success
from celesto.cli.prune import _format_bytes, _total_size
from celesto.images.manager import resolve_image_dir
from celesto.images.published import DECOMPRESSED_ROOTFS_SIDECAR_SUFFIX

_SCHEMA_VERSION = 1
_COPY_CHUNK = 1024 * 1024
_MANIFEST_MEMBER = "manifest.json"
# Real manifests are a few KB; anything huge is not one of our archives.
_MANIFEST_SIZE_CAP = 10 * 1024 * 1024

# The decompressed rootfs and its sidecar are recreated on load from the
# compressed wire file, so archives never carry them alongside it.
_DECOMPRESSED_ROOTFS = "rootfs.ext4"
_ROOTFS_ZST = "rootfs.ext4.zst"
_ROOTFS_SIDECAR = _DECOMPRESSED_ROOTFS + DECOMPRESSED_ROOTFS_SIDECAR_SUFFIX
# Builders hold this lock while rewriting an entry (see builder.py).
_BUILD_LOCK = ".build.lock"


class _EntryChangedError(Exception):
    """A file in the image shrank while it was being archived."""


class ImageSavePayload(TypedDict):
    name: str
    archive_path: str
    archive_size_bytes: int
    files: int
    excluded_decompressed_rootfs: bool
    warnings: list[str]


class ImageLoadPayload(TypedDict):
    name: str
    path: str
    size_bytes: int
    files: int
    warnings: list[str]


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(_COPY_CHUNK):
            hasher.update(chunk)
    return hasher.hexdigest()


class _HashingReader:
    """Wrap a binary file so a digest covers exactly the bytes tar reads."""

    def __init__(self, fileobj: io.BufferedReader, hasher: hashlib._Hash) -> None:
        self._fileobj = fileobj
        self._hasher = hasher

    def read(self, size: int = -1) -> bytes:
        chunk = self._fileobj.read(size)
        self._hasher.update(chunk)
        return chunk


def _canonical_path(path: str) -> str:
    """Key under which a declared path is compared with reserved names.

    The image cache may live on a case-insensitive filesystem (macOS by
    default), where ``rootfs.ext4.ZST`` lands as ``rootfs.ext4.zst``, so
    every name rule and collision check works on this key, not the spelling.
    """
    return unicodedata.normalize("NFC", path).casefold()


def _valid_relative_file_path(path: str) -> bool:
    if not path or path.startswith("/") or "\\" in path:
        return False
    return all(segment not in {"", ".", ".."} for segment in path.split("/"))


def _remove_existing_entry(path: Path) -> None:
    """Remove a cache entry in whatever form it exists (dir, link, file)."""
    if path.is_symlink() or path.is_file():
        path.unlink()
    else:
        shutil.rmtree(path)


def run_image_save(
    *,
    name: str,
    output: str,
    image_dir: str | None = None,
    json_output: bool = False,
    command_name: str = "image.save",
) -> int:
    """Execute ``celesto image save``."""
    import fcntl

    import zstandard

    root = resolve_image_dir(image_dir)
    requested = _normalize_rm_name(name, root)
    out_path = Path(output)

    if not _valid_entry_name(requested):
        return _fail(
            command_name,
            f"'{name}' is not a cached image name.",
            json_output=json_output,
            code="invalid_input",
            recovery="Run 'celesto image list' to see cached images.",
            exit_code=2,
        )
    if out_path.is_dir():
        return _fail(
            command_name,
            f"'{out_path}' is a folder; -o needs a file name.",
            json_output=json_output,
            code="invalid_input",
            recovery=f"Retry with a file path, e.g. 'celesto image save {requested} "
            f"-o {shlex.quote(str(out_path / (requested.replace('/', '-') + '.tar')))}'.",
            exit_code=2,
        )

    retry_command = f"celesto image save {requested} -o {shlex.quote(str(out_path))}"
    try:
        matches = _expand_custom_entries(_resolve_entries(requested, root), root)
    except ValueError as exc:
        return _fail(
            command_name,
            str(exc),
            json_output=json_output,
            code="invalid_input",
            recovery="Retry with one of the full names above.",
            exit_code=2,
        )
    except OSError as exc:
        return _fail(
            command_name,
            f"Could not read the image folder '{root}': {_brief_error(exc)}",
            json_output=json_output,
            recovery=f"Fix the folder's permissions, then retry '{retry_command}'.",
        )

    if not matches:
        return _fail(
            command_name,
            f"No cached image named '{requested}'.",
            json_output=json_output,
            recovery="Run 'celesto image list' to see cached images.",
        )
    if len(matches) > 1:
        options = ", ".join(sorted(m.relative_to(root).as_posix() for m in matches))
        return _fail(
            command_name,
            f"'{requested}' matches more than one cached image. Pick one of: {options}.",
            json_output=json_output,
            code="invalid_input",
            recovery=f"Retry with the full name, e.g. 'celesto image save "
            f"{options.split(', ')[0]} -o {shlex.quote(str(out_path))}'.",
            exit_code=2,
        )

    entry = matches[0]
    archive_name = entry.relative_to(root).as_posix()
    if entry.parent == root / "macos":
        return _fail(
            command_name,
            "macOS images stay on the Apple computer where they were installed.",
            json_output=json_output,
            code="unsupported_operation",
            recovery=f"Build it locally with 'celesto image build --os macos --ipsw latest "
            f"-t {entry.name}'.",
        )

    zst_path = entry / _ROOTFS_ZST
    # A symlinked wire file is skipped by the archive loop below, so
    # treating it as present would produce an archive with no rootfs.
    zst_present = zst_path.is_file() and not zst_path.is_symlink()
    # The sidecar is a local cache key that load regenerates from the
    # installed .zst digest; it never travels. The decompressed rootfs is
    # regenerated too whenever the wire file is present.
    excluded = {_DECOMPRESSED_ROOTFS, _ROOTFS_SIDECAR} if zst_present else {_ROOTFS_SIDECAR}

    warnings: list[str] = []
    files_meta: list[dict[str, Any]] = []
    # Write to a sibling temp file and rename at the end so a failed save
    # never destroys an existing archive at the -o path.
    partial_archive = out_path.with_name(f"{out_path.name}.partial-{os.getpid()}")
    compressor = zstandard.ZstdCompressor(threads=-1)
    try:
        tmp_parent = str(out_path.parent) if out_path.parent.is_dir() else None
        with (
            (entry / _BUILD_LOCK).open("a") as build_lock,
            tempfile.TemporaryDirectory(dir=tmp_parent) as tmp,
            tarfile.open(partial_archive, "w") as tar,
        ):
            # Hold the entry's build lock so the archive is one consistent
            # generation, not a mix of two builds; non-blocking so a running
            # build reports as busy instead of hanging the save.
            fcntl.flock(build_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            scratch = Path(tmp) / "member.zst"
            for f in sorted(entry.rglob("*")):
                if f.is_symlink():
                    warnings.append(
                        f"Skipped '{f.relative_to(entry).as_posix()}': links are "
                        "not saved into archives."
                    )
                    continue
                if not f.is_file():
                    continue
                rel = f.relative_to(entry).as_posix()
                if rel in excluded:
                    continue
                # Dot-prefixed names are lock files and builders' in-progress
                # temp artifacts, never part of the image.
                if any(segment.startswith(".") for segment in rel.split("/")):
                    continue
                if rel.endswith(".zst"):
                    # Hash while tar reads the file so the manifest digest
                    # matches the archived bytes even if the source changes
                    # mid-save; a shrinking source fails the save instead of
                    # producing a silently inconsistent archive.
                    hasher = hashlib.sha256()
                    with open(f, "rb") as src:
                        info = tar.gettarinfo(arcname=f"files/{rel}", fileobj=src)
                        # Force a plain file member: gettarinfo turns a second
                        # hardlink to an already-added file into a link entry
                        # the manifest cannot describe.
                        info.type = tarfile.REGTYPE
                        info.linkname = ""
                        info.size = os.fstat(src.fileno()).st_size
                        try:
                            tar.addfile(info, _HashingReader(src, hasher))
                        except OSError as exc:
                            if os.fstat(src.fileno()).st_size < info.size:
                                raise _EntryChangedError(rel) from exc
                            raise
                    files_meta.append(
                        {
                            "path": rel,
                            "encoding": "raw",
                            "size": info.size,
                            "sha256": hasher.hexdigest(),
                        }
                    )
                else:
                    # Compress into one reused scratch file, add, discard —
                    # scratch usage stays bounded by a single member, and the
                    # recorded size counts the bytes actually compressed.
                    with open(f, "rb") as src, open(scratch, "wb") as dst:
                        read_bytes, _ = compressor.copy_stream(src, dst)
                    files_meta.append(
                        {
                            "path": rel,
                            "encoding": "zstd",
                            "size": read_bytes,
                            "sha256": _sha256_file(scratch),
                        }
                    )
                    tar.add(scratch, arcname=f"files/{rel}", recursive=False)
                    scratch.unlink()

            manifest = {
                "schema_version": _SCHEMA_VERSION,
                "saved_by": __version__,
                "created": datetime.now(UTC).isoformat(),
                "name": archive_name,
                "kind": _entry_kind(entry, root),
                "files": files_meta,
            }
            manifest_bytes = json.dumps(manifest, indent=2).encode()
            info = tarfile.TarInfo(_MANIFEST_MEMBER)
            info.size = len(manifest_bytes)
            tar.addfile(info, io.BytesIO(manifest_bytes))
        partial_archive.replace(out_path)
    except _EntryChangedError as exc:
        with suppress(OSError):
            partial_archive.unlink(missing_ok=True)
        return _fail(
            command_name,
            f"The image changed while it was being saved ('{exc.args[0]}' shrank).",
            json_output=json_output,
            recovery=f"Wait until nothing is using the image, then retry '{retry_command}'.",
        )
    except BlockingIOError:
        with suppress(OSError):
            partial_archive.unlink(missing_ok=True)
        return _fail(
            command_name,
            f"'{archive_name}' is being built right now.",
            json_output=json_output,
            recovery=f"Wait for the build to finish, then retry '{retry_command}'.",
        )
    except OSError as exc:
        with suppress(OSError):
            partial_archive.unlink(missing_ok=True)
        return _fail(
            command_name,
            f"Could not write '{out_path}': {_brief_error(exc)}",
            json_output=json_output,
            recovery=f"Free up disk space or fix permissions, then retry '{retry_command}'.",
        )
    except zstandard.ZstdError as exc:
        with suppress(OSError):
            partial_archive.unlink(missing_ok=True)
        return _fail(
            command_name,
            f"Could not save the image: {_brief_error(exc)}",
            json_output=json_output,
            recovery=f"Retry '{retry_command}'.",
        )
    except BaseException:
        with suppress(OSError):
            partial_archive.unlink(missing_ok=True)
        raise

    payload = ImageSavePayload(
        name=archive_name,
        archive_path=str(out_path),
        archive_size_bytes=out_path.stat().st_size,
        files=len(files_meta),
        excluded_decompressed_rootfs=zst_present,
        warnings=warnings,
    )
    if json_output:
        return emit_success(command_name, payload)
    console = console_stdout()
    console.print(
        f"Saved [bold]{archive_name}[/bold] to {out_path} "
        f"({_format_bytes(payload['archive_size_bytes'])}). Load it on another "
        f"machine with 'celesto image load -i {shlex.quote(str(out_path))}'."
    )
    for warning in warnings:
        console.print(f"[yellow]{warning}[/yellow]")
    return 0


def run_image_load(
    *,
    input_file: str,
    image_dir: str | None = None,
    force: bool = False,
    json_output: bool = False,
    command_name: str = "image.load",
) -> int:
    """Execute ``celesto image load``."""
    import zstandard

    from celesto.host.disk import decompress_zstd_sparse
    from celesto.images.published import (
        _decompressed_rootfs_sidecar_value,
        _looks_like_zstd_decode_error,
    )

    root = resolve_image_dir(image_dir)
    in_path = Path(input_file)
    quoted_input = shlex.quote(str(input_file))
    not_an_archive = "Check that the file was created by 'celesto image save' and is not corrupted."

    def bad_archive(
        message: str | None = None,
        *,
        recovery: str | None = None,
    ) -> int:
        return _fail(
            command_name,
            message or f"'{in_path}' is not a Celesto image archive.",
            json_output=json_output,
            code="invalid_input",
            recovery=recovery or not_an_archive,
            exit_code=2,
        )

    try:
        tar = tarfile.open(in_path, "r:")  # noqa: SIM115 — closed by `with tar:` below
    except (OSError, tarfile.TarError) as exc:
        return _fail(
            command_name,
            f"Could not open '{in_path}': {_brief_error(exc)}",
            json_output=json_output,
            code="invalid_input",
            recovery=not_an_archive,
            exit_code=2,
        )

    with tar:
        # A truncated archive can fail while listing members or reading the
        # manifest — that's damage, not a crash.
        try:
            members: list[tarfile.TarInfo] = []
            for member in tar:
                if len(members) >= 10000 or member.issparse():
                    return bad_archive(
                        "Archive contains sparse data or too many files and was not loaded."
                    )
                members.append(member)
            manifest_members = [m for m in members if m.name == _MANIFEST_MEMBER]
            if (
                len(manifest_members) != 1
                or not manifest_members[0].isreg()
                or manifest_members[0].size > _MANIFEST_SIZE_CAP
            ):
                return bad_archive()
            manifest_file = tar.extractfile(manifest_members[0])
            manifest = json.load(manifest_file) if manifest_file else None
        except tarfile.TarError:
            return bad_archive(f"'{in_path}' is damaged and was not loaded.")
        except ValueError:
            manifest = None
        if not isinstance(manifest, dict):
            return bad_archive()

        schema = manifest.get("schema_version")
        if isinstance(schema, int) and schema > _SCHEMA_VERSION:
            return bad_archive(
                "This archive was saved by a newer Celesto.",
                recovery=(
                    f"Run 'celesto update', then retry 'celesto image load -i {quoted_input}'."
                ),
            )
        name = manifest.get("name")
        if schema != _SCHEMA_VERSION or not isinstance(name, str) or not _valid_entry_name(name):
            return bad_archive()

        # Only members declared in the manifest, as regular files, at safe
        # relative paths, are ever written to disk — extraction below builds
        # its own destination paths and never uses tar member names as paths.
        allowed: dict[str, dict[str, Any]] = {}
        declared: set[str] = set()
        raw_files = manifest.get("files")
        for meta in raw_files if isinstance(raw_files, list) else [None]:
            if (
                not isinstance(meta, dict)
                or not isinstance(meta.get("path"), str)
                or meta.get("encoding") not in {"raw", "zstd"}
                # .zst files always travel raw; a re-compressed one would
                # install bytes that differ from the digest the manifest
                # (and the regenerated rootfs sidecar) describes.
                or (_canonical_path(meta["path"]).endswith(".zst") and meta["encoding"] != "raw")
                or not isinstance(meta.get("size"), int)
                or isinstance(meta.get("size"), bool)
                or meta["size"] < 0
                or not isinstance(meta.get("sha256"), str)
                or not _SHA256_RE.match(meta["sha256"])
                or not _valid_relative_file_path(meta["path"])
            ):
                return bad_archive()
            key = _canonical_path(meta["path"])
            if key in declared:
                # Two spellings of one file would silently overwrite each
                # other on a case-insensitive filesystem.
                return bad_archive()
            declared.add(key)
            allowed[f"files/{meta['path']}"] = meta
        # save never emits these: dot-prefixed names are lock files, build
        # fingerprints and in-progress artifacts, and the decompressed
        # rootfs is regenerated below from the installed .zst so an archive
        # cannot assert which pinned bytes a rootfs came from.
        never_saved = {_DECOMPRESSED_ROOTFS} if _ROOTFS_ZST in declared else set()
        # A directory squatting on one of the rootfs names would make every
        # later start of a published image fail until the entry is removed.
        reserved_dirs = tuple(f"{n}/" for n in (_DECOMPRESSED_ROOTFS, _ROOTFS_ZST, _ROOTFS_SIDECAR))
        if any(
            key in never_saved
            or key.startswith(reserved_dirs)
            or any(seg.startswith(".") for seg in key.split("/"))
            for key in declared
        ):
            return bad_archive(
                f"'{in_path}' contains files that 'celesto image save' never writes "
                "and was not loaded.",
                recovery="Recreate it on the source machine with "
                f"'celesto image save {name} -o {shlex.quote(in_path.name)}'.",
            )
        try:
            configured_budget = int(
                os.environ.get("CELESTO_IMAGE_LOAD_MAX_BYTES", str(64 * 1024**3))
            )
            if configured_budget <= 0:
                raise ValueError
        except ValueError:
            return bad_archive(
                "CELESTO_IMAGE_LOAD_MAX_BYTES must be a positive integer; "
                "correct it and retry the load."
            )
        # Preserve one GiB of free space. The caller, not the archive, owns this budget.
        existing_parent = root
        while not existing_parent.exists():
            existing_parent = existing_parent.parent
        budget = min(configured_budget, max(0, shutil.disk_usage(existing_parent).free - 1024**3))
        if sum(meta["size"] for meta in allowed.values()) > budget:
            return bad_archive(
                "Image exceeds the import size budget; free disk space or increase "
                "CELESTO_IMAGE_LOAD_MAX_BYTES and retry."
            )
        written = 0

        def charge(size: int) -> None:
            nonlocal written
            if size > budget - written:
                raise tarfile.TarError("image exceeds the import size budget")
            written += size

        data_members = [m for m in members if m.name != _MANIFEST_MEMBER]
        seen: set[str] = set()
        for member in data_members:
            if (
                not member.isreg()
                or member.issparse()
                or member.name not in allowed
                or member.name in seen
            ):
                return _fail(
                    command_name,
                    f"'{in_path}' contains unexpected entries and was not loaded.",
                    json_output=json_output,
                    code="invalid_input",
                    recovery="Recreate it on the source machine with "
                    f"'celesto image save {name} -o {shlex.quote(in_path.name)}'.",
                    exit_code=2,
                )
            if member.size > budget:
                return bad_archive(
                    "Archive member exceeds the import size budget and was not loaded."
                )
            if (
                allowed[member.name]["encoding"] == "raw"
                and member.size != allowed[member.name]["size"]
            ):
                return bad_archive(
                    "Archive is damaged: member size disagrees with its manifest "
                    "and was not loaded."
                )
            seen.add(member.name)
        missing = set(allowed) - seen
        if missing:
            return bad_archive(f"'{in_path}' is incomplete and was not loaded.")

        target = root / name
        if target.exists() and not force:
            return _fail(
                command_name,
                f"'{name}' already exists.",
                json_output=json_output,
                recovery=f"Run 'celesto image load -i {quoted_input} --force' to replace it.",
            )

        target.parent.mkdir(parents=True, exist_ok=True)
        partial = Path(tempfile.mkdtemp(prefix=f".{target.name}.partial-", dir=target.parent))
        try:
            zst_sha: str | None = None
            installed = 0
            for member in data_members:
                meta = allowed[member.name]
                if _canonical_path(meta["path"]) == _ROOTFS_SIDECAR:
                    # Older Celesto saved the sidecar for entries without a
                    # .zst. It is a local cache key, never installed from an
                    # archive: load regenerates it below when it applies.
                    continue
                installed += 1
                destination = partial / meta["path"]
                destination.parent.mkdir(parents=True, exist_ok=True)
                source = tar.extractfile(member)
                if source is None:
                    raise tarfile.TarError(f"could not read '{member.name}' from the archive")
                # Every member's stored bytes are verified against the
                # manifest digest before use; for the always-raw
                # rootfs.ext4.zst, that same digest is the sole source of
                # the regenerated sidecar value.
                hasher = hashlib.sha256()
                if meta["encoding"] == "raw":
                    with source, open(destination, "wb") as out:
                        while chunk := source.read(_COPY_CHUNK):
                            charge(len(chunk))
                            out.write(chunk)
                            hasher.update(chunk)
                    digest = hasher.hexdigest()
                    if digest != meta["sha256"]:
                        raise zstandard.ZstdError(f"'{meta['path']}' failed its integrity check")
                else:
                    tmp_zst = destination.with_name(destination.name + ".tmp.zst")
                    with source, open(tmp_zst, "wb") as out:
                        while chunk := source.read(_COPY_CHUNK):
                            charge(len(chunk))
                            out.write(chunk)
                            hasher.update(chunk)
                    digest = hasher.hexdigest()
                    if digest != meta["sha256"]:
                        tmp_zst.unlink()
                        raise zstandard.ZstdError(f"'{meta['path']}' failed its integrity check")
                    try:
                        decompress_zstd_sparse(
                            tmp_zst,
                            destination,
                            max_output_bytes=min(meta["size"], budget - written),
                        )
                        charge(destination.stat().st_size)
                    except OSError as exc:
                        if _looks_like_zstd_decode_error(exc):
                            raise zstandard.ZstdError(
                                f"'{meta['path']}' is not a valid zstd stream"
                            ) from exc
                        raise
                    tmp_zst.unlink()
                if destination.stat().st_size != meta["size"]:
                    raise zstandard.ZstdError(
                        f"'{meta['path']}' does not match the size the archive declares"
                    )
                if _canonical_path(meta["path"]) == _ROOTFS_ZST:
                    # Always raw (validated above), so this digest is also
                    # the digest of the installed file.
                    zst_sha = digest

            # Recreate what save deliberately left out, byte-compatible with
            # what ensure_published_image validates on the next start. This
            # goes by what is on disk, not by manifest spellings: whenever a
            # compressed rootfs was installed, the decompressed copy and the
            # sidecar are rebuilt from its verified digest, and a value
            # carried in the manifest (older archives) is ignored, since it
            # is the archive author's claim.
            zst = partial / _ROOTFS_ZST
            rootfs = partial / _DECOMPRESSED_ROOTFS
            if zst.is_file():
                if zst_sha is None:
                    raise tarfile.TarError("the compressed rootfs was not declared")
                rootfs.unlink(missing_ok=True)
                (partial / _ROOTFS_SIDECAR).unlink(missing_ok=True)
                try:
                    decompress_zstd_sparse(zst, rootfs, max_output_bytes=budget - written)
                    charge(rootfs.stat().st_size)
                except OSError as exc:
                    if _looks_like_zstd_decode_error(exc):
                        raise zstandard.ZstdError(
                            f"'{_ROOTFS_ZST}' is not a valid zstd stream"
                        ) from exc
                    raise
                (partial / _ROOTFS_SIDECAR).write_text(_decompressed_rootfs_sidecar_value(zst_sha))

            if target.exists():
                _remove_existing_entry(target)
            partial.rename(target)
        except (tarfile.TarError, zstandard.ZstdError) as exc:
            shutil.rmtree(partial, ignore_errors=True)
            return bad_archive(f"'{in_path}' is damaged and was not loaded: {_brief_error(exc)}.")
        except OSError as exc:
            shutil.rmtree(partial, ignore_errors=True)
            return _fail(
                command_name,
                f"Could not load the image: {_brief_error(exc)}",
                json_output=json_output,
                recovery="Free up disk space or fix permissions, then retry "
                f"'celesto image load -i {quoted_input}'.",
            )
        except BaseException:
            # Ctrl-C and other non-Exception exits must not orphan the
            # multi-GB staging directory.
            shutil.rmtree(partial, ignore_errors=True)
            raise

    warnings = _non_default_dir_warnings(root)
    stale_match = _IMAGE_DIR_NAME_RE.match(name)
    if stale_match and stale_match["version"] != __version__:
        warnings.append(
            "This image comes from a different Celesto version, so it shows "
            "as (stale) in 'celesto image list'."
        )

    payload = ImageLoadPayload(
        name=name,
        path=str(target),
        size_bytes=_total_size(target),
        files=installed,
        warnings=warnings,
    )
    if json_output:
        return emit_success(command_name, payload)
    console = console_stdout()
    console.print(
        f"Loaded [bold]{name}[/bold] ({_format_bytes(payload['size_bytes'])}). "
        "Run 'celesto image list' to confirm."
    )
    for warning in warnings:
        console.print(f"[yellow]{warning}[/yellow]")
    return 0

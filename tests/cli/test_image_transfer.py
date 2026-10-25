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

"""Tests for `celesto image save` / `celesto image load`."""

from __future__ import annotations

import hashlib
import io
import json
import os
import tarfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest
import zstandard

from celesto.cli.main import main

_DEFAULT_HOLE_BYTES = 1 * 1024 * 1024
_TRAILING_HOLE_BYTES = 1 * 1024 * 1024
_SPARSE_PAYLOAD = b"\x00" * _DEFAULT_HOLE_BYTES + b"REAL-DATA" + b"\x00" * _TRAILING_HOLE_BYTES


def _make_published_entry(
    root: Path,
    name: str,
    *,
    hole_bytes: int = _DEFAULT_HOLE_BYTES,
) -> Path:
    payload = b"\x00" * hole_bytes + b"REAL-DATA" + b"\x00" * _TRAILING_HOLE_BYTES
    d = root / name
    d.mkdir(parents=True)
    (d / "rootfs.ext4.zst").write_bytes(zstandard.compress(payload))
    sha = hashlib.sha256((d / "rootfs.ext4.zst").read_bytes()).hexdigest()
    (d / "rootfs.ext4.from-sha256").write_text(f"sparse-v1:{sha}")
    (d / "vmlinux.bin").write_bytes(b"kernel-bytes")
    with open(d / "rootfs.ext4", "wb") as f:
        f.truncate(len(payload))
        f.seek(hole_bytes)
        f.write(b"REAL-DATA")
    return d


def _write_archive(
    path: Path, manifest: dict[str, Any], members: Sequence[tarfile.TarInfo | tuple[str, bytes]]
) -> None:
    with tarfile.open(path, "w") as tar:
        blob = json.dumps(manifest).encode()
        info = tarfile.TarInfo("manifest.json")
        info.size = len(blob)
        tar.addfile(info, io.BytesIO(blob))
        for member in members:
            if isinstance(member, tuple):
                name, data = member
                info = tarfile.TarInfo(name)
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))
            else:
                tar.addfile(member)


class TestSaveLoadRoundTrip:
    def test_published_entry_round_trips(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        sparse_test_config: tuple[int, bool],
    ) -> None:
        hole_bytes, supports_sparse_allocation = sparse_test_config
        src = tmp_path / "src"
        entry = _make_published_entry(
            src,
            "ubuntu-v0.0.1-amd64-firecracker",
            hole_bytes=hole_bytes,
        )
        archive = tmp_path / "ubuntu.tar"

        ret = main(
            ["image", "save", "ubuntu", "--image-dir", str(src), "-o", str(archive), "--json"]
        )
        assert ret == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["command"] == "image.save"
        assert payload["data"]["excluded_decompressed_rootfs"] is True

        # The multi-MB decompressed rootfs never travels.
        with tarfile.open(archive) as tar:
            names = tar.getnames()
        assert "manifest.json" in names
        assert "files/rootfs.ext4" not in names
        assert "files/rootfs.ext4.zst" in names
        assert archive.stat().st_size < 64 * 1024

        dest = tmp_path / "dest"
        ret = main(["image", "load", "-i", str(archive), "--image-dir", str(dest), "--json"])
        assert ret == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["command"] == "image.load"

        loaded = dest / "ubuntu-v0.0.1-amd64-firecracker"
        assert sorted(p.name for p in loaded.iterdir()) == [
            "rootfs.ext4",
            "rootfs.ext4.from-sha256",
            "rootfs.ext4.zst",
            "vmlinux.bin",
        ]
        # Sidecar reproduced exactly, so ensure_published_image accepts it.
        assert (loaded / "rootfs.ext4.from-sha256").read_text() == (
            entry / "rootfs.ext4.from-sha256"
        ).read_text()
        # Rootfs content intact and holes restored.
        with open(loaded / "rootfs.ext4", "rb") as f:
            f.seek(hole_bytes)
            assert f.read(9) == b"REAL-DATA"
            f.seek(-_TRAILING_HOLE_BYTES, os.SEEK_END)
            assert f.read() == b"\x00" * _TRAILING_HOLE_BYTES
        st = os.stat(loaded / "rootfs.ext4")
        if supports_sparse_allocation:
            assert st.st_blocks * 512 < st.st_size

    def test_custom_entry_round_trips(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        src = tmp_path / "src"
        fp = src / "custom" / "myimg" / "abc123def4567890"
        fp.mkdir(parents=True)
        (fp / "metadata.json").write_text(json.dumps({"name": "myimg", "arch": "amd64"}))
        (fp / "rootfs.ext4").write_bytes(b"custom-rootfs")
        (fp / ".build.lock").write_text("")
        archive = tmp_path / "myimg.tar"

        ret = main(
            [
                "image",
                "save",
                "custom/myimg",
                "--image-dir",
                str(src),
                "-o",
                str(archive),
                "--json",
            ]
        )
        assert ret == 0
        capsys.readouterr()

        with tarfile.open(archive) as tar:
            names = tar.getnames()
        assert "files/.build.lock" not in names and "files/.build.lock.zst" not in names

        dest = tmp_path / "dest"
        ret = main(["image", "load", "-i", str(archive), "--image-dir", str(dest), "--json"])
        assert ret == 0
        capsys.readouterr()
        loaded = dest / "custom" / "myimg" / "abc123def4567890"
        assert (loaded / "rootfs.ext4").read_bytes() == b"custom-rootfs"
        assert json.loads((loaded / "metadata.json").read_text())["arch"] == "amd64"

    def test_load_refuses_overwrite_without_force(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        src = tmp_path / "src"
        _make_published_entry(src, "ubuntu-v0.0.1-amd64-firecracker")
        archive = tmp_path / "ubuntu.tar"
        assert main(["image", "save", "ubuntu", "--image-dir", str(src), "-o", str(archive)]) == 0
        capsys.readouterr()

        dest = tmp_path / "dest"
        assert main(["image", "load", "-i", str(archive), "--image-dir", str(dest)]) == 0
        capsys.readouterr()

        ret = main(["image", "load", "-i", str(archive), "--image-dir", str(dest), "--json"])
        assert ret == 1
        payload = json.loads(capsys.readouterr().out)
        assert "--force" in payload["error"]["recovery"]

        ret = main(
            ["image", "load", "-i", str(archive), "--image-dir", str(dest), "--force", "--json"]
        )
        assert ret == 0

    def test_save_ambiguous_preset_lists_options(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        src = tmp_path / "src"
        _make_published_entry(src, "ubuntu-v0.0.1-amd64-firecracker")
        _make_published_entry(src, "ubuntu-v0.0.2-amd64-qemu")

        ret = main(
            [
                "image",
                "save",
                "ubuntu",
                "--image-dir",
                str(src),
                "-o",
                str(tmp_path / "x.tar"),
                "--json",
            ]
        )
        assert ret == 2
        payload = json.loads(capsys.readouterr().out)
        assert "ubuntu-v0.0.1-amd64-firecracker" in payload["error"]["message"]
        assert "ubuntu-v0.0.2-amd64-qemu" in payload["error"]["message"]


class TestLoadRejectsMaliciousArchives:
    def _assert_rejected(
        self, archive: Path, dest: Path, capsys: pytest.CaptureFixture[str]
    ) -> dict[str, Any]:
        ret = main(["image", "load", "-i", str(archive), "--image-dir", str(dest), "--json"])
        assert ret == 2
        payload = json.loads(capsys.readouterr().out)
        assert payload["ok"] is False
        # Nothing may be written outside (or inside) the destination.
        assert not dest.exists() or not any(dest.iterdir())
        return dict(payload)

    def test_traversal_path_in_manifest(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        archive = tmp_path / "evil.tar"
        _write_archive(
            archive,
            {
                "schema_version": 1,
                "name": "evil",
                "rootfs_sidecar": None,
                "files": [{"path": "../../escape", "encoding": "raw", "size": 4}],
            },
            [("files/../../escape", b"boom")],
        )
        self._assert_rejected(archive, tmp_path / "dest", capsys)
        assert not (tmp_path / "escape").exists()

    def test_absolute_member_name(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        archive = tmp_path / "evil.tar"
        _write_archive(
            archive,
            {
                "schema_version": 1,
                "name": "evil",
                "rootfs_sidecar": None,
                "files": [{"path": "/etc/passwd", "encoding": "raw", "size": 4}],
            },
            [("files//etc/passwd", b"boom")],
        )
        self._assert_rejected(archive, tmp_path / "dest", capsys)

    def test_symlink_member_rejected(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        archive = tmp_path / "evil.tar"
        link = tarfile.TarInfo("files/link")
        link.type = tarfile.SYMTYPE
        link.linkname = "/etc/passwd"
        _write_archive(
            archive,
            {
                "schema_version": 1,
                "name": "evil",
                "rootfs_sidecar": None,
                "files": [{"path": "link", "encoding": "raw", "size": 0}],
            },
            [link],
        )
        self._assert_rejected(archive, tmp_path / "dest", capsys)

    def test_undeclared_member_rejected(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        archive = tmp_path / "evil.tar"
        _write_archive(
            archive,
            {"schema_version": 1, "name": "ok-name", "rootfs_sidecar": None, "files": []},
            [("files/surprise", b"boom")],
        )
        self._assert_rejected(archive, tmp_path / "dest", capsys)

    def test_bad_entry_name_rejected(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        archive = tmp_path / "evil.tar"
        _write_archive(
            archive,
            {"schema_version": 1, "name": "../outside", "rootfs_sidecar": None, "files": []},
            [],
        )
        self._assert_rejected(archive, tmp_path / "dest", capsys)

    def test_newer_schema_names_update(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        archive = tmp_path / "future.tar"
        _write_archive(
            archive,
            {"schema_version": 99, "name": "x", "rootfs_sidecar": None, "files": []},
            [],
        )
        ret = main(
            ["image", "load", "-i", str(archive), "--image-dir", str(tmp_path / "dest"), "--json"]
        )
        assert ret == 2
        payload = json.loads(capsys.readouterr().out)
        assert "celesto update" in payload["error"]["recovery"]

    def test_not_a_tar(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        bogus = tmp_path / "bogus.tar"
        bogus.write_bytes(b"not a tar at all")

        ret = main(
            ["image", "load", "-i", str(bogus), "--image-dir", str(tmp_path / "dest"), "--json"]
        )
        assert ret == 2
        payload = json.loads(capsys.readouterr().out)
        assert "celesto image save" in payload["error"]["recovery"]


class TestArchiveRobustness:
    def test_sibling_zst_pair_round_trips(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """x and x.zst in one entry must both survive (regression: member
        name collision silently dropped one)."""
        src = tmp_path / "src"
        entry = src / "oddball"
        entry.mkdir(parents=True)
        (entry / "data.txt").write_bytes(b"plain")
        (entry / "data.txt.zst").write_bytes(zstandard.compress(b"compressed"))
        archive = tmp_path / "odd.tar"

        assert (
            main(
                ["image", "save", "oddball", "--image-dir", str(src), "-o", str(archive), "--json"]
            )
            == 0
        )
        capsys.readouterr()
        dest = tmp_path / "dest"
        assert main(["image", "load", "-i", str(archive), "--image-dir", str(dest), "--json"]) == 0
        capsys.readouterr()

        loaded = dest / "oddball"
        assert (loaded / "data.txt").read_bytes() == b"plain"
        assert (loaded / "data.txt.zst").read_bytes() == zstandard.compress(b"compressed")

    def test_zstd_encoded_zst_member_is_rejected(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """.zst files always travel raw; a re-compressed rootfs.ext4.zst
        would install bytes whose digest differs from what the manifest and
        the regenerated sidecar describe, so load refuses the archive."""
        zst_file = zstandard.compress(_SPARSE_PAYLOAD)
        stored = zstandard.compress(zst_file)
        archive = tmp_path / "in.tar"
        _write_archive(
            archive,
            {
                "schema_version": 1,
                "name": "oddball",
                "rootfs_sidecar": None,
                "files": [
                    {
                        "path": "rootfs.ext4.zst",
                        "encoding": "zstd",
                        "size": len(zst_file),
                        "sha256": hashlib.sha256(stored).hexdigest(),
                    }
                ],
            },
            [("files/rootfs.ext4.zst", stored)],
        )

        dest = tmp_path / "dest"
        ret = main(["image", "load", "-i", str(archive), "--image-dir", str(dest), "--json"])
        assert ret == 2
        payload = json.loads(capsys.readouterr().out)
        assert payload["error"]["code"] == "invalid_input"
        assert not (dest / "oddball").exists()

    def test_save_skips_build_temp_artifacts(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Dot-prefixed lock files and builders' in-progress artifacts must
        not travel; archiving them would install a half-written rootfs on
        the target machine."""
        src = tmp_path / "src"
        entry = _make_published_entry(src, "ubuntu-v0.0.1-amd64-firecracker")
        (entry / ".rootfs.tmp.ext4").write_bytes(b"half-written")
        context_dir = entry / ".build-abc123"
        context_dir.mkdir()
        (context_dir / "Dockerfile").write_text("FROM scratch")
        archive = tmp_path / "ubuntu.tar"

        assert main(["image", "save", "ubuntu", "--image-dir", str(src), "-o", str(archive)]) == 0
        capsys.readouterr()

        with tarfile.open(archive) as tar:
            names = tar.getnames()
        assert names, "archive must not be empty"
        assert not any(".rootfs.tmp.ext4" in n or ".build-abc123" in n for n in names)

    def test_save_reports_busy_while_entry_is_being_built(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """While a builder holds the entry's build lock, save must fail
        with a clear message instead of archiving a mix of two builds."""
        fcntl = pytest.importorskip("fcntl")
        src = tmp_path / "src"
        entry = _make_published_entry(src, "ubuntu-v0.0.1-amd64-firecracker")
        archive = tmp_path / "ubuntu.tar"

        with (entry / ".build.lock").open("w") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            ret = main(
                ["image", "save", "ubuntu", "--image-dir", str(src), "-o", str(archive), "--json"]
            )

        assert ret == 1
        payload = json.loads(capsys.readouterr().out)
        assert "being built" in payload["error"]["message"]
        assert "retry" in payload["error"]["recovery"]
        assert not archive.exists()

    def test_raw_zst_member_keeps_source_metadata(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Raw members are streamed from an open fd; the tar header must
        still carry the source file's mtime, like every other member."""
        src = tmp_path / "src"
        entry = _make_published_entry(src, "ubuntu-v0.0.1-amd64-firecracker")
        stamp = 1_700_000_000
        os.utime(entry / "rootfs.ext4.zst", (stamp, stamp))
        archive = tmp_path / "ubuntu.tar"

        assert main(["image", "save", "ubuntu", "--image-dir", str(src), "-o", str(archive)]) == 0
        capsys.readouterr()

        with tarfile.open(archive) as tar:
            member = tar.getmember("files/rootfs.ext4.zst")
        assert member.isreg()
        assert member.mtime == stamp

    def test_truncated_archive_gets_clean_envelope(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A cut-off transfer must produce the error envelope, not a
        traceback (regression)."""
        src = tmp_path / "src"
        _make_published_entry(src, "ubuntu-v0.0.1-amd64-firecracker")
        archive = tmp_path / "ubuntu.tar"
        assert main(["image", "save", "ubuntu", "--image-dir", str(src), "-o", str(archive)]) == 0
        capsys.readouterr()
        # Cut into the first member's data (small archives are mostly
        # zero padding, so a percentage cut may remove nothing real).
        data = archive.read_bytes()
        assert len(data) > 700, "test needs an archive large enough to truncate"
        archive.write_bytes(data[:700])

        ret = main(
            ["image", "load", "-i", str(archive), "--image-dir", str(tmp_path / "dest"), "--json"]
        )

        assert ret == 2
        payload = json.loads(capsys.readouterr().out)
        assert payload["error"]["code"] == "invalid_input"

    def test_archive_missing_declared_member_is_rejected(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """An archive whose manifest promises files it doesn't carry must
        not load as success (regression)."""
        archive = tmp_path / "short.tar"
        _write_archive(
            archive,
            {
                "schema_version": 1,
                "name": "ubuntu-v0.0.1-amd64-firecracker",
                "rootfs_sidecar": None,
                "files": [
                    {
                        "path": "vmlinux.bin",
                        "encoding": "raw",
                        "size": 4,
                        "sha256": hashlib.sha256(b"kern").hexdigest(),
                    },
                    {
                        "path": "rootfs.ext4.zst",
                        "encoding": "raw",
                        "size": 4,
                        "sha256": hashlib.sha256(b"zstd").hexdigest(),
                    },
                ],
            },
            [("files/vmlinux.bin", b"kern")],
        )

        ret = main(
            ["image", "load", "-i", str(archive), "--image-dir", str(tmp_path / "dest"), "--json"]
        )

        assert ret == 2
        payload = json.loads(capsys.readouterr().out)
        assert "incomplete" in payload["error"]["message"]
        assert not (tmp_path / "dest" / "ubuntu-v0.0.1-amd64-firecracker").exists()

    def test_size_mismatch_is_rejected(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        archive = tmp_path / "lying.tar"
        _write_archive(
            archive,
            {
                "schema_version": 1,
                "name": "entry",
                "rootfs_sidecar": None,
                "files": [
                    {
                        "path": "blob",
                        "encoding": "raw",
                        "size": 3,
                        "sha256": hashlib.sha256(b"0123456789").hexdigest(),
                    }
                ],
            },
            [("files/blob", b"0123456789")],
        )

        ret = main(
            ["image", "load", "-i", str(archive), "--image-dir", str(tmp_path / "dest"), "--json"]
        )

        assert ret == 2
        payload = json.loads(capsys.readouterr().out)
        assert "damaged" in payload["error"]["message"]
        assert not (tmp_path / "dest" / "entry").exists()

    def test_load_force_replaces_symlinked_entry(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--force onto a symlinked entry must replace the link, not crash
        (regression: rmtree refused symlinks)."""
        src = tmp_path / "src"
        _make_published_entry(src, "ubuntu-v0.0.1-amd64-firecracker")
        archive = tmp_path / "ubuntu.tar"
        assert main(["image", "save", "ubuntu", "--image-dir", str(src), "-o", str(archive)]) == 0
        capsys.readouterr()

        dest = tmp_path / "dest"
        dest.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "keep").write_text("keep")
        (dest / "ubuntu-v0.0.1-amd64-firecracker").symlink_to(outside)

        ret = main(
            ["image", "load", "-i", str(archive), "--image-dir", str(dest), "--force", "--json"]
        )

        assert ret == 0
        capsys.readouterr()
        loaded = dest / "ubuntu-v0.0.1-amd64-firecracker"
        assert not loaded.is_symlink()
        assert (loaded / "vmlinux.bin").is_file()
        assert (outside / "keep").exists()

    def test_save_to_directory_gets_clean_envelope(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """-o pointing at a folder must error cleanly, not traceback in
        cleanup (regression)."""
        src = tmp_path / "src"
        _make_published_entry(src, "ubuntu-v0.0.1-amd64-firecracker")

        ret = main(
            ["image", "save", "ubuntu", "--image-dir", str(src), "-o", str(tmp_path), "--json"]
        )

        assert ret == 2
        payload = json.loads(capsys.readouterr().out)
        assert payload["error"]["code"] == "invalid_input"
        assert "-o" in payload["error"]["message"]

    def test_failed_save_preserves_existing_archive(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A failing save must never destroy a pre-existing file at -o
        (regression: cleanup unlinked it)."""
        from unittest.mock import patch

        src = tmp_path / "src"
        entry = src / "entry"
        entry.mkdir(parents=True)
        (entry / "blob").write_bytes(b"x")
        archive = tmp_path / "precious.tar"
        archive.write_bytes(b"OLD ARCHIVE")

        with patch("zstandard.ZstdCompressor") as mock_compressor:
            mock_compressor.return_value.copy_stream.side_effect = OSError(28, "No space left")
            ret = main(
                ["image", "save", "entry", "--image-dir", str(src), "-o", str(archive), "--json"]
            )

        assert ret == 1
        payload = json.loads(capsys.readouterr().out)
        assert payload["ok"] is False
        assert archive.read_bytes() == b"OLD ARCHIVE"
        assert not list(archive.parent.glob("precious.tar.partial*"))

    def test_save_warns_about_skipped_links(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        src = tmp_path / "src"
        entry = src / "entry"
        entry.mkdir(parents=True)
        (entry / "blob").write_bytes(b"x")
        (entry / "link").symlink_to(entry / "blob")

        ret = main(
            [
                "image",
                "save",
                "entry",
                "--image-dir",
                str(src),
                "-o",
                str(tmp_path / "e.tar"),
                "--json",
            ]
        )

        assert ret == 0
        payload = json.loads(capsys.readouterr().out)
        assert any("link" in w for w in payload["data"]["warnings"])


class TestUpstreamReviewRegressions:
    def test_symlinked_zst_is_treated_as_absent(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A symlinked wire file must not produce an archive with no rootfs
        (regression: is_file() followed the link, excluding the real one)."""
        src = tmp_path / "src"
        entry = src / "entry"
        entry.mkdir(parents=True)
        real_zst = tmp_path / "elsewhere.zst"
        real_zst.write_bytes(zstandard.compress(b"data"))
        (entry / "rootfs.ext4.zst").symlink_to(real_zst)
        (entry / "rootfs.ext4").write_bytes(b"decompressed")
        archive = tmp_path / "e.tar"

        ret = main(
            ["image", "save", "entry", "--image-dir", str(src), "-o", str(archive), "--json"]
        )

        assert ret == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["data"]["excluded_decompressed_rootfs"] is False
        with tarfile.open(archive) as tar:
            names = tar.getnames()
        # The real decompressed rootfs travels (zstd-encoded, suffix-free).
        assert "files/rootfs.ext4" in names

        dest = tmp_path / "dest"
        assert main(["image", "load", "-i", str(archive), "--image-dir", str(dest), "--json"]) == 0
        capsys.readouterr()
        assert (dest / "entry" / "rootfs.ext4").read_bytes() == b"decompressed"

    def test_corrupted_member_bytes_are_rejected(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Same-length corruption must fail the per-file digest check
        (regression: size-only validation let it load)."""
        archive = tmp_path / "tampered.tar"
        _write_archive(
            archive,
            {
                "schema_version": 1,
                "name": "entry",
                "rootfs_sidecar": None,
                "files": [
                    {
                        "path": "blob",
                        "encoding": "raw",
                        "size": 10,
                        "sha256": hashlib.sha256(b"0123456789").hexdigest(),
                    }
                ],
            },
            [("files/blob", b"0123456780")],  # same length, one byte off
        )

        ret = main(
            ["image", "load", "-i", str(archive), "--image-dir", str(tmp_path / "dest"), "--json"]
        )

        assert ret == 2
        payload = json.loads(capsys.readouterr().out)
        assert "damaged" in payload["error"]["message"]
        assert not (tmp_path / "dest" / "entry").exists()

    def test_manifest_without_sha256_is_rejected(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        archive = tmp_path / "nosha.tar"
        _write_archive(
            archive,
            {
                "schema_version": 1,
                "name": "entry",
                "rootfs_sidecar": None,
                "files": [{"path": "blob", "encoding": "raw", "size": 4}],
            },
            [("files/blob", b"data")],
        )

        ret = main(
            ["image", "load", "-i", str(archive), "--image-dir", str(tmp_path / "dest"), "--json"]
        )

        assert ret == 2
        payload = json.loads(capsys.readouterr().out)
        assert payload["error"]["code"] == "invalid_input"


class TestLoadDoesNotTrustArchiveProvenance:
    """An archive may describe the files it carries, never where they came from.

    The decompressed rootfs and its ``rootfs.ext4.from-sha256`` sidecar are
    the only binding between ``rootfs.ext4`` and the SHA-256-pinned
    ``rootfs.ext4.zst`` that ``ensure_published_image`` verifies. Both are
    always regenerated on load from the bytes actually installed, so a
    crafted archive cannot claim a tampered rootfs was produced from the
    pinned compressed bytes (security audit run-1).
    """

    @staticmethod
    def _members(zst: bytes, kernel: bytes = b"kernel") -> list[tuple[str, bytes]]:
        return [("files/vmlinux.bin", kernel), ("files/rootfs.ext4.zst", zst)]

    @staticmethod
    def _files(members: list[tuple[str, bytes]]) -> list[dict[str, Any]]:
        return [
            {
                "path": name.removeprefix("files/"),
                "encoding": "raw",
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
            for name, data in members
        ]

    def test_manifest_sidecar_claim_is_ignored(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        zst = zstandard.compress(b"rootfs bytes")
        members = self._members(zst)
        archive = tmp_path / "claim.tar"
        _write_archive(
            archive,
            {
                "schema_version": 1,
                "name": "entry",
                "rootfs_sidecar": "sparse-v1:" + "0" * 64,
                "files": self._files(members),
            },
            members,
        )
        dest = tmp_path / "dest"
        assert main(["image", "load", "-i", str(archive), "--image-dir", str(dest), "--json"]) == 0
        capsys.readouterr()
        installed_sha = hashlib.sha256(
            (dest / "entry" / "rootfs.ext4.zst").read_bytes()
        ).hexdigest()
        assert (dest / "entry" / "rootfs.ext4.from-sha256").read_text() == (
            f"sparse-v1:{installed_sha}"
        )
        assert (dest / "entry" / "rootfs.ext4").read_bytes() == b"rootfs bytes"

    @pytest.mark.parametrize(
        "extra",
        [
            ("files/rootfs.ext4", b"tampered"),
            ("files/Rootfs.EXT4", b"tampered"),
            ("files/.fingerprint", b"forged"),
            ("files/sub/.hidden", b"forged"),
        ],
        ids=[
            "decompressed-rootfs",
            "decompressed-rootfs-case-variant",
            "dot-file",
            "nested-dot-file",
        ],
    )
    def test_members_save_never_emits_are_rejected(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], extra: tuple[str, bytes]
    ) -> None:
        members = [*self._members(zstandard.compress(b"rootfs bytes")), extra]
        archive = tmp_path / "forged.tar"
        _write_archive(
            archive,
            {"schema_version": 1, "name": "entry", "files": self._files(members)},
            members,
        )
        dest = tmp_path / "dest"
        ret = main(["image", "load", "-i", str(archive), "--image-dir", str(dest), "--json"])
        assert ret == 2
        payload = json.loads(capsys.readouterr().out)
        assert payload["ok"] is False
        assert payload["error"]["code"] == "invalid_input"
        assert "celesto image save" in payload["error"]["recovery"]
        assert not dest.exists() or not any(dest.iterdir())

    def test_forged_archive_under_published_name_never_serves_tampered_rootfs(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """End-to-end: load a forged archive named like the published cache
        entry, then start-path resolution must boot the pinned rootfs."""
        from unittest.mock import MagicMock, patch

        from celesto import __version__
        from celesto.images.published import (
            ManifestKey,
            PublishedImage,
            _decompressed_rootfs_sidecar_value,
            cache_name,
            ensure_published_image,
        )

        genuine = b"GENUINE ROOTFS " * 64
        genuine_zst = zstandard.compress(genuine)
        kernel = b"GENUINE KERNEL " * 16
        tampered = b"TAMPERED ROOTFS " * 64
        entry = PublishedImage(
            preset="ubuntu",
            arch="arm64",
            vmm="qemu",
            os="ubuntu",
            kernel_url="https://example.invalid/vmlinux-arm64.image",
            kernel_sha256=hashlib.sha256(kernel).hexdigest(),
            rootfs_url="https://example.invalid/ubuntu-arm64-rootfs.ext4.zst",
            rootfs_sha256=hashlib.sha256(genuine_zst).hexdigest(),
        )
        manifest: dict[ManifestKey, PublishedImage] = {("ubuntu", "arm64", "qemu", "ubuntu"): entry}
        name = cache_name("ubuntu", "arm64", "qemu", __version__)
        members = self._members(zstandard.compress(tampered), kernel)
        archive = tmp_path / "forged.tar"
        _write_archive(
            archive,
            {
                "schema_version": 1,
                "name": name,
                "rootfs_sidecar": _decompressed_rootfs_sidecar_value(entry.rootfs_sha256),
                "files": self._files(members),
            },
            members,
        )
        dest = tmp_path / "images"
        assert main(["image", "load", "-i", str(archive), "--image-dir", str(dest), "--json"]) == 0
        capsys.readouterr()

        bodies = {entry.kernel_url: kernel, entry.rootfs_url: genuine_zst}
        downloads: list[str] = []

        def fake_get(url: str, *_args: object, **_kwargs: object) -> MagicMock:
            downloads.append(url)
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            resp.headers.get.return_value = None
            resp.iter_content = lambda chunk_size, body=bodies[url]: iter([body])
            return resp

        with patch("celesto.images.manager.requests.get", side_effect=fake_get):
            local = ensure_published_image(
                "ubuntu", "arm64", "qemu", cache_dir=dest, manifest=manifest, version=__version__
            )
            assert downloads == [entry.kernel_url, entry.rootfs_url]
            assert local.rootfs_path.read_bytes() == genuine
            downloads.clear()
            again = ensure_published_image(
                "ubuntu", "arm64", "qemu", cache_dir=dest, manifest=manifest, version=__version__
            )
            assert downloads == []
            assert again.rootfs_path.read_bytes() == genuine

    def test_sidecar_member_is_discarded_not_installed(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Archives saved by older Celesto versions could carry the sidecar
        (for entries without a .zst). It is a local cache key, so load
        drops it and never installs the archive's value, whatever its case."""
        zst = zstandard.compress(b"rootfs bytes")
        members = [
            ("files/vmlinux.bin", b"kernel"),
            ("files/rootfs.ext4.zst", zst),
            ("files/ROOTFS.EXT4.FROM-SHA256", b"sparse-v1:" + b"0" * 64),
        ]
        archive = tmp_path / "old.tar"
        _write_archive(
            archive,
            {"schema_version": 1, "name": "entry", "files": self._files(members)},
            members,
        )
        dest = tmp_path / "dest"
        assert main(["image", "load", "-i", str(archive), "--image-dir", str(dest), "--json"]) == 0
        capsys.readouterr()
        installed = sorted(p.name for p in (dest / "entry").iterdir())
        assert installed == [
            "rootfs.ext4",
            "rootfs.ext4.from-sha256",
            "rootfs.ext4.zst",
            "vmlinux.bin",
        ]
        zst_sha = hashlib.sha256((dest / "entry" / "rootfs.ext4.zst").read_bytes()).hexdigest()
        assert (dest / "entry" / "rootfs.ext4.from-sha256").read_text() == f"sparse-v1:{zst_sha}"
        assert (dest / "entry" / "rootfs.ext4").read_bytes() == b"rootfs bytes"

    def test_case_variant_members_cannot_forge_rootfs(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """On a case-insensitive filesystem 'rootfs.ext4.ZST' lands as
        rootfs.ext4.zst, so reserved-name rules must compare case-folded
        names and the archive must be refused."""
        genuine_zst = zstandard.compress(b"GENUINE")
        members = [
            ("files/vmlinux.bin", b"kernel"),
            ("files/rootfs.ext4.ZST", genuine_zst),
            ("files/rootfs.ext4", b"TAMPERED"),
        ]
        archive = tmp_path / "forged.tar"
        _write_archive(
            archive,
            {"schema_version": 1, "name": "entry", "files": self._files(members)},
            members,
        )
        dest = tmp_path / "dest"
        ret = main(["image", "load", "-i", str(archive), "--image-dir", str(dest), "--json"])
        assert ret == 2
        payload = json.loads(capsys.readouterr().out)
        assert payload["error"]["code"] == "invalid_input"
        assert not dest.exists() or not any(dest.iterdir())

    def test_paths_that_collide_on_case_insensitive_filesystems_are_rejected(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        members = [("files/config.json", b"a"), ("files/Config.JSON", b"b")]
        archive = tmp_path / "collide.tar"
        _write_archive(
            archive,
            {"schema_version": 1, "name": "entry", "files": self._files(members)},
            members,
        )
        dest = tmp_path / "dest"
        assert main(["image", "load", "-i", str(archive), "--image-dir", str(dest), "--json"]) == 2
        capsys.readouterr()
        assert not dest.exists() or not any(dest.iterdir())

    def test_stray_sidecar_without_zst_is_not_saved_and_archive_loads(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        src = tmp_path / "src"
        entry = src / "entry"
        entry.mkdir(parents=True)
        (entry / "rootfs.ext4").write_bytes(b"decompressed")
        (entry / "rootfs.ext4.from-sha256").write_text("sparse-v1:" + "0" * 64)
        (entry / "vmlinux.bin").write_bytes(b"kernel")
        archive = tmp_path / "e.tar"
        assert (
            main(["image", "save", "entry", "--image-dir", str(src), "-o", str(archive), "--json"])
            == 0
        )
        capsys.readouterr()
        with tarfile.open(archive) as tar:
            assert "files/rootfs.ext4.from-sha256" not in tar.getnames()
        dest = tmp_path / "dest"
        assert main(["image", "load", "-i", str(archive), "--image-dir", str(dest), "--json"]) == 0
        capsys.readouterr()
        assert (dest / "entry" / "rootfs.ext4").read_bytes() == b"decompressed"
        assert not (dest / "entry" / "rootfs.ext4.from-sha256").exists()

    @pytest.mark.parametrize(
        "path",
        ["rootfs.ext4/x", "ROOTFS.EXT4.ZST/x", "rootfs.ext4.from-sha256/x"],
    )
    def test_directories_at_reserved_rootfs_names_are_rejected(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], path: str
    ) -> None:
        """A directory planted where rootfs.ext4 or its siblings live would
        make every later start of a published image fail until the entry
        is removed, so those names are reserved as path prefixes too."""
        members = [("files/vmlinux.bin", b"kernel"), (f"files/{path}", b"x")]
        archive = tmp_path / "dir.tar"
        _write_archive(
            archive,
            {"schema_version": 1, "name": "entry", "files": self._files(members)},
            members,
        )
        dest = tmp_path / "dest"
        assert main(["image", "load", "-i", str(archive), "--image-dir", str(dest), "--json"]) == 2
        payload = json.loads(capsys.readouterr().out)
        assert payload["error"]["code"] == "invalid_input"
        assert not dest.exists() or not any(dest.iterdir())

    def test_duplicate_tar_members_are_rejected(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        zst = zstandard.compress(b"rootfs bytes")
        members = [("files/vmlinux.bin", b"kernel"), ("files/rootfs.ext4.zst", zst)]
        archive = tmp_path / "dup.tar"
        _write_archive(
            archive,
            {"schema_version": 1, "name": "entry", "files": self._files(members)},
            [*members, ("files/rootfs.ext4.zst", zst)],
        )
        dest = tmp_path / "dest"
        assert main(["image", "load", "-i", str(archive), "--image-dir", str(dest), "--json"]) == 2
        payload = json.loads(capsys.readouterr().out)
        assert payload["error"]["code"] == "invalid_input"
        assert not dest.exists() or not any(dest.iterdir())

    def test_corrupt_zstd_member_is_reported_as_damage(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A zstd-encoded member whose bytes are not a zstd stream is a
        damaged archive, not a disk-space problem."""
        garbage = b"not a zstd frame at all"
        archive = tmp_path / "corrupt.tar"
        _write_archive(
            archive,
            {
                "schema_version": 1,
                "name": "entry",
                "files": [
                    {
                        "path": "config.json",
                        "encoding": "zstd",
                        "size": 5,
                        "sha256": hashlib.sha256(garbage).hexdigest(),
                    }
                ],
            },
            [("files/config.json", garbage)],
        )
        dest = tmp_path / "dest"
        assert main(["image", "load", "-i", str(archive), "--image-dir", str(dest), "--json"]) == 2
        payload = json.loads(capsys.readouterr().out)
        assert payload["error"]["code"] == "invalid_input"
        assert "damaged" in payload["error"]["message"]
        assert not dest.exists() or not any(dest.iterdir())


@pytest.mark.parametrize("name", ["CUSTOM", "Custom", "MACOS", "MacOS"])
def test_load_rejects_case_alias_of_namespace_root(
    tmp_path: Path, name: str, capsys: pytest.CaptureFixture[str]
) -> None:
    archive = tmp_path / "alias.tar"
    root = tmp_path / "images"
    sentinel = root / name / "keep"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text("existing image")
    _write_archive(archive, {"schema_version": 1, "name": name, "files": []}, [])
    assert (
        main(["image", "load", "-i", str(archive), "--image-dir", str(root), "--force", "--json"])
        == 2
    )
    assert sentinel.read_text() == "existing image"


@pytest.mark.parametrize("encoding", ["raw", "zstd", "rootfs"])
def test_load_enforces_expansion_budget_and_preserves_existing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    encoding: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("CELESTO_IMAGE_LOAD_MAX_BYTES", "4096")
    monkeypatch.setenv("CELESTO_DISABLE_NATIVE_DISK", "1")
    archive = tmp_path / "oversize.tar"
    root = tmp_path / "images"
    entry = root / "example"
    entry.mkdir(parents=True)
    (entry / "keep").write_text("old")
    content = b"x" * 8192
    stored = content if encoding == "raw" else zstandard.compress(content)
    name = "rootfs.ext4.zst" if encoding == "rootfs" else "payload"
    meta = {
        "path": name,
        "encoding": "zstd" if encoding == "zstd" else "raw",
        "size": len(stored) if encoding == "rootfs" else len(content),
        "sha256": hashlib.sha256(stored).hexdigest(),
    }
    _write_archive(
        archive,
        {"schema_version": 1, "name": "example", "files": [meta]},
        [(f"files/{name}", stored)],
    )
    result = main(
        ["image", "load", "-i", str(archive), "--image-dir", str(root), "--force", "--json"]
    )
    assert result != 0
    assert (entry / "keep").read_text() == "old"
    assert sorted(p.name for p in root.iterdir()) == ["example"]

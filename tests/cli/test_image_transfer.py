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
    path: Path, manifest: dict[str, Any], members: list[tarfile.TarInfo | tuple[str, bytes]]
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
        capsys: pytest.CaptureFixture,
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

    def test_custom_entry_round_trips(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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
        self, archive: Path, dest: Path, capsys: pytest.CaptureFixture
    ) -> dict[str, Any]:
        ret = main(["image", "load", "-i", str(archive), "--image-dir", str(dest), "--json"])
        assert ret == 2
        payload = json.loads(capsys.readouterr().out)
        assert payload["ok"] is False
        # Nothing may be written outside (or inside) the destination.
        assert not dest.exists() or not any(dest.iterdir())
        return dict(payload)

    def test_traversal_path_in_manifest(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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

    def test_absolute_member_name(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
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

    def test_symlink_member_rejected(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        archive = tmp_path / "evil.tar"
        _write_archive(
            archive,
            {"schema_version": 1, "name": "ok-name", "rootfs_sidecar": None, "files": []},
            [("files/surprise", b"boom")],
        )
        self._assert_rejected(archive, tmp_path / "dest", capsys)

    def test_bad_entry_name_rejected(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        archive = tmp_path / "evil.tar"
        _write_archive(
            archive,
            {"schema_version": 1, "name": "../outside", "rootfs_sidecar": None, "files": []},
            [],
        )
        self._assert_rejected(archive, tmp_path / "dest", capsys)

    def test_newer_schema_names_update(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
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

    def test_not_a_tar(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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

    def test_size_mismatch_is_rejected(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture, extra: tuple[str, bytes]
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """End-to-end: load a forged archive named like the published cache
        entry, then start-path resolution must boot the pinned rootfs."""
        from unittest.mock import MagicMock, patch

        from celesto import __version__
        from celesto.images.published import (
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
        manifest = {("ubuntu", "arm64", "qemu", "ubuntu"): entry}
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture, path: str
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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
        self, tmp_path: Path, capsys: pytest.CaptureFixture
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


class TestHostileManifestName:
    def test_load_renders_archive_name_literally(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """An archive-supplied name must not become Rich markup or terminal escapes."""
        src = tmp_path / "src"
        _make_published_entry(src, "codex-v0.0.1-amd64-firecracker")
        archive = tmp_path / "codex.tar"
        assert main(["image", "save", "codex", "--image-dir", str(src), "-o", str(archive)]) == 0
        capsys.readouterr()

        # Control characters are rejected at load, so markup is the live threat here.
        hostile = "[link=mailto:owner@attacker.example]codex-v0.0.1-amd64-firecracker"
        with tarfile.open(archive) as tar:
            manifest = json.load(tar.extractfile("manifest.json"))
            members = [
                (m.name, tar.extractfile(m).read())
                for m in tar.getmembers()
                if m.name != "manifest.json"
            ]
        manifest["name"] = hostile
        hostile_archive = tmp_path / "hostile.tar"
        _write_archive(hostile_archive, manifest, members)

        dest = tmp_path / "dest"
        ret = main(["image", "load", "-i", str(hostile_archive), "--image-dir", str(dest)])

        assert ret == 0
        out = capsys.readouterr().out
        assert "[link=mailto:owner@attacker.example]" in out
        assert "\x1b" not in out

    def test_inspect_renders_archive_file_names_and_sidecar_literally(
        self, tmp_path: Path, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Member file names and the on-disk sidecar are untrusted: never markup or ESC."""
        monkeypatch.setenv("COLUMNS", "200")
        hostile_file = "[red]rootfs[/red].bin"
        data = b"custom-rootfs"
        # A compressed rootfs makes load restore the sidecar the manifest supplies.
        zst = zstandard.compress(b"\x00" * 16)
        manifest = {
            "schema_version": 1,
            "name": "hostile-files",
            "files": [
                {
                    "path": hostile_file,
                    "encoding": "raw",
                    "size": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                },
                {
                    "path": "rootfs.ext4.zst",
                    "encoding": "raw",
                    "size": len(zst),
                    "sha256": hashlib.sha256(zst).hexdigest(),
                },
            ],
        }
        archive = tmp_path / "hostile-files.tar"
        _write_archive(
            archive,
            manifest,
            [(f"files/{hostile_file}", data), ("files/rootfs.ext4.zst", zst)],
        )
        dest = tmp_path / "dest"
        assert main(["image", "load", "-i", str(archive), "--image-dir", str(dest)]) == 0
        capsys.readouterr()
        # Load regenerates the sidecar from the installed bytes, so the only
        # way hostile text reaches it is a rewrite of the file on disk.
        (dest / "hostile-files" / "rootfs.ext4.from-sha256").write_text(
            "[bold]sparse-v1:deadbeef\x1b]0;owned\x07"
        )

        ret = main(["image", "inspect", "hostile-files", "--image-dir", str(dest)])

        assert ret == 0
        out = capsys.readouterr().out
        assert "[red]rootfs[/red]" in out
        assert "[bold]sparse-v1:deadbeef" in out
        assert "\x1b" not in out


class TestLoadRejectsUnprintableNames:
    """Names an archive supplies must be printable so they can be shown and typed back."""

    @staticmethod
    def _archive(path: Path, name: str, member: str) -> None:
        """Write a one-file archive with the given entry name and member path."""
        data = b"custom-rootfs"
        _write_archive(
            path,
            {
                "schema_version": 1,
                "name": name,
                "files": [
                    {
                        "path": member,
                        "encoding": "raw",
                        "size": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(),
                    }
                ],
            },
            [(f"files/{member}", data)],
        )

    @pytest.mark.parametrize(
        ("name", "member"),
        [("codex\x1b]0;owned\x07", "rootfs.bin"), ("codex", "root\x1bfs.bin")],
        ids=["entry-name", "member-path"],
    )
    def test_control_characters_are_rejected(
        self, tmp_path: Path, capsys: pytest.CaptureFixture, name: str, member: str
    ) -> None:
        """Load refuses archives whose name or member path has control characters."""
        archive = tmp_path / "bad.tar"
        self._archive(archive, name, member)
        dest = tmp_path / "dest"

        ret = main(["image", "load", "-i", str(archive), "--image-dir", str(dest), "--json"])

        assert ret == 2
        payload = json.loads(capsys.readouterr().out)
        assert payload["error"]["code"] == "invalid_input"
        assert not dest.exists() or not any(dest.iterdir())

    def test_error_hints_quote_the_archive_name(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """A name with shell metacharacters must be quoted in the suggested command."""
        name = "my image$(id)"
        data = b"custom-rootfs"
        archive = tmp_path / "extra.tar"
        _write_archive(
            archive,
            {
                "schema_version": 1,
                "name": name,
                "files": [
                    {
                        "path": "rootfs.bin",
                        "encoding": "raw",
                        "size": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(),
                    }
                ],
            },
            [("files/rootfs.bin", data), ("files/undeclared.bin", b"x")],
        )
        dest = tmp_path / "dest"

        ret = main(["image", "load", "-i", str(archive), "--image-dir", str(dest), "--json"])

        assert ret == 2
        payload = json.loads(capsys.readouterr().out)
        assert "celesto image save 'my image$(id)' -o" in payload["error"]["recovery"]


class TestSaveAndLoadAgreeOnNames:
    """Save refuses what load would reject, and both keep control characters off the terminal."""

    @staticmethod
    def _entry(root: Path, name: str, file_name: str = "rootfs.ext4") -> Path:
        """Create a minimal cache entry directory with one data file."""
        entry = root / name
        entry.mkdir(parents=True)
        (entry / file_name).write_bytes(b"x" * 10)
        return entry

    def test_save_rejects_entry_name_with_control_characters(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """An entry whose folder name carries ESC cannot be saved."""
        name = "codex\x1b]0;owned\x07"
        self._entry(tmp_path / "src", name)
        archive = tmp_path / "out.tar"

        ret = main(
            [
                "image",
                "save",
                name,
                "--image-dir",
                str(tmp_path / "src"),
                "-o",
                str(archive),
                "--json",
            ]
        )

        assert ret == 2
        payload = json.loads(capsys.readouterr().out)
        assert payload["error"]["code"] == "invalid_input"
        assert "\x1b" not in payload["error"]["message"]
        assert "\x1b" not in payload["error"]["recovery"]
        assert not archive.exists()

    def test_save_rejects_file_name_with_control_characters(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """A file inside the entry whose name carries ESC cannot be saved."""
        self._entry(tmp_path / "src", "codex", file_name="root\x1bfs.bin")
        archive = tmp_path / "out.tar"

        ret = main(
            [
                "image",
                "save",
                "codex",
                "--image-dir",
                str(tmp_path / "src"),
                "-o",
                str(archive),
                "--json",
            ]
        )

        assert ret == 2
        payload = json.loads(capsys.readouterr().out)
        assert payload["error"]["code"] == "invalid_input"
        assert "\x1b" not in payload["error"]["message"]
        assert "\x1b" not in payload["error"]["recovery"]
        assert not archive.exists()

    def test_save_output_path_is_shown_without_control_characters(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """The Saved line and its suggested load command never carry ESC from -o."""
        self._entry(tmp_path / "src", "codex")
        archive = tmp_path / "out\x1b]0;owned\x07.tar"

        ret = main(
            ["image", "save", "codex", "--image-dir", str(tmp_path / "src"), "-o", str(archive)]
        )

        assert ret == 0
        assert "\x1b" not in capsys.readouterr().out

    def test_load_error_hints_show_input_path_without_control_characters(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Load error messages sanitize the archive path before quoting it."""
        data = b"custom-rootfs"
        archive = tmp_path / "in\x1b]0;owned\x07.tar"
        _write_archive(
            archive,
            {
                "schema_version": 1,
                "name": "codex",
                "files": [
                    {
                        "path": "rootfs.bin",
                        "encoding": "raw",
                        "size": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(),
                    }
                ],
            },
            [("files/rootfs.bin", data), ("files/undeclared.bin", b"x")],
        )

        ret = main(
            ["image", "load", "-i", str(archive), "--image-dir", str(tmp_path / "dest"), "--json"]
        )

        assert ret == 2
        payload = json.loads(capsys.readouterr().out)
        assert "\x1b" not in payload["error"]["message"]
        assert "\x1b" not in payload["error"]["recovery"]

    def test_save_retry_command_shell_quotes_the_image_name(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """A recovery hint that embeds the image name must be safe to paste into a shell."""
        name = "my image$(id)"
        self._entry(tmp_path / "src", name)
        # A regular file where a directory is needed fails the write for every
        # user, root included, unlike a chmod-based setup.
        blocker = tmp_path / "blocker"
        blocker.write_bytes(b"")
        ret = main(
            [
                "image",
                "save",
                name,
                "--image-dir",
                str(tmp_path / "src"),
                "-o",
                str(blocker / "out.tar"),
                "--json",
            ]
        )

        assert ret != 0
        payload = json.loads(capsys.readouterr().out)
        recovery = payload["error"]["recovery"]
        assert "$(id)" not in recovery.replace("'my image$(id)'", "")
        assert "'my image$(id)'" in recovery

    def test_missing_image_error_shows_name_without_control_characters(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """A single-segment name with ESC that matches nothing is echoed sanitized."""
        (tmp_path / "src").mkdir()
        name = "codex\x1b]0;owned\x07"

        ret = main(
            [
                "image",
                "save",
                name,
                "--image-dir",
                str(tmp_path / "src"),
                "-o",
                str(tmp_path / "out.tar"),
                "--json",
            ]
        )

        assert ret != 0
        payload = json.loads(capsys.readouterr().out)
        assert "\x1b" not in payload["error"]["message"]
        assert "\x1b" not in payload["error"]["recovery"]

    @pytest.mark.parametrize("requested", ["custom/web", "custom/web/a"])
    def test_ambiguous_match_error_shows_names_without_control_characters(
        self, requested: str, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Folder names listed for an ambiguous name or prefix are echoed sanitized."""
        root = tmp_path / "src"
        self._entry(root, "custom/web/a1")
        self._entry(root, "custom/web/a2\x1b]0;owned\x07")

        ret = main(
            [
                "image",
                "save",
                requested,
                "--image-dir",
                str(root),
                "-o",
                str(tmp_path / "out\x1b]0;owned\x07.tar"),
                "--json",
            ]
        )

        assert ret == 2
        payload = json.loads(capsys.readouterr().out)
        assert "matches more than one" in payload["error"]["message"]
        assert "custom/web/a2]0;owned" in payload["error"]["message"]
        assert "\x1b" not in payload["error"]["message"]
        assert "\x1b" not in payload["error"]["recovery"]

    def test_load_open_error_shows_exception_text_without_control_characters(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """A missing archive whose path carries ESC is reported without the escape."""
        archive = tmp_path / "missing\x1b]0;owned\x07.tar"

        ret = main(
            ["image", "load", "-i", str(archive), "--image-dir", str(tmp_path / "dest"), "--json"]
        )

        assert ret != 0
        payload = json.loads(capsys.readouterr().out)
        assert "\x1b" not in payload["error"]["message"]
        assert "\x1b" not in payload["error"]["recovery"]

    def test_save_write_error_shows_output_path_without_control_characters(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """A failed archive write never echoes ESC from the -o path."""
        self._entry(tmp_path / "src", "codex")
        blocker = tmp_path / "blk\x1b]0;owned\x07"
        blocker.write_bytes(b"")

        ret = main(
            [
                "image",
                "save",
                "codex",
                "--image-dir",
                str(tmp_path / "src"),
                "-o",
                str(blocker / "out.tar"),
                "--json",
            ]
        )

        assert ret != 0
        payload = json.loads(capsys.readouterr().out)
        assert "Could not write" in payload["error"]["message"]
        assert "\x1b" not in payload["error"]["message"]
        assert "\x1b" not in payload["error"]["recovery"]

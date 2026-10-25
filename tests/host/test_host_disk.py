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

"""Tests for host disk helper fallback boundaries."""

import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from celesto.host import disk


def test_clone_or_sparse_copy_prefers_cp_before_native(tmp_path: Path) -> None:
    """GNU cp should stay the production default for raw disk clones."""
    source = tmp_path / "source.ext4"
    target = tmp_path / "target.ext4"
    core_disk = MagicMock()

    with (
        patch.object(disk, "_cp_clone_or_sparse_copy", return_value="cp") as mock_cp,
        patch.object(disk, "_native_available", side_effect=AssertionError("native skipped")),
        patch.object(disk, "core_disk", core_disk),
    ):
        assert disk.clone_or_sparse_copy(source, target) == "cp"

    mock_cp.assert_called_once_with(source, target)
    core_disk.clone_or_sparse_copy.assert_not_called()


def test_clone_or_sparse_copy_uses_native_after_cp_failure(tmp_path: Path) -> None:
    """Native copy remains available after cp cannot handle the clone."""
    source = tmp_path / "source.ext4"
    target = tmp_path / "target.ext4"
    core_disk = MagicMock()
    core_disk.clone_or_sparse_copy.return_value = "sparse"

    with (
        patch.object(disk, "_cp_clone_or_sparse_copy", return_value=None) as mock_cp,
        patch.object(disk, "_native_available", return_value=True),
        patch.object(disk, "core_disk", core_disk),
        patch.object(shutil, "copystat") as mock_copystat,
        patch.object(
            disk,
            "_python_clone_or_sparse_copy",
            side_effect=AssertionError("must not fall back"),
        ),
    ):
        assert disk.clone_or_sparse_copy(source, target) == "native:sparse"

    mock_cp.assert_called_once_with(source, target)
    core_disk.clone_or_sparse_copy.assert_called_once_with(str(source), str(target))
    mock_copystat.assert_called_once_with(source, target)


def test_clone_or_sparse_copy_uses_python_when_cp_and_native_unavailable(tmp_path: Path) -> None:
    """Disk copies should keep the Python sparse fallback path."""
    source = tmp_path / "source.ext4"
    target = tmp_path / "target.ext4"

    with (
        patch.object(disk, "_cp_clone_or_sparse_copy", return_value=None) as mock_cp,
        patch.object(disk, "_native_available", return_value=False),
        patch.object(disk, "_python_clone_or_sparse_copy", return_value="sparse") as mock_python,
    ):
        assert disk.clone_or_sparse_copy(source, target) == "sparse"

    mock_cp.assert_called_once_with(source, target)
    mock_python.assert_called_once_with(source, target)


def test_clone_or_sparse_copy_propagates_native_oserror(tmp_path: Path) -> None:
    """Native copy failures after invocation must not silently recopy in Python."""
    core_disk = MagicMock()
    core_disk.clone_or_sparse_copy.side_effect = OSError("No space left on device")

    with (
        patch.object(disk, "_cp_clone_or_sparse_copy", return_value=None),
        patch.object(disk, "_native_available", return_value=True),
        patch.object(disk, "core_disk", core_disk),
        patch.object(
            disk,
            "_python_clone_or_sparse_copy",
            side_effect=AssertionError("must not fall back"),
        ),
        pytest.raises(OSError, match="No space left on device"),
    ):
        disk.clone_or_sparse_copy(tmp_path / "source.ext4", tmp_path / "target.ext4")


def test_decompress_zstd_sparse_propagates_native_oserror(tmp_path: Path) -> None:
    """Native decompression failures after invocation must remain visible."""
    core_disk = MagicMock()
    core_disk.decompress_zstd_sparse.side_effect = OSError("corrupt zstd stream")

    with (
        patch.object(disk, "_native_available", return_value=True),
        patch.object(disk, "core_disk", core_disk),
        patch.object(
            disk,
            "_python_decompress_zstd_sparse",
            side_effect=AssertionError("must not fall back"),
        ),
        pytest.raises(OSError, match="corrupt zstd stream"),
    ):
        disk.decompress_zstd_sparse(tmp_path / "rootfs.ext4.zst", tmp_path / "rootfs.ext4")


@pytest.mark.parametrize("size,limit", [(9, 8), (9, 9), (0, 0)])
@pytest.mark.parametrize("native", [False, True])
def test_bounded_decompression_preserves_target_on_rejection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, size: int, limit: int, native: bool
) -> None:
    import zstandard

    monkeypatch.setenv("CELESTO_DISABLE_NATIVE_DISK", "0" if native else "1")
    if native and not disk.has_native_disk_io():
        pytest.skip("native disk extension is unavailable")
    source = tmp_path / "image.zst"
    target = tmp_path / "image"
    source.write_bytes(zstandard.ZstdCompressor().compress(b"x" * size))
    target.write_bytes(b"existing image")
    if size > limit:
        with pytest.raises(OSError, match="limit") as failure:
            disk.decompress_zstd_sparse(source, target, chunk_size=4, max_output_bytes=limit)
        assert isinstance(failure.value, disk.ImageSizeLimitError)
        assert target.read_bytes() == b"existing image"
    else:
        disk.decompress_zstd_sparse(source, target, chunk_size=4, max_output_bytes=limit)
        assert target.read_bytes() == b"x" * size
    assert sorted(path.name for path in tmp_path.iterdir()) == ["image", "image.zst"]


def test_python_decompress_preserves_symlink_victim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import zstandard

    monkeypatch.setenv("CELESTO_DISABLE_NATIVE_DISK", "1")
    source = tmp_path / "image.zst"
    target = tmp_path / "image"
    victim = tmp_path / "victim"
    source.write_bytes(zstandard.ZstdCompressor().compress(b"decoded image"))
    victim.write_bytes(b"private existing contents")
    (tmp_path / "image.tmp").symlink_to(victim)
    disk.decompress_zstd_sparse(source, target)
    assert target.read_bytes() == b"decoded image"
    assert victim.read_bytes() == b"private existing contents"

"""Sparse disk-image helpers."""

import celesto_core._ffi as _ffi


def available() -> bool:
    """Return True when this wheel includes native disk/image helpers."""

    return bool(_ffi.has_native_disk_io())


def clone_or_sparse_copy(source: str, target: str) -> str:
    """Copy a disk image using reflink or sparse-preserving native I/O."""

    return str(_ffi.clone_or_sparse_copy(source, target))


def decompress_zstd_sparse(
    source: str, target: str, chunk_size: int = 1048576, max_output_bytes: int | None = None
) -> str:
    """Decompress an image, rejecting decoded bytes above max_output_bytes when supplied."""

    if max_output_bytes is None:
        return str(_ffi.decompress_zstd_sparse(source, target, chunk_size))
    return str(
        _ffi.decompress_zstd_sparse(source, target, chunk_size, max_output_bytes=max_output_bytes)
    )


__all__ = [
    "available",
    "clone_or_sparse_copy",
    "decompress_zstd_sparse",
]

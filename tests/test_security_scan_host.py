"""Regression probes for the host trust boundaries reported by the security scan."""

import asyncio
import io
import struct
import tarfile
from pathlib import Path
from typing import cast

import pytest

from celesto.comm.rust_http_vsock_channel import _safe_extract_tar
from celesto.exceptions import CelestoError
from celesto.images.builder import ImageBuilder
from celesto.vm import CelestoManager


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize(
    "identifier", ["..", ".", "../victim", "/tmp/victim", "name/../victim", "name/../../keep"]
)
def test_delete_rejects_unsafe_identifier_before_cleanup(
    tmp_path: Path, identifier: str, asynchronous: bool
) -> None:
    data = tmp_path / "data"
    manager = CelestoManager(data_dir=data, socket_dir=tmp_path / "sockets", backend="qemu")
    (data / "firmware").mkdir()
    sentinel = data / "keep"
    sentinel.write_text("private data")
    socket_sentinel = tmp_path / "keep.sock"
    socket_sentinel.write_text("unrelated control socket")
    for prefix in ("fc-", "qmp-"):
        (tmp_path / "sockets" / f"{prefix}name").mkdir(parents=True)
    try:
        with pytest.raises(ValueError):
            if asynchronous:
                asyncio.run(manager.async_delete(identifier))
            else:
                manager.delete(identifier)
        assert sentinel.read_text() == "private data"
        assert socket_sentinel.read_text() == "unrelated control socket"
    finally:
        manager.close()


@pytest.mark.parametrize("size", ["16; touch /tmp/should-not-exist", True, 0, -1, 1.5])
def test_ext4_helper_rejects_invalid_size_before_any_io(
    tmp_path: Path, size: str | int | float
) -> None:
    builder = ImageBuilder.__new__(ImageBuilder)
    with pytest.raises(ValueError, match="positive integer"):
        builder._create_ext4_with_docker(
            tmp_path / "missing.tar", tmp_path / "disk.ext4", cast(int, size), tmp_path
        )


def test_directory_download_rejects_sparse_member_before_writing(tmp_path: Path) -> None:
    blob = io.BytesIO()
    with tarfile.open(fileobj=blob, mode="w", format=tarfile.GNU_FORMAT) as tar:
        member = tarfile.TarInfo("expanded")
        member.type = tarfile.GNUTYPE_SPARSE
        member.size = 0
        tar.addfile(member)
    destination = tmp_path / "download"
    with pytest.raises(CelestoError, match="sparse"):
        _safe_extract_tar(blob.getvalue(), destination)
    assert not (destination / "expanded").exists()


@pytest.mark.parametrize("version,offset,length,features", [(2, 512, 8, 0), (3, 0, 0, 4)])
def test_untrusted_qcow_references_rejected_before_overlay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    version: int,
    offset: int,
    length: int,
    features: int,
) -> None:
    header = bytearray(104)
    struct.pack_into(">IIQI", header, 0, 0x514649FB, version, offset, length)
    struct.pack_into(">Q", header, 72, features)
    disk = tmp_path / "untrusted.qcow2"
    disk.write_bytes(header)
    manager = CelestoManager(
        data_dir=tmp_path / "data", socket_dir=tmp_path / "sockets", backend="qemu"
    )
    monkeypatch.setattr(manager, "_find_qemu_img_binary", lambda: Path("/not-run/qemu-img"))
    try:
        with pytest.raises(CelestoError, match="external"):
            manager._create_qemu_overlay_disk(disk, tmp_path / "overlay.qcow2")
    finally:
        manager.close()


def test_manually_constructed_api_server_is_not_unauthenticated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from fastapi.testclient import TestClient

    from celesto.server.app import create_app

    monkeypatch.delenv("CELESTO_SERVER_TOKEN", raising=False)
    app = create_app()
    client = TestClient(app)
    assert client.get("/openapi.json").status_code == 401
    assert (
        client.get(
            "/openapi.json", headers={"Authorization": f"Bearer {app.state.auth_token}"}
        ).status_code
        == 200
    )

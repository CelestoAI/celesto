"""Exercise HTTP download cleanup with a controlled guest transport.

Failure inventory: canceled sandbox/browser reads delete a file before a late
download writes it again; failed downloads leak partial content; successful reads
return the wrong bytes or bypass the receive limit. The real authenticated ASGI
routes, executor and filesystem run; only the guest transport is synthetic so its
completion order can be forced without a VM.
"""

import asyncio
import json
import threading
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
import pytest

pytest.importorskip("fastapi")

from celesto.exceptions import CelestoError
from celesto.server.app import create_app


@pytest.mark.asyncio
@pytest.mark.parametrize("resource", ["sandboxes", "browser-sessions"])
@pytest.mark.parametrize("cancel", [False, True], ids=["complete", "cancel"])
@pytest.mark.parametrize("fail", [False, True], ids=["success", "failure"])
async def test_file_read_cleans_up_after_worker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    resource: str,
    cancel: bool,
    fail: bool,
) -> None:
    loop = asyncio.get_running_loop()
    entered = asyncio.Event()
    worker_done = asyncio.Event()
    started = threading.Event()
    release = threading.Event()
    paths: list[Path] = []
    to_thread = asyncio.to_thread

    async def observed_thread(function: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        def run() -> Any:
            try:
                return function(*args, **kwargs)
            finally:
                if started.is_set():
                    loop.call_soon_threadsafe(worker_done.set)

        return await to_thread(run)

    # Observe completion of the whole submitted operation, including its cleanup.
    # The real to_thread still owns scheduling and cancellation semantics.
    monkeypatch.setattr(asyncio, "to_thread", observed_thread)

    def download(remote: str, destination: Path, *, max_bytes: int) -> None:
        assert remote == "/saved.bin"
        assert max_bytes == 16 * 1024 * 1024
        paths.append(destination)
        started.set()
        loop.call_soon_threadsafe(entered.set)
        assert release.wait(timeout=5), "The test did not release its guest transport"
        destination.write_bytes(b"saved")
        if fail:
            raise CelestoError("Synthetic guest transfer failure")

    vm = SimpleNamespace(
        run=lambda *_args: SimpleNamespace(exit_code=0, stdout="5", stderr=""),
        download_file=download,
    )
    app = create_app(auth_token="synthetic-cleanup-test")
    if resource == "sandboxes":
        app.state.sandboxes["probe"] = vm
    else:
        app.state.browser_sessions["probe"] = SimpleNamespace(vm=vm)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": "Bearer synthetic-cleanup-test"},
    ) as client:
        request = asyncio.create_task(
            client.get(f"/{resource}/probe/files", params={"path": "/saved.bin"})
        )
        try:
            await asyncio.wait_for(entered.wait(), timeout=5)
            if cancel:
                request.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await request
            release.set()
            if not cancel:
                response = await asyncio.wait_for(request, timeout=5)
                assert response.status_code == (409 if fail else 200)
                if not fail:
                    assert response.content == b"saved"
            await asyncio.wait_for(worker_done.wait(), timeout=5)
            remaining = [str(path) for path in paths if path.exists()]
            (tmp_path / "file-cleanup.json").write_text(
                json.dumps(
                    {"resource": resource, "cancel": cancel, "fail": fail, "remaining": remaining}
                )
            )
            assert paths, "The request did not reach the guest transport"
            assert not remaining, "Downloaded content survived after its worker completed"
        finally:
            release.set()
            if not request.done():
                request.cancel()
            await asyncio.gather(request, return_exceptions=True)
            if started.is_set():
                await asyncio.wait_for(worker_done.wait(), timeout=5)
            for path in paths:
                path.unlink(missing_ok=True)

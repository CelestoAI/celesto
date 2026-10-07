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

"""Forks that must be refused up front, and the saved-copy-left-behind warning.

``tests/e2e/test_fork_engine.py`` refuses a taken name, a paused source and a
shared folder on real sandboxes. The other refusals need a source a real run
can't easily make: one from an older image, one in an error state, a full
disk, no free ports, a guest that stops answering, an unsupported backend or
guest, or a name at the length limit. Failure modes, written before the
tests:

1. A refusal is raised with words other than the decision log's (D1b), or
   with a placeholder instead of the actual sandbox name.
2. A refusal comes after the source was flushed, paused or copied, or after
   a child or a generation (saved copy) was created.
3. A source from an older image is forked anyway, whichever way the image is
   detected: no instance ID in its config, a recorded identity without one,
   or a running guest that says it doesn't support instance IDs.
4. A stopped source from a current image with no recorded identity is
   forked with nothing to compare its children against, or refused with the
   older-image message instead of "hasn't finished its first start".
5. A count outside 1 to 10 reaches the engine, or suggests the wrong
   ``--count``; the CLI has no range check of its own.
6. The disk space and port messages say "1 times" or "1 new sandboxes".
7. A guest that doesn't answer the flush, or the identity read, surfaces as
   a raw transport error instead of the "didn't respond" message.
8. A generation that can't be deleted fails the fork, or is dropped silently
   instead of a warning naming the exact command to remove it.
9. The CLI's ``--json`` output carries a different message, or exits 0.

The disk copy, hypervisor and guest agent are replaced at their boundaries
(the ``world`` fixture from ``test_fork_children.py``); the fork's checks,
locks and generation are real.
"""

from __future__ import annotations

import json
from collections import namedtuple
from pathlib import Path
from typing import Any

import pytest

from celesto._fork import (
    child_failed_message,
    count_message,
    disk_space_message,
    identity_not_confirmed_message,
)
from celesto.cli import main as cli_main
from celesto.cli.main import main
from celesto.comm.rust_http_vsock_channel import RustHttpVsockChannel
from celesto.exceptions import CelestoError
from celesto.facade import Celesto
from celesto.types import GuestOS, MacOSMachineConfig, NetworkConfig, VMIdentity, VMState
from celesto.vm import CelestoManager
from tests.vm.test_fork_children import (  # noqa: F401 - fixture
    _SOURCE_FINGERPRINT,
    _SOURCE_MACHINE_ID,
    _World,
    world,
)

_OLDER_IMAGE = (
    "Sandbox '{name}' was created from an older image and can't be forked. "
    "Run 'celesto image pull --all', then create a new sandbox with "
    "'celesto sandbox create' and fork that one."
)
_FIRST_START = (
    "Sandbox '{name}' hasn't finished its first start, so it can't be forked yet. "
    "Run 'celesto sandbox start {name}', then fork again."
)
_FLUSH_FAILED = (
    "Sandbox '{name}' didn't respond when saving its files. "
    "Run 'celesto sandbox stop {name}', then fork again."
)


def _source(
    world: _World,  # noqa: F811
    *,
    name: str = "src",
    backend: str = "firecracker",
    status: VMState = VMState.STOPPED,
    record: str = "full",
    **config_update: Any,
) -> Celesto:
    """Add a source sandbox; *record* is "full", "no-instance-id" or "none"."""
    config = world.config(name, backend, **config_update)
    world.state.create_vm(config)
    world.state.update_vm(
        name,
        status=status,
        network=NetworkConfig(
            guest_ip="172.16.0.2",
            gateway_ip="172.16.0.1",
            netmask="255.255.255.252",
            tap_device="tap-src",
            guest_mac="06:00:ac:10:00:02",
            ssh_host_port=2222,
        ),
    )
    if record != "none":
        world.state.record_vm_identity(
            name,
            VMIdentity(
                instance_id=config.instance_id if record == "full" else None,
                ssh_host_key_fingerprint=_SOURCE_FINGERPRINT,
                machine_id=_SOURCE_MACHINE_ID,
            ),
        )
    return Celesto.from_id(name, state_manager=world.state, data_dir=world.manager.data_dir)


def _refused(world: _World, source: Celesto, count: int = 1, **kwargs: Any) -> str:  # noqa: F811
    """Fork, expect a refusal, and check nothing was flushed, copied or created."""
    sandboxes = sorted(vm.vm_id for vm in world.state.list_vms())
    flushes: list[str] = []
    original_sync = RustHttpVsockChannel.sync

    def counting_sync(channel: RustHttpVsockChannel, timeout: int = 10) -> None:
        flushes.append(channel.sandbox_name)
        original_sync(channel, timeout=timeout)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(RustHttpVsockChannel, "sync", counting_sync)
        with pytest.raises(CelestoError) as caught:
            source._fork_many(count, boot_timeout=30, **kwargs)
    assert world.capture_policies == []
    assert world.created == []
    assert world.generations() == []
    assert sorted(vm.vm_id for vm in world.state.list_vms()) == sandboxes
    assert flushes == [] or str(caught.value) == _FLUSH_FAILED.format(name=source.vm_id)
    return str(caught.value)


# -- older image (3) and first start (17) ---------------------------------


def test_a_source_without_an_instance_id_is_from_an_older_image(world: _World) -> None:  # noqa: F811
    source = _source(world, status=VMState.RUNNING, record="none", instance_id=None)

    assert _refused(world, source) == _OLDER_IMAGE.format(name="src")


def test_a_recorded_identity_without_an_instance_id_is_from_an_older_image(
    world: _World,  # noqa: F811
) -> None:
    source = _source(world, status=VMState.RUNNING, record="no-instance-id")

    assert _refused(world, source) == _OLDER_IMAGE.format(name="src")


def test_a_running_guest_without_instance_id_support_is_from_an_older_image(
    world: _World,  # noqa: F811
) -> None:
    source = _source(world, status=VMState.RUNNING, record="none")
    world.guest_output = lambda vm_id: "supports_instance_id=0\n"  # type: ignore[method-assign]

    assert _refused(world, source) == _OLDER_IMAGE.format(name="src")


def test_a_stopped_source_never_started_must_finish_its_first_start(
    world: _World,  # noqa: F811
) -> None:
    source = _source(world, status=VMState.STOPPED, record="none")

    assert _refused(world, source) == _FIRST_START.format(name="src")


# -- state (2), count (8), backend (5), guest (6) --------------------------


def test_a_source_in_an_error_state_is_refused(world: _World) -> None:  # noqa: F811
    source = _source(world, status=VMState.ERROR)

    assert _refused(world, source) == (
        "Sandbox 'src' is in an error state and can't be forked. "
        "Run 'celesto sandbox logs src' to see what went wrong."
    )


@pytest.mark.parametrize(("count", "suggested"), [(0, 1), (-1, 1), (11, 10), (25, 10)])
def test_a_count_outside_one_to_ten_is_refused(
    world: _World,  # noqa: F811
    count: int,
    suggested: int,
) -> None:
    source = _source(world)

    assert _refused(world, source, count) == (
        f"You can fork 1 to 10 sandboxes at a time; you asked for {count}. "
        f"Run 'celesto sandbox fork src --count {suggested}'."
    )


def test_count_retry_keeps_the_requested_name() -> None:
    assert count_message("demo", 11, "exp") == (
        "You can fork 1 to 10 sandboxes at a time; you asked for 11. "
        "Run 'celesto sandbox fork demo --name exp --count 10'."
    )


def test_retry_messages_include_exact_commands_and_count() -> None:
    assert identity_not_confirmed_message("exp-1", "demo").endswith(
        "Run 'celesto sandbox fork demo --name exp-1'."
    )
    assert child_failed_message("exp-1", "demo").endswith(
        "Run 'celesto sandbox fork demo --name exp-1'."
    )
    assert disk_space_message("demo", 11, 12_000_000_000, 1_000_000_000).endswith(
        "Free up space, then run 'celesto sandbox fork demo --count 5'."
    )


def test_a_libkrun_source_is_refused(world: _World) -> None:  # noqa: F811
    source = _source(world, backend="libkrun")

    assert _refused(world, source) == (
        "Sandbox 'src' uses an engine that can't be forked yet. "
        "Run 'celesto sandbox create --name src-qemu --backend qemu', then "
        "run 'celesto sandbox fork src-qemu'."
    )


@pytest.mark.parametrize(
    ("config_update", "message"),
    [
        (
            {
                "guest_os": GuestOS.MACOS,
                "backend": "vz",
                "boot_mode": "platform",
                "kernel_path": None,
                "rootfs_path": None,
                "comm_channel": "ssh",
                "vsock": None,
                "macos_machine": MacOSMachineConfig(
                    base_image="macos-latest",
                    manifest_path=Path("/nonexistent/manifest.json"),
                    bundle_path=Path("/nonexistent/vm.bundle"),
                    guest_version="26.0",
                ),
            },
            "Sandbox 'src' runs macOS and can't be forked yet. "
            "Create 'celesto sandbox create --name src-linux --os linux', then "
            "run 'celesto sandbox fork src-linux'.",
        ),
        (
            {
                "guest_os": GuestOS.WINDOWS,
                "backend": "qemu",
                "boot_mode": "firmware",
                "kernel_path": None,
            },
            "Sandbox 'src' runs Windows and can't be forked yet. "
            "Create 'celesto sandbox create --name src-linux --os linux', then "
            "run 'celesto sandbox fork src-linux'.",
        ),
    ],
    ids=["macos", "windows"],
)
def test_macos_and_windows_sandboxes_are_refused(
    world: _World,  # noqa: F811
    config_update: dict[str, Any],
    message: str,
) -> None:
    source = _source(world, **config_update)

    assert _refused(world, source) == message


# -- names (18, 19) --------------------------------------------------------


@pytest.mark.parametrize("count", [1, 2])
def test_a_name_that_is_not_a_sandbox_name_is_refused(world: _World, count: int) -> None:  # noqa: F811
    source = _source(world)

    assert _refused(world, source, count, name="Exp") == (
        "'Exp' can't be used as a sandbox name. Use up to 64 lowercase letters, "
        "numbers, hyphens or underscores, starting and ending with a letter or number."
    )


def test_a_source_name_too_long_to_number_is_refused(world: _World) -> None:  # noqa: F811
    long_name = "a" * 64
    source = _source(world, name=long_name)

    assert _refused(world, source) == (
        f"Sandbox '{long_name}' has a name too long to number its forks. "
        "Choose a shorter name with '--name'."
    )


# -- disk space (10) and ports (11) ----------------------------------------

_Usage = namedtuple("_Usage", "total used free")


@pytest.mark.parametrize(
    ("count", "message"),
    [
        (
            3,
            "Forking 'src' 3 times needs about 10.4 GB, but only 3.1 GB is free. "
            "Free up space, then run 'celesto sandbox fork src --count 1'.",
        ),
        (
            1,
            "Forking 'src' once needs about 5.2 GB, but only 3.1 GB is free. "
            "Free up space, then run 'celesto sandbox fork src --count 1'.",
        ),
    ],
)
def test_a_fork_that_will_not_fit_on_disk_is_refused(
    world: _World,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    count: int,
    message: str,
) -> None:
    source = _source(world)
    # The source disk really uses 2.6 GB; a stopped source's generation and
    # each child cost that much again.
    monkeypatch.setattr(CelestoManager, "_allocated_bytes", staticmethod(lambda path: 2.6e9))
    monkeypatch.setattr("celesto.vm.shutil.disk_usage", lambda path: _Usage(500e9, 496.9e9, 3.1e9))

    assert _refused(world, source, count) == message


@pytest.mark.parametrize(("count", "sandboxes"), [(3, "3 new sandboxes"), (1, "1 new sandbox")])
def test_a_fork_without_enough_free_ports_is_refused(
    world: _World,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    count: int,
    sandboxes: str,
) -> None:
    source = _source(world)
    monkeypatch.setattr(CelestoManager, "_local_ssh_port_is_available", lambda *a, **k: False)

    assert _refused(world, source, count) == (
        f"Not enough free ports for {sandboxes}. "
        "Run 'celesto sandbox list' to find sandboxes you can delete."
    )


# -- the guest stops answering (12) ----------------------------------------


def test_a_source_that_does_not_answer_the_flush_is_refused_before_the_copy(
    world: _World,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _source(world, status=VMState.RUNNING)

    def no_answer(self: RustHttpVsockChannel, timeout: int = 10) -> None:
        raise TimeoutError("guest agent did not answer")

    monkeypatch.setattr(RustHttpVsockChannel, "sync", no_answer)

    assert _refused(world, source) == _FLUSH_FAILED.format(name="src")
    assert world.state.get_vm("src").status == VMState.RUNNING


def test_a_source_that_does_not_answer_the_identity_read_is_refused(
    world: _World,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _source(world, status=VMState.RUNNING, record="none")

    def no_answer(self: RustHttpVsockChannel, *args: Any, **kwargs: Any) -> None:
        raise TimeoutError("guest agent did not answer")

    monkeypatch.setattr(RustHttpVsockChannel, "run", no_answer)

    assert _refused(world, source) == _FLUSH_FAILED.format(name="src")


# -- the generation can't be deleted (21) ----------------------------------


def test_a_generation_that_cannot_be_deleted_is_a_warning_with_the_command(
    world: _World,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _source(world)
    original_delete = CelestoManager.delete_snapshot

    def stuck(self: CelestoManager, snapshot_id: str) -> None:
        raise OSError("device busy")

    monkeypatch.setattr(CelestoManager, "delete_snapshot", stuck)

    batch = source._fork_many(2, boot_timeout=30)

    assert [(child.name, child.ok) for child in batch.children] == [
        ("src-1", True),
        ("src-2", True),
    ]
    listed = [s.snapshot_id for s in world.manager.list_snapshots(vm_id="src")]
    assert len(listed) == 1 and listed[0].startswith("fork-src-"), listed
    assert batch.warnings == (
        f"The fork of 'src' left a saved copy behind. Run 'celesto sandbox snapshot "
        f"delete {listed[0]}' to remove it.",
    )
    # The command in the warning really removes it.
    original_delete(world.manager, listed[0])
    assert world.generations() == []


# -- through the CLI --------------------------------------------------------


@pytest.mark.parametrize(
    ("setup", "args", "message"),
    [
        (
            {},
            ["--count", "25"],
            "Invalid value for --count: You can fork 1 to 10 sandboxes at a time; "
            "you asked for 25. "
            "Run 'celesto sandbox fork src --count 10'.",
        ),
        (
            {},
            ["--count", "0"],
            "Invalid value for --count: You can fork 1 to 10 sandboxes at a time; "
            "you asked for 0. "
            "Run 'celesto sandbox fork src --count 1'.",
        ),
        (
            {"backend": "libkrun"},
            [],
            "Sandbox 'src' uses an engine that can't be forked yet. "
            "Run 'celesto sandbox create --name src-qemu --backend qemu', then "
            "run 'celesto sandbox fork src-qemu'.",
        ),
    ],
    ids=["count-25", "count-0", "libkrun"],
)
def test_cli_json_reports_the_refusal_and_exits_1(
    world: _World,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    setup: dict[str, Any],
    args: list[str],
    message: str,
) -> None:
    source = _source(world, **setup)
    monkeypatch.setattr(cli_main, "_cli_vm_from_id", lambda vm_id, **_: source)

    code = main(["sandbox", "fork", "src", *args, "--json"])

    out, _err = capsys.readouterr()
    envelope = json.loads(out)
    assert code == (2 if "--count" in args else 1)
    assert envelope["ok"] is False
    assert envelope["error"]["message"] == message
    assert world.created == []
    assert world.generations() == []

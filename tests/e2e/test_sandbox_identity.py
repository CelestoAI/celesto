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

"""Every sandbox has its own identity, and keeps it across restart and restore.

Drives the real CLI (``celesto sandbox ...``) against a locally built Alpine
image, so the image's startup script is the one in this checkout. Each run
writes a JSON artifact with every sandbox's instance ID, SSH host key
fingerprint and machine ID before and after a restart and a snapshot restore.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import uuid
from contextlib import suppress
from pathlib import Path
from typing import Any

import pytest
from _util import BOOT_TIMEOUT, E2E_BACKENDS, e2e_artifact_dir, require_e2e_backend

from celesto.cli._sqlite import SQLiteStateManager
from celesto.vm import resolve_data_dir

pytestmark = pytest.mark.e2e

_HEX32 = re.compile(r"^[0-9a-f]{32}$")
_CLI_MAIN = "from celesto.cli.main import main; raise SystemExit(main())"

# Read straight from the guest with its own tools, independent of how the host
# records identity, so the database check below compares two separate sources.
_GUEST_IDENTITY_SCRIPT = (
    "printf 'instance_id=%s\\n' \"$(cat /etc/celesto/instance-id 2>/dev/null)\"; "
    "printf 'machine_id=%s\\n' \"$(cat /etc/machine-id 2>/dev/null)\"; "
    "printf 'dbus_machine_id=%s\\n' \"$(cat /var/lib/dbus/machine-id 2>/dev/null)\"; "
    "printf 'fingerprint=%s\\n' "
    "\"$(ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub 2>/dev/null | awk '{print $2}')\"; "
    "printf 'marker=%s\\n' \"$(test -e /etc/celesto/features/instance-id && echo yes)\"; "
    "printf 'cmdline=%s\\n' \"$(cat /proc/cmdline)\""
)


def _require_backend(backend: str, request: pytest.FixtureRequest) -> None:
    require_e2e_backend(backend, request.config, sandbox_name=f"identity-{backend}")  # type: ignore[arg-type]


def _celesto(*args: str) -> dict[str, Any]:
    """Run one CLI command with ``--json`` and return its ``data`` payload."""
    # Flags must come before ``--``; everything after it is the guest command.
    split = args.index("--") if "--" in args else len(args)
    proc = subprocess.run(
        [sys.executable, "-c", _CLI_MAIN, *args[:split], "--json", *args[split:]],
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"celesto {' '.join(args)} printed no JSON: {proc.stdout}\n{proc.stderr}")
    assert envelope["ok"], f"celesto {' '.join(args)} failed: {envelope['error']}"
    return envelope["data"] or {}


def _guest_identity(name: str) -> dict[str, str]:
    data = _celesto("sandbox", "exec", name, "--", "sh", "-c", _GUEST_IDENTITY_SCRIPT)
    stdout = data.get("stdout", "")
    values: dict[str, str] = {}
    for line in stdout.splitlines():
        key, sep, value = line.partition("=")
        if sep:
            values[key] = value.strip()
    return values


def _recorded_identity(state: SQLiteStateManager, name: str) -> dict[str, str | None] | None:
    record = state.get_vm_identity(name)
    if record is None:
        return None
    return {
        "instance_id": record.instance_id,
        "ssh_host_key_fingerprint": record.ssh_host_key_fingerprint,
        "machine_id": record.machine_id,
    }


def _snapshot(name: str, state: SQLiteStateManager) -> dict[str, Any]:
    guest = _guest_identity(name)
    return {
        "config_instance_id": state.get_vm(name).config.instance_id,
        "guest": {key: value for key, value in guest.items() if key != "cmdline"},
        "boot_line_instance_id": next(
            (
                part.split("=", 1)[1]
                for part in guest.get("cmdline", "").split()
                if part.startswith("celesto.instance_id=")
            ),
            None,
        ),
        "recorded": _recorded_identity(state, name),
    }


def _assert_consistent(name: str, snap: dict[str, Any]) -> None:
    guest = snap["guest"]
    instance_id = snap["config_instance_id"]
    assert instance_id, f"{name} has no instance ID in its config"
    assert snap["boot_line_instance_id"] == instance_id, f"{name} boot line: {snap}"
    assert guest["instance_id"] == instance_id, f"{name} guest instance ID: {snap}"
    assert guest["marker"] == "yes", f"{name} image has no instance ID marker: {snap}"
    assert _HEX32.match(guest["machine_id"]), f"{name} machine ID: {snap}"
    if guest["dbus_machine_id"]:
        assert guest["dbus_machine_id"] == guest["machine_id"], f"{name} dbus copy: {snap}"
    assert guest["fingerprint"].startswith("SHA256:"), f"{name} fingerprint: {snap}"
    assert snap["recorded"] == {
        "instance_id": instance_id,
        "ssh_host_key_fingerprint": guest["fingerprint"],
        "machine_id": guest["machine_id"],
    }, f"{name} recorded identity: {snap}"


def _identity_triplet(snap: dict[str, Any]) -> tuple[str, str, str]:
    guest = snap["guest"]
    return (guest["instance_id"], guest["fingerprint"], guest["machine_id"])


@pytest.mark.parametrize("backend", E2E_BACKENDS, ids=str)
def test_each_sandbox_keeps_its_own_identity(
    backend: str, request: pytest.FixtureRequest, tmp_path: Path
) -> None:
    """Two sandboxes differ; restart and snapshot restore keep each identity."""
    _require_backend(backend, request)

    prefix = os.environ.get("CELESTO_E2E_NAME_PREFIX", "e2e-")
    suffix = uuid.uuid4().hex[:6]
    first = f"{prefix}identity-a-{suffix}"
    second = f"{prefix}identity-b-{suffix}"
    state = SQLiteStateManager(resolve_data_dir() / "celesto.db")
    report: dict[str, Any] = {"backend": backend, "sandboxes": {first: {}, second: {}}}
    artifact_dir = e2e_artifact_dir(tmp_path)
    artifact = artifact_dir / f"sandbox-identity-{backend}.json"
    created: list[str] = []
    snapshot_id: str | None = None
    try:
        for name in (first, second):
            _celesto(
                "sandbox",
                "create",
                "--name",
                name,
                "--os",
                "alpine",
                "--backend",
                backend,
                "--boot-timeout",
                str(BOOT_TIMEOUT),
            )
            created.append(name)
            snap = _snapshot(name, state)
            report["sandboxes"][name]["created"] = snap
            _assert_consistent(name, snap)

        a_created = report["sandboxes"][first]["created"]
        b_created = report["sandboxes"][second]["created"]
        for index, label in enumerate(("instance ID", "host key fingerprint", "machine ID")):
            assert _identity_triplet(a_created)[index] != _identity_triplet(b_created)[index], (
                f"both sandboxes share a {label}"
            )

        _celesto("sandbox", "stop", first)
        _celesto("sandbox", "start", first, "--boot-timeout", str(BOOT_TIMEOUT))
        restarted = _snapshot(first, state)
        report["sandboxes"][first]["after_restart"] = restarted
        _assert_consistent(first, restarted)
        assert _identity_triplet(restarted) == _identity_triplet(a_created)

        snapshot = _celesto("sandbox", "snapshot", "create", first, "--snapshot-type", "disk")
        snapshot_id = snapshot["snapshot"]["snapshot_id"]
        # Stop first, like test_lifecycle's restore test: restoring over a
        # still-running Firecracker sandbox races its tap device.
        _celesto("sandbox", "stop", first)
        _celesto("sandbox", "snapshot", "restore", snapshot_id, "--resume")
        restored = _snapshot(first, state)
        report["sandboxes"][first]["after_restore"] = restored
        _assert_consistent(first, restored)
        assert _identity_triplet(restored) == _identity_triplet(a_created)
        report["result"] = "passed"
    except BaseException as exc:
        report["result"] = f"failed: {exc}"
        raise
    finally:
        artifact.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(f"sandbox identity artifact: {artifact}")
        for name in created:
            with suppress(Exception):
                _celesto("sandbox", "delete", name)
        if snapshot_id is not None:
            with suppress(Exception):
                _celesto("sandbox", "snapshot", "delete", snapshot_id)

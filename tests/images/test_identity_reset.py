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

"""The startup script's identity reset, run with ``sh`` against a temp root.

The end-to-end test (``tests/e2e/test_sandbox_identity.py``) boots real
sandboxes, but it can only show the reset on a fresh disk and a plain restart.
It cannot boot a disk that already has keys under a *new* instance ID (that is
fork, which comes later), boot without an instance ID, or try every guest
layout. This test runs the exact shell block from both startup scripts
(``_base_init_script`` and ``scripts/ci/preset-init.sh``) to cover those.

Ways the reset could fail, written before the shell code:

1. A new instance ID keeps the old SSH host keys, so a copied disk shares
   them with its source.
2. The same instance ID (a restart or a restore) regenerates the keys or the
   machine ID, which breaks users' known_hosts and the recorded identity.
3. The new machine ID is not 32 lowercase hex characters, or is unchanged.
4. ``/var/lib/dbus/machine-id`` ends up different from ``/etc/machine-id``,
   or a dbus symlink is replaced, or a dbus copy is invented where the image
   has no dbus.
5. A boot line without an instance ID changes keys, the machine ID, or saves
   an instance ID: older sandboxes must behave exactly as before.
6. The capability marker is missing, so Celesto treats the image as old.
7. A malformed instance ID (shell metacharacters, paths) is acted on.
8. Key generation fails and the instance ID is saved anyway, so the next
   boot never retries and the guest claims a reset that did not happen.
9. The two startup scripts drift apart, or the reset runs after the guest
   agent or sshd start (and so could expose the old keys).
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from celesto.images.builder import ImageBuilder

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PRESET_INIT = _REPO_ROOT / "scripts" / "ci" / "preset-init.sh"
_BLOCK_START = "# >>> Celesto identity reset"
_BLOCK_END = "# <<< Celesto identity reset"
_HEX32 = re.compile(r"^[0-9a-f]{32}$")
_ID_A = "0123456789abcdef0123456789abcdef"
_ID_B = "fedcba9876543210fedcba9876543210"

pytestmark = pytest.mark.skipif(
    shutil.which("ssh-keygen") is None, reason="ssh-keygen is needed to create host keys"
)


def _scripts() -> dict[str, str]:
    return {
        "base-init": ImageBuilder()._default_init_script(),
        "preset-init": _PRESET_INIT.read_text(),
    }


def _block(script: str) -> str:
    start = script.index(_BLOCK_START)
    end = script.index(_BLOCK_END, start) + len(_BLOCK_END)
    return script[start:end]


@pytest.fixture(params=["base-init", "preset-init"])
def reset_block(request: pytest.FixtureRequest) -> str:
    return _block(_scripts()[request.param])


class _Guest:
    """A fake guest root plus a fake ``/proc/cmdline``."""

    def __init__(self, root: Path, block: str) -> None:
        self.root = root
        self.block = block
        (root / "etc" / "ssh").mkdir(parents=True)
        self.cmdline = root / "cmdline"

    def boot(self, cmdline: str, *, path: str | None = None) -> subprocess.CompletedProcess[str]:
        self.cmdline.write_text(cmdline + "\n")
        env = {"PATH": path} if path is not None else None
        return subprocess.run(
            [
                "/bin/sh",
                "-c",
                f'{self.block}\ncelesto_reset_identity "$1" "$2"',
                "sh",
                str(self.cmdline),
                str(self.root),
            ],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )

    def read(self, relative: str) -> str | None:
        path = self.root / relative
        return path.read_text() if path.exists() else None

    def host_key(self) -> str | None:
        return self.read("etc/ssh/ssh_host_ed25519_key.pub")

    def plant_old_identity(self) -> None:
        subprocess.run(
            [
                "ssh-keygen",
                "-q",
                "-t",
                "ed25519",
                "-N",
                "",
                "-f",
                str(self.root / "etc" / "ssh" / "ssh_host_ed25519_key"),
            ],
            check=True,
        )
        (self.root / "etc" / "machine-id").write_text("11111111111111111111111111111111\n")


@pytest.fixture
def guest(tmp_path: Path, reset_block: str) -> _Guest:
    return _Guest(tmp_path / "root", reset_block)


def _boot_line(instance_id: str | None) -> str:
    base = "console=ttyS0 reboot=k panic=1 init=/init root=/dev/vda rw"
    return f"{base} celesto.instance_id={instance_id}" if instance_id else base


def test_new_instance_id_replaces_keys_and_machine_id(guest: _Guest) -> None:
    guest.plant_old_identity()
    old_key = guest.host_key()

    result = guest.boot(_boot_line(_ID_A))

    assert result.returncode == 0, result.stderr
    assert guest.host_key() is not None
    assert guest.host_key() != old_key
    machine_id = (guest.read("etc/machine-id") or "").strip()
    assert _HEX32.match(machine_id), machine_id
    assert machine_id != "11111111111111111111111111111111"
    assert (guest.read("etc/celesto/instance-id") or "").strip() == _ID_A


def test_same_instance_id_keeps_keys_and_machine_id(guest: _Guest) -> None:
    assert guest.boot(_boot_line(_ID_A)).returncode == 0
    key = guest.host_key()
    machine_id = guest.read("etc/machine-id")
    private_key = guest.read("etc/ssh/ssh_host_ed25519_key")

    assert guest.boot(_boot_line(_ID_A)).returncode == 0

    assert guest.host_key() == key
    assert guest.read("etc/ssh/ssh_host_ed25519_key") == private_key
    assert guest.read("etc/machine-id") == machine_id


def test_each_new_instance_id_gets_a_different_machine_id(guest: _Guest) -> None:
    assert guest.boot(_boot_line(_ID_A)).returncode == 0
    first = (guest.read("etc/machine-id"), guest.host_key())

    assert guest.boot(_boot_line(_ID_B)).returncode == 0
    second = (guest.read("etc/machine-id"), guest.host_key())

    assert first[0] != second[0]
    assert first[1] != second[1]
    assert (guest.read("etc/celesto/instance-id") or "").strip() == _ID_B


def test_dbus_machine_id_copy_matches(guest: _Guest) -> None:
    dbus = guest.root / "var" / "lib" / "dbus"
    dbus.mkdir(parents=True)
    (dbus / "machine-id").write_text("22222222222222222222222222222222\n")

    assert guest.boot(_boot_line(_ID_A)).returncode == 0

    assert guest.read("var/lib/dbus/machine-id") == guest.read("etc/machine-id")


def test_dbus_machine_id_symlink_is_kept(guest: _Guest) -> None:
    dbus = guest.root / "var" / "lib" / "dbus"
    dbus.mkdir(parents=True)
    (dbus / "machine-id").symlink_to("../../../etc/machine-id")

    assert guest.boot(_boot_line(_ID_A)).returncode == 0

    assert (dbus / "machine-id").is_symlink()
    assert guest.read("var/lib/dbus/machine-id") == guest.read("etc/machine-id")


def test_no_dbus_copy_is_invented(guest: _Guest) -> None:
    assert guest.boot(_boot_line(_ID_A)).returncode == 0

    assert not (guest.root / "var" / "lib" / "dbus").exists()


def test_boot_line_without_instance_id_changes_nothing(guest: _Guest) -> None:
    guest.plant_old_identity()
    key = guest.host_key()

    result = guest.boot(_boot_line(None))

    assert result.returncode == 0, result.stderr
    assert guest.host_key() == key
    assert guest.read("etc/machine-id") == "11111111111111111111111111111111\n"
    assert guest.read("etc/celesto/instance-id") is None


@pytest.mark.parametrize("instance_id", [None, _ID_A])
def test_marker_says_the_image_supports_instance_ids(
    guest: _Guest, instance_id: str | None
) -> None:
    assert guest.boot(_boot_line(instance_id)).returncode == 0

    assert (guest.root / "etc" / "celesto" / "features" / "instance-id").is_file()


@pytest.mark.parametrize(
    "bad_id",
    ["$(touch${IFS}pwned)", "../../etc/passwd", "0123456789ABCDEF0123456789ABCDEF", "abc;def"],
)
def test_malformed_instance_id_is_ignored(guest: _Guest, bad_id: str) -> None:
    guest.plant_old_identity()
    key = guest.host_key()

    assert guest.boot(_boot_line(bad_id)).returncode == 0

    assert guest.host_key() == key
    assert guest.read("etc/celesto/instance-id") is None
    assert not (guest.root / "pwned").exists()
    assert not Path("pwned").exists()


def test_failed_key_generation_does_not_save_instance_id(guest: _Guest, tmp_path: Path) -> None:
    # A PATH with the basic tools but no ssh-keygen.
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for tool in ("tr", "grep", "head", "cut", "cat", "rm", "mkdir", "od", "mv", "chmod"):
        found = shutil.which(tool)
        assert found is not None, tool
        (bin_dir / tool).symlink_to(found)

    guest.boot(_boot_line(_ID_A), path=str(bin_dir))

    assert guest.read("etc/celesto/instance-id") is None


def test_both_startup_scripts_share_one_reset_that_runs_before_services() -> None:
    scripts = _scripts()
    blocks = {name: _block(script) for name, script in scripts.items()}
    assert blocks["base-init"] == blocks["preset-init"]
    for name, script in scripts.items():
        call = script.index('celesto_reset_identity /proc/cmdline ""')
        assert call < script.index("celesto-guest-agent --listen"), name
        assert call < script.index("/usr/sbin/sshd"), name

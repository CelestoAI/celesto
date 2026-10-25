"""Privilege regressions; run as root in a disposable Linux container only.

CELESTO_PRIVILEGED_TESTS=1 python -m unittest discover -s tests/host \
    -p test_setup_scripts_security.py -v

Uses real distinct uids and filesystem permissions. Never enable on a real host.
"""

from __future__ import annotations

import io
import json
import os
import pwd
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar

_ROOT = Path(__file__).resolve().parents[2]
_ENABLED = (
    os.environ.get("CELESTO_PRIVILEGED_TESTS") == "1"
    and sys.platform == "linux"
    and os.geteuid() == 0
)


@unittest.skipUnless(_ENABLED, "requires an explicitly enabled disposable root Linux container")
class SetupPrivilegeTests(unittest.TestCase):
    account: ClassVar[pwd.struct_passwd]

    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(["useradd", "--create-home", "celesto-security-test"], check=True)
        cls.account = pwd.getpwnam("celesto-security-test")

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.root.chmod(0o755)
        self.tools = self.root / "tools"
        self.tools.mkdir()
        self.runtime_home = Path(self.account.pw_dir)
        self.destination = self.runtime_home / ".celesto" / "bin"
        directory = self.destination.parent
        if directory.is_symlink():
            directory.unlink()
        elif directory.exists():
            shutil.rmtree(directory)
        self.env = {**os.environ, "PATH": f"{self.tools}:/usr/sbin:/usr/bin:/sbin:/bin"}
        self.env.pop("SUDO_USER", None)
        self.env.pop("SUDO_UID", None)

    def executable(self, name: str, script: str) -> Path:
        path = self.tools / name
        path.write_text("#!/bin/bash\nset -eu\n" + script)
        path.chmod(0o755)
        return path

    def installer(self) -> subprocess.CompletedProcess[str]:
        archive = self.root / "release.tgz"
        architecture = subprocess.check_output(["uname", "-m"], text=True).strip()
        with tarfile.open(archive, "w:gz") as tar:
            member = tarfile.TarInfo(
                f"release-v1.14.1-{architecture}/firecracker-v1.14.1-{architecture}"
            )
            binary = b"#!/bin/sh\necho 'Firecracker v1.14.1'\n"
            member.mode = 0o755
            member.size = len(binary)
            tar.addfile(member, io.BytesIO(binary))
        self.executable("wget", 'cp "$RELEASE_TARBALL" "$3"\n')
        return subprocess.run(
            [
                "bash",
                str(_ROOT / "scripts/internal/install-firecracker.sh"),
                "--skip-deps",
                "--runtime-user",
                self.account.pw_name,
                "--firecracker-dir",
                str(self.destination),
            ],
            env={**self.env, "RELEASE_TARBALL": str(archive)},
            capture_output=True,
            text=True,
            check=False,
        )

    def receipt(self, **values: object) -> None:
        print(json.dumps({"test": self.id(), **values}, sort_keys=True))

    def test_runtime_home_link_cannot_change_root_directory_ownership(self) -> None:
        protected = self.root / "protected"
        protected.mkdir()
        victim = protected / "keep"
        victim.write_text("unchanged")
        self.destination.parent.symlink_to(protected, target_is_directory=True)

        result = self.installer()

        self.receipt(exit_code=result.returncode, owner=protected.stat().st_uid)
        self.assertEqual(protected.stat().st_uid, 0)
        self.assertEqual(victim.read_text(), "unchanged")
        self.assertFalse((protected / "bin").exists())
        self.assertNotEqual(result.returncode, 0)

    def test_version_check_never_executes_replaced_published_program(self) -> None:
        marker = self.runtime_home / "executed-as"
        marker.unlink(missing_ok=True)
        self.env["EXECUTION_MARKER"] = str(marker)
        self.executable(
            "mv",
            '/bin/mv "$@"\n'
            'for destination in "$@"; do :; done\n'
            'if [[ "$destination" == */firecracker ]]; then\n'
            '  printf \'#!/bin/sh\\nid -u > "%s"\\n\' "$EXECUTION_MARKER" > "$destination"\n'
            '  chmod 755 "$destination"\n'
            "fi\n",
        )

        result = self.installer()

        self.receipt(exit_code=result.returncode, replacement_executed=marker.exists())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(marker.exists(), "installer executed a runtime-replaceable program")
        self.assertEqual((self.destination / "firecracker").stat().st_uid, self.account.pw_uid)

    def test_regular_runtime_install_publishes_owned_executable(self) -> None:
        result = self.installer()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        binary = self.destination / "firecracker"
        output = subprocess.check_output(
            ["runuser", "-u", self.account.pw_name, "--", str(binary), "--version"], text=True
        )
        self.receipt(owner=binary.stat().st_uid, version=output.strip())
        self.assertEqual(binary.stat().st_uid, self.account.pw_uid)
        self.assertEqual(output.strip(), "Firecracker v1.14.1")

    def test_loopfs_refuses_delegated_runtime_operations(self) -> None:
        # These files satisfy the old ownership checks. Only the authority guard
        # prevents extraction/mounting, not absent files or a different error.
        runtime_dir = self.runtime_home / "loopfs"
        runtime_dir.mkdir(exist_ok=True)
        os.chown(runtime_dir, self.account.pw_uid, self.account.pw_gid)
        mount_dir = runtime_dir / "mnt"
        mount_dir.mkdir(exist_ok=True)
        os.chown(mount_dir, self.account.pw_uid, self.account.pw_gid)
        image = runtime_dir / "rootfs.ext4"
        image.touch()
        os.chown(image, self.account.pw_uid, self.account.pw_gid)
        archive = runtime_dir / "rootfs.tar"
        with tarfile.open(archive, "w") as tar:
            member = tarfile.TarInfo("payload")
            member.uid = 0
            member.mode = 0o4755
            member.size = 4
            tar.addfile(member, io.BytesIO(b"evil"))
        os.chown(archive, self.account.pw_uid, self.account.pw_gid)
        marker = self.root / "privileged-call"
        self.env["CALL_MARKER"] = str(marker)
        self.executable("mount", 'echo mount >> "$CALL_MARKER"\n')
        self.executable("umount", 'echo umount >> "$CALL_MARKER"\n')
        self.executable("tar", 'echo tar >> "$CALL_MARKER"\n')
        for args in (
            ["mount", str(image), str(mount_dir)],
            ["extract", str(archive), str(mount_dir)],
            ["umount", str(mount_dir)],
        ):
            with self.subTest(action=args[0]):
                result = subprocess.run(
                    ["bash", str(_ROOT / "scripts/internal/image-build-loopfs.sh"), *args],
                    env={
                        **self.env,
                        "SUDO_USER": self.account.pw_name,
                        "SUDO_UID": str(self.account.pw_uid),
                    },
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.receipt(action=args[0], exit_code=result.returncode)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(marker.exists())
        self.assertFalse((mount_dir / "payload").exists())

    def test_root_mount_disables_guest_privileges(self) -> None:
        image = self.root / "rootfs.ext4"
        image.touch()
        destination = self.root / "mnt"
        destination.mkdir()
        log = self.root / "mount-arguments"
        self.env["MOUNT_LOG"] = str(log)
        self.executable("mount", 'printf "%s\\n" "$@" > "$MOUNT_LOG"\n')
        result = subprocess.run(
            [
                "bash",
                str(_ROOT / "scripts/internal/image-build-loopfs.sh"),
                "mount",
                str(image),
                str(destination),
            ],
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        args = log.read_text().splitlines()
        options = args[args.index("-o") + 1].split(",")
        self.receipt(mount_options=options)
        self.assertTrue({"loop", "nosuid", "nodev", "noexec"}.issubset(options))

    def test_root_extract_refuses_an_ordinary_directory(self) -> None:
        archive = self.root / "rootfs.tar"
        with tarfile.open(archive, "w") as tar:
            member = tarfile.TarInfo("payload")
            member.mode = 0o4755
            member.uid = 0
            member.size = 4
            tar.addfile(member, io.BytesIO(b"evil"))
        destination = self.root / "mnt"
        destination.mkdir()
        result = subprocess.run(
            [
                "bash",
                str(_ROOT / "scripts/internal/image-build-loopfs.sh"),
                "extract",
                str(archive),
                str(destination),
            ],
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.receipt(exit_code=result.returncode, extracted=(destination / "payload").exists())
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((destination / "payload").exists())

    def test_generated_runtime_policy_grants_no_arbitrary_root_tools(self) -> None:
        # Setup writes only inside this disposable container. Dummy network
        # commands satisfy discovery; any live operation is an unexpected error.
        for command in ("ip", "nft", "sysctl"):
            self.executable(command, "exit 91\n")
        self.executable("visudo", "exit 0\n")
        Path("/etc/sudoers.d").mkdir(exist_ok=True)
        policy_path = Path("/etc/sudoers.d") / f"celesto-runtime-{self.account.pw_name}"
        policy_path.write_text(f"{self.account.pw_name} ALL=(root) NOPASSWD: /usr/sbin/ip *\n")
        result = subprocess.run(
            [
                "bash",
                str(_ROOT / "scripts/internal/configure-runtime-sudoers.sh"),
                "--runtime-user",
                self.account.pw_name,
                "--skip-runtime-check",
            ],
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        active_lines = [
            line
            for line in policy_path.read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.receipt(policy=active_lines)
        self.assertEqual(active_lines, [])


if __name__ == "__main__":
    unittest.main()

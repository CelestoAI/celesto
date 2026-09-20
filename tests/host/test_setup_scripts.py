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

"""Portable regression tests for the packaged Linux setup scripts."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_INSTALL_SCRIPT = _REPO_ROOT / "scripts" / "internal" / "install-firecracker.sh"
_SYSTEM_SETUP_SCRIPT = _REPO_ROOT / "scripts" / "system-setup.sh"
_ONE_LINE_INSTALLER = _REPO_ROOT / "scripts" / "install.sh"
_RUNTIME_CONFIG_SCRIPT = _REPO_ROOT / "scripts" / "internal" / "configure-runtime-sudoers.sh"


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(0o755)


def _fake_download_tools(tmp_path: Path) -> Path:
    tools = tmp_path / "tools"
    tools.mkdir()
    _write_executable(
        tools / "uname",
        '#!/bin/bash\n[[ "$1" == "-m" ]] && echo x86_64 || /usr/bin/uname "$@"\n',
    )
    _write_executable(
        tools / "wget",
        """#!/bin/bash
set -eu
while [[ $# -gt 0 ]]; do
    if [[ "$1" == "-O" ]]; then
        : > "$2"
        exit 0
    fi
    shift
done
exit 1
""",
    )
    _write_executable(
        tools / "tar",
        """#!/bin/bash
set -eu
if [[ "${FAIL_FAKE_TAR:-}" == "1" ]]; then
    exit 2
fi
destination=""
while [[ $# -gt 0 ]]; do
    if [[ "$1" == "-C" ]]; then
        destination="$2"
        shift 2
        continue
    fi
    shift
done
release="$destination/release-v1.14.1-x86_64"
mkdir -p "$release"
cat > "$release/firecracker-v1.14.1-x86_64" <<'EOF'
#!/bin/sh
echo 'Firecracker v1.14.1'
EOF
chmod 755 "$release/firecracker-v1.14.1-x86_64"
""",
    )
    return tools


def _run_installer(
    destination: Path,
    tools: Path,
    *,
    fail_tar: bool = False,
    runtime_user: str | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PATH"] = f"{tools}{os.pathsep}{env['PATH']}"
    if fail_tar:
        env["FAIL_FAKE_TAR"] = "1"
    args = [
        "bash",
        str(_INSTALL_SCRIPT),
        "--skip-deps",
        "--firecracker-dir",
        str(destination),
    ]
    if runtime_user is not None:
        args.extend(["--runtime-user", runtime_user])
    return subprocess.run(
        args,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_installer_supports_custom_directory_with_spaces(tmp_path: Path) -> None:
    tools = _fake_download_tools(tmp_path)
    destination = tmp_path / "custom runtime" / "bin"

    result = _run_installer(destination, tools)

    assert result.returncode == 0, result.stderr or result.stdout
    binary = destination / "firecracker"
    assert binary.is_file()
    assert os.access(binary, os.X_OK)
    version_output = subprocess.check_output([binary], text=True)
    assert "Firecracker v1.14.1" in version_output


def test_explicit_directory_does_not_require_runtime_user_home(tmp_path: Path) -> None:
    if subprocess.run(["id", "nobody"], check=False, capture_output=True).returncode != 0:
        pytest.skip("test requires the standard nobody account")

    tools = _fake_download_tools(tmp_path)
    _write_executable(tools / "getent", "#!/bin/sh\nexit 1\n")
    destination = tmp_path / "explicit" / "bin"

    result = _run_installer(destination, tools, runtime_user="nobody")

    assert result.returncode == 0, result.stderr or result.stdout
    assert (destination / "firecracker").is_file()


def test_failed_reinstall_preserves_existing_binary(tmp_path: Path) -> None:
    tools = _fake_download_tools(tmp_path)
    destination = tmp_path / "bin"
    destination.mkdir()
    binary = destination / "firecracker"
    binary.write_text("#!/bin/sh\necho existing\n")
    binary.chmod(0o755)

    result = _run_installer(destination, tools, fail_tar=True)

    assert result.returncode != 0
    assert binary.read_text() == "#!/bin/sh\necho existing\n"


@pytest.mark.parametrize(
    "script",
    [_INSTALL_SCRIPT, _SYSTEM_SETUP_SCRIPT, _ONE_LINE_INSTALLER, _RUNTIME_CONFIG_SCRIPT],
)
def test_changed_setup_scripts_have_valid_bash_syntax(script: Path) -> None:
    subprocess.run(["bash", "-n", str(script)], check=True)


def test_firecracker_installer_has_no_system_destination_or_jailer_state() -> None:
    text = _INSTALL_SCRIPT.read_text() + _SYSTEM_SETUP_SCRIPT.read_text()

    assert "/usr/local/bin/firecracker" not in text
    assert "/usr/local/bin/jailer" not in text
    assert "/srv/jailer" not in text
    assert "groupadd -g 2000 firecracker" not in text


def test_system_setup_handles_fedora_without_assuming_apt() -> None:
    text = _SYSTEM_SETUP_SCRIPT.read_text()

    assert "/run/ostree-booted" in text
    assert "rpm-ostree install" in text
    assert "dnf install" in text
    assert "Host dependencies already installed" in text


def test_one_line_installer_keeps_custom_directory_for_doctor() -> None:
    text = _ONE_LINE_INSTALLER.read_text()

    assert "FIRECRACKER_DIR_ARG" in text
    assert 'export SMOLVM_FIRECRACKER_DIR="${FIRECRACKER_DIR_ARG}"' in text
    assert "if ((${#SETUP_ARGS[@]})); then" in text
    assert 'celesto setup "${SETUP_ARGS[@]}"' in text


def test_runtime_sudo_policy_excludes_user_writable_programs() -> None:
    text = _RUNTIME_CONFIG_SCRIPT.read_text()

    assert 'LOOPFS_HELPER_DIR="/var/lib/smolvm/libexec"' in text
    assert '[[ -L "${LOOPFS_HELPER_DST}"' in text
    assert "SMOLVM_VM_CMDS" not in text
    assert "FIRECRACKER_BIN" not in text
    assert "kill -9" not in text
    assert "SMOLVM_FIRECRACKER_DIR" not in text


def test_setup_recovery_shell_quotes_custom_firecracker_directory() -> None:
    text = _SYSTEM_SETUP_SCRIPT.read_text()

    assert "printf -v firecracker_dir_arg '%q'" in text


@pytest.mark.parametrize("upgrade", [False, True])
@pytest.mark.parametrize(
    "args",
    [
        [],
        ["--skip-deps"],
        ["--with-docker"],
        ["--firecracker-dir", "/tmp/custom runtime"],
        ["--firecracker-dir=/tmp/custom runtime"],
    ],
)
def test_one_line_installer_dry_run(tmp_path: Path, upgrade: bool, args: list[str]) -> None:
    _dry_run_one_line(tmp_path, upgrade=upgrade, args=args)


@pytest.mark.parametrize("failure", ["install", "setup", "doctor", "download"])
def test_one_line_installer_stops_on_failure(tmp_path: Path, failure: str) -> None:
    _dry_run_one_line(tmp_path, failure=failure, uv_available=failure != "download")


def test_one_line_installer_bootstraps_uv(tmp_path: Path) -> None:
    _dry_run_one_line(tmp_path, uv_available=False)


def test_one_line_installer_activates_pending_kvm_membership(tmp_path: Path) -> None:
    _dry_run_one_line(tmp_path, pending_kvm=True)


def _dry_run_one_line(
    tmp_path: Path,
    *,
    upgrade: bool = False,
    args: list[str] | None = None,
    failure: str = "",
    uv_available: bool = True,
    pending_kvm: bool = False,
) -> None:
    """Execute the real entry point with installation commands replaced by recorders."""
    args = args or []
    tools = tmp_path / "tools"
    tools.mkdir()
    tool_bin = tmp_path / "custom tools"
    tool_bin.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    log = tmp_path / "commands"
    _write_executable(
        tools / "uv",
        """#!/bin/bash
printf 'uv' >> "$COMMAND_LOG"
printf ' <%s>' "$@" >> "$COMMAND_LOG"
printf '\\n' >> "$COMMAND_LOG"
case "$*" in
    --version) echo 'uv test' ;;
    'tool list') [[ "$UPGRADE" == 1 ]] && echo 'celesto v0.0.15a0'; exit 0 ;;
    'tool dir --bin') echo "$TOOL_BIN" ;;
    'tool install'*) [[ "$FAILURE" != install ]] ;;
esac
""",
    )
    _write_executable(
        tool_bin / "celesto",
        """#!/bin/bash
printf 'celesto' >> "$COMMAND_LOG"
printf ' <%s>' "$@" >> "$COMMAND_LOG"
printf ' dir=%s\\n' "${SMOLVM_FIRECRACKER_DIR:-}" >> "$COMMAND_LOG"
[[ "$1" != "$FAILURE" ]]
""",
    )
    _write_executable(tools / "uname", "#!/bin/sh\necho Linux\n")
    _write_executable(
        tools / "id",
        """#!/bin/bash
case "$*" in
    -un) echo test-user ;;
    -Gn) echo test-user ;;
    '-Gn test-user')
        if [[ "$PENDING_KVM" == 1 ]]; then
            echo 'test-user kvm'
        else
            echo test-user
        fi
        ;;
    *) exit 1 ;;
esac
""",
    )
    _write_executable(
        tools / "sg",
        """#!/bin/bash
printf 'sg' >> "$COMMAND_LOG"
printf ' <%s>' "$@" >> "$COMMAND_LOG"
printf '\\n' >> "$COMMAND_LOG"
[[ "$1" == kvm && "$2" == -c ]]
/bin/bash -c "$3"
""",
    )
    if not uv_available:
        (tools / "uv").rename(tmp_path / "uv-template")
        _write_executable(
            tools / "curl",
            """#!/bin/bash
[[ "$FAILURE" != download ]] || exit 22
printf 'cp "$UV_TEMPLATE" "$UV_DESTINATION"\\n'
""",
        )
    env = {
        **os.environ,
        "HOME": str(home),
        "PATH": f"{tools}:/usr/bin:/bin",
        "COMMAND_LOG": str(log),
        "TOOL_BIN": str(tool_bin),
        "UPGRADE": str(int(upgrade)),
        "PENDING_KVM": str(int(pending_kvm)),
        "FAILURE": failure,
        "UV_TEMPLATE": str(tmp_path / "uv-template"),
        "UV_DESTINATION": str(tools / "uv"),
    }
    env.pop("SMOLVM_FIRECRACKER_DIR", None)
    result = subprocess.run(
        ["/bin/bash", str(_ONE_LINE_INSTALLER), *args],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if failure:
        assert result.returncode != 0
        assert "Done!" not in result.stdout
        failure_commands = log.read_text() if log.exists() else ""
        if failure in ("install", "download"):
            assert "celesto <setup>" not in failure_commands
        if failure != "doctor":
            assert "celesto <doctor>" not in failure_commands
        return
    assert result.returncode == 0, result.stdout + result.stderr
    commands = log.read_text().splitlines()
    install = "uv <tool> <install>" + (" <--upgrade>" if upgrade else "")
    assert install + " <celesto[server]>=0.0.15a0>" in commands
    directory = (
        "/tmp/custom runtime" if any(a.startswith("--firecracker-dir") for a in args) else ""
    )
    assert "celesto <setup>" + "".join(f" <{a}>" for a in args) + f" dir={directory}" in commands
    if pending_kvm:
        assert any(command.startswith("sg <kvm> <-c>") for command in commands)
    else:
        assert not any(command.startswith("sg ") for command in commands)
    assert commands[-1] == f"celesto <doctor> dir={directory}"


@pytest.mark.parametrize("args", [[], ["--skip-deps"], ["--check-only"], ["--with-docker"]])
def test_macos_dependency_dry_run(tmp_path: Path, args: list[str]) -> None:
    tools = tmp_path / "tools"
    tools.mkdir()
    log = tmp_path / "brew-log"
    _write_executable(tools / "uname", "#!/bin/sh\necho Darwin\n")
    _write_executable(tools / "ssh", "#!/bin/sh\nexit 0\n")
    _write_executable(
        tools / "brew",
        """#!/bin/bash
printf '%s\\n' "$*" >> "$BREW_LOG"
if [[ "$*" == 'install qemu' ]]; then
    printf '#!/bin/sh\\nexit 0\\n' > "$TOOLS/qemu-system-aarch64"
    /bin/chmod +x "$TOOLS/qemu-system-aarch64"
else
    printf '#!/bin/sh\\nexit 0\\n' > "$TOOLS/docker"
    /bin/chmod +x "$TOOLS/docker"
fi
""",
    )
    result = subprocess.run(
        ["/bin/bash", str(_REPO_ROOT / "scripts/system-setup-macos.sh"), *args],
        env={
            **os.environ,
            # Keep host-installed commands such as /usr/bin/docker out of the
            # simulated macOS environment. Every discoverable command is
            # provided explicitly in ``tools`` above.
            "PATH": str(tools),
            "TOOLS": str(tools),
            "BREW_LOG": str(log),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    if args in (["--skip-deps"], ["--check-only"]):
        assert result.returncode != 0
        assert not log.exists(), "Read-only/skip-deps setup must not install QEMU"
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        expected = ["install qemu"] + (["install --cask docker"] if args else [])
        assert log.read_text().splitlines() == expected

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

"""Alpine images must not be open to CVE-2026-123158 (sshd password bypass).

On musl without PAM, an affected sshd accepts a password of 257 to 1,024 bytes
for any account whose stored hash is exactly ``*``, when sent as the second
attempt on a connection. Each test builds a real Alpine recipe, turns on
password login so the sshd code itself is under test, and tries the bypass.

Run with ``pytest -m e2e tests/e2e/test_alpine_sshd_password_bypass.py``. Set
``CELESTO_E2E_ARTIFACT_DIR`` to choose where the JSON report is written.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock, patch
from uuid import uuid4

import paramiko
import pytest

from celesto.images.builder import ImageBuilder

pytestmark = pytest.mark.e2e

REPO_ROOT = Path(__file__).resolve().parents[2]
PATCHED_OPENSSH_SERVER = {"3.19": "9.6_p1-r3", "3.20": "9.7_p1-r6"}

PROBE_SETUP = r"""
set -e
ssh-keygen -A >/dev/null
mkdir -p /run/sshd
echo 'root:probe-root-password' | chpasswd
adduser -D target >/dev/null
sed -i 's/^target:[^:]*:/target:*:/' /etc/shadow
exec /usr/sbin/sshd -D -e -o PasswordAuthentication=yes
"""


def _run(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def _builder_dockerfile(method_name: str, tmp_path: Path) -> str:
    """Return the Dockerfile a builder recipe really sends to ``docker build``."""
    captured: dict[str, str] = {}

    def fake_do_build(_name: str, dockerfile: str, *args: object, **_kwargs: object) -> None:
        captured["dockerfile"] = dockerfile
        cast(Path, args[2]).touch()
        cast(Path, args[3]).touch()

    with (
        patch.object(ImageBuilder, "_host_arch_key", return_value="x86_64"),
        patch.object(ImageBuilder, "check_docker", return_value=True),
        patch.object(ImageBuilder, "_do_build", MagicMock(side_effect=fake_do_build)),
    ):
        builder = ImageBuilder(cache_dir=tmp_path / "images")
        if method_name == "build_alpine_ssh":
            builder.build_alpine_ssh()
        else:
            builder.build_alpine_ssh_key("ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMockKey user@test")
    return captured["dockerfile"]


@pytest.fixture(
    params=["build_alpine_ssh", "build_alpine_ssh_key", "Dockerfile.base-alpine-rootfs"]
)
def built_image(request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[tuple[str, str, str]]:
    if shutil.which("docker") is None:
        pytest.skip("docker is not installed")

    recipe = cast(str, request.param)
    tag = f"celesto-sshd-probe-{uuid4().hex[:12]}"
    if recipe.startswith("Dockerfile"):
        dockerfile_path = REPO_ROOT / "scripts" / "ci" / recipe
        dockerfile = dockerfile_path.read_text()
        context = dockerfile_path.parent
    else:
        dockerfile = _builder_dockerfile(recipe, tmp_path)
        context = tmp_path / "context"
        context.mkdir()
        (context / "init").write_text("#!/bin/sh\n")
        dockerfile_path = context / "Dockerfile"
        dockerfile_path.write_text(dockerfile)

    _run(
        "docker",
        "build",
        "-t",
        tag,
        "--build-arg",
        "SSH_PASSWORD=celesto",
        "-f",
        str(dockerfile_path),
        str(context),
    )
    try:
        yield recipe, dockerfile, tag
    finally:
        subprocess.run(["docker", "rmi", "-f", tag], capture_output=True, check=False)


def _try_bypass(port: int) -> list[str]:
    """Send a short password, then an oversized one, on the same connection."""
    outcomes = []
    with socket.create_connection(("127.0.0.1", port), timeout=10) as sock:
        transport = paramiko.Transport(sock)
        try:
            transport.start_client(timeout=10)
            for password in ("x" * 16, "A" * 300):
                try:
                    transport.auth_password("target", password, fallback=False)
                except paramiko.AuthenticationException:
                    outcomes.append("rejected")
                else:
                    outcomes.append("accepted")
                    break
        finally:
            transport.close()
    return outcomes


def _container_logs(container: str) -> str:
    return subprocess.run(
        ["docker", "logs", container], capture_output=True, text=True, check=False
    ).stderr


def _wait_for_sshd(container: str) -> int:
    for _ in range(50):
        if "Server listening" in _container_logs(container):
            return int(_run("docker", "port", container, "22/tcp").rsplit(":", 1)[1])
        time.sleep(0.2)
    raise AssertionError("sshd did not start")


def _write_report(recipe: str, report: dict[str, Any], tmp_path: Path) -> Path:
    directory = Path(os.environ.get("CELESTO_E2E_ARTIFACT_DIR", tmp_path))
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"sshd-password-bypass-{recipe}.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    return path


def test_alpine_recipe_rejects_sshd_password_bypass(
    built_image: tuple[str, str, str], tmp_path: Path
) -> None:
    recipe, dockerfile, tag = built_image

    alpine = _run("docker", "run", "--rm", tag, "cat", "/etc/alpine-release")
    branch = ".".join(alpine.split(".")[:2])
    floor = PATCHED_OPENSSH_SERVER[branch]
    installed = _run(
        "docker", "run", "--rm", tag, "sh", "-c", "apk info -e -v openssh-server"
    ).removeprefix("openssh-server-")
    comparison = _run("docker", "run", "--rm", tag, "apk", "version", "-t", installed, floor)

    container = f"{tag}-sshd"
    report: dict[str, Any] = {
        "cve": "CVE-2026-123158",
        "recipe": recipe,
        "alpine": alpine,
        "openssh_server": installed,
        "required_openssh_server": floor,
        "bypass_attempts": [],
    }
    try:
        _run(
            "docker",
            "run",
            "-d",
            "--name",
            container,
            "-p",
            "127.0.0.1::22",
            tag,
            "sh",
            "-c",
            PROBE_SETUP,
        )
        report["bypass_attempts"] = _try_bypass(_wait_for_sshd(container))
    except Exception as error:
        report["error"] = repr(error)
        report["sshd_logs"] = _container_logs(container)
        raise
    finally:
        print(f"report: {_write_report(recipe, report, tmp_path)}")
        subprocess.run(["docker", "rm", "-f", container], capture_output=True, check=False)

    assert report["bypass_attempts"] == ["rejected", "rejected"]
    assert comparison in {">", "="}, f"{installed} is older than {floor}"
    # A floor in the recipe stops an old cached layer or image from being reused.
    assert f"openssh-server>={floor}" in dockerfile

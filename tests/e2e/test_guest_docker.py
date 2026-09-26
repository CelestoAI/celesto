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

"""Prove a user-installed Docker runtime can run containers inside a guest.

Celesto does not preinstall a container runtime. Guests use a custom ``/init``
(not systemd), so this test installs ``docker.io``, starts ``dockerd`` by hand,
and runs ``hello-world`` to exercise the kernel cgroup/bridge options and the
cgroup v2 mount that make that install path work.
"""

from __future__ import annotations

from contextlib import suppress

import pytest
from _util import (
    BOOT_TIMEOUT,
    E2E_BACKENDS,
    E2EBackend,
    require_backend_available,
    selected_backend,
)

from celesto import Celesto
from celesto.types import VMState

pytestmark = pytest.mark.e2e

# apt + docker.io + hello-world pull need more than the default Ubuntu disk,
# and dockerd needs headroom beyond the default 1 GiB guest RAM.
_DOCKER_DISK_MIB = 4096
_DOCKER_MEMORY_MIB = 2048
_APT_TIMEOUT_S = 600
_DOCKERD_READY_TIMEOUT_S = 120
_HELLO_WORLD_TIMEOUT_S = 180


def _ensure_cgroup_v2(sandbox: Celesto) -> None:
    """Mount the unified hierarchy when guest init has not already done so."""
    result = sandbox.run(
        "mkdir -p /sys/fs/cgroup && "
        "if ! grep -q ' /sys/fs/cgroup cgroup2 ' /proc/mounts; then "
        "mount -t cgroup2 cgroup2 /sys/fs/cgroup; "
        "fi && "
        "grep -q ' /sys/fs/cgroup cgroup2 ' /proc/mounts",
        timeout=30,
    )
    assert result.exit_code == 0, (
        f"cgroup v2 is required for Docker resource controls: "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def _install_docker(sandbox: Celesto) -> None:
    result = sandbox.run(
        "export DEBIAN_FRONTEND=noninteractive && "
        "apt-get update -qq && "
        "apt-get install -y -qq docker.io iptables",
        timeout=_APT_TIMEOUT_S,
    )
    assert result.exit_code == 0, (
        f"docker.io install failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def _start_dockerd(sandbox: Celesto) -> None:
    # Guests run Celesto's custom /init as PID 1, so systemctl is unavailable.
    start = sandbox.run(
        "mkdir -p /var/run /var/lib/docker /var/log && "
        "if ! command -v dockerd >/dev/null 2>&1; then "
        "echo 'dockerd not found after install' >&2; exit 1; "
        "fi && "
        "if [ ! -S /var/run/docker.sock ]; then "
        "nohup dockerd >/var/log/dockerd.log 2>&1 & "
        "fi",
        timeout=30,
    )
    assert start.exit_code == 0, (
        f"failed to start dockerd: stdout={start.stdout!r} stderr={start.stderr!r}"
    )

    ready = sandbox.run(
        "for i in $(seq 1 60); do "
        "docker info >/dev/null 2>&1 && exit 0; "
        "sleep 2; "
        "done; "
        "echo 'dockerd did not become ready' >&2; "
        "tail -n 80 /var/log/dockerd.log >&2 || true; "
        "exit 1",
        timeout=_DOCKERD_READY_TIMEOUT_S,
    )
    assert ready.exit_code == 0, (
        f"dockerd never became ready: stdout={ready.stdout!r} stderr={ready.stderr!r}"
    )


@pytest.mark.parametrize("backend", E2E_BACKENDS, ids=str)
def test_user_installed_docker_runs_hello_world(
    backend: E2EBackend,
    request: pytest.FixtureRequest,
) -> None:
    """Install Docker in an Ubuntu guest and run a container successfully."""
    selected = selected_backend(request.config)
    if selected != "all" and backend != selected:
        pytest.skip(
            f"End-to-end tests for '{backend}' are skipped because this run selected "
            f"'{selected}'; rerun all backends with: pytest tests/e2e."
        )
    require_backend_available(backend, request.config, sandbox_name=f"guest-docker-{backend}")

    sandbox = Celesto(
        backend=backend,
        os="ubuntu",
        disk_size=_DOCKER_DISK_MIB,
        memory=_DOCKER_MEMORY_MIB,
        comm_channel="ssh",
    )
    try:
        sandbox.start(boot_timeout=BOOT_TIMEOUT)
        assert sandbox.status == VMState.RUNNING

        _ensure_cgroup_v2(sandbox)
        _install_docker(sandbox)
        _start_dockerd(sandbox)

        hello = sandbox.run(
            "docker run --rm hello-world",
            timeout=_HELLO_WORLD_TIMEOUT_S,
        )
        assert hello.exit_code == 0, (
            f"docker run failed: stdout={hello.stdout!r} stderr={hello.stderr!r}"
        )
        assert "Hello from Docker" in hello.stdout, hello.stdout
    finally:
        with suppress(Exception):
            sandbox.stop()
        with suppress(Exception):
            sandbox.delete()

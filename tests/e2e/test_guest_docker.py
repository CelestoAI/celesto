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
(not systemd), so this test installs ``docker.io``, waits for the guest agent to
start ``dockerd``, and runs ``hello-world`` to exercise the kernel cgroup/bridge options and the
cgroup v2 mount that make that install path work.
"""

from __future__ import annotations

from contextlib import suppress
from ipaddress import IPv4Address, ip_address
from pathlib import Path

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
# Loop sleeps up to 120s; leave headroom so the failure path can print the log.
_DOCKERD_READY_TIMEOUT_S = 180
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


def _install_docker(sandbox: Celesto, backend: E2EBackend) -> None:
    # GitHub-hosted runners use an internal resolver and block queries to the
    # public fallback resolvers baked into the guest image. Use the runner's
    # reachable resolver for this package-install test on TAP-backed guests.
    if backend == "firecracker":
        host_resolver_file = Path("/run/systemd/resolve/resolv.conf")
        if not host_resolver_file.is_file():
            host_resolver_file = Path("/etc/resolv.conf")
        resolvers = []
        for line in host_resolver_file.read_text().splitlines():
            fields = line.split()
            if len(fields) != 2 or fields[0] != "nameserver":
                continue
            try:
                address = ip_address(fields[1])
            except ValueError:
                continue
            if isinstance(address, IPv4Address) and not address.is_loopback:
                resolvers.append(str(address))
        assert resolvers, "Host has no IPv4 DNS server reachable from the guest"
        result = sandbox.run(
            "printf '%s\\n' "
            + " ".join(f"'nameserver {address}'" for address in resolvers[:2])
            + " > /etc/resolv.conf",
            timeout=30,
        )
        assert result.exit_code == 0, result.stderr

    # A failing lookup here distinguishes guest networking from apt/package
    # problems, and keeps the route and resolver details in the CI log.
    dns = sandbox.run("getent ahostsv4 archive.ubuntu.com", timeout=45)
    if dns.exit_code != 0:
        network = sandbox.run("ip route; cat /etc/resolv.conf", timeout=30)
        pytest.fail(
            "Guest DNS could not resolve archive.ubuntu.com: "
            f"lookup={dns.stdout!r} {dns.stderr!r}; "
            f"network={network.stdout!r} {network.stderr!r}"
        )
    result = sandbox.run(
        "export DEBIAN_FRONTEND=noninteractive && "
        "apt-get update -qq -o APT::Update::Error-Mode=any && "
        "apt-get install -y -qq docker.io iptables",
        timeout=_APT_TIMEOUT_S,
    )
    assert result.exit_code == 0, (
        f"docker.io install failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def _wait_for_dockerd(sandbox: Celesto) -> None:
    # The guest agent discovers and starts Docker after installation.
    ready = sandbox.run(
        "for i in $(seq 1 60); do "
        "docker info >/dev/null 2>&1 && exit 0; "
        "sleep 2; "
        "done; "
        "echo 'dockerd did not become ready' >&2; "
        "tail -n 80 /var/log/celesto-docker.log >&2 || true; "
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
        _install_docker(sandbox, backend)
        _wait_for_dockerd(sandbox)

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

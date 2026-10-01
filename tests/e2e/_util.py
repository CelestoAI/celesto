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

"""Shared helpers for the real-KVM end-to-end suite."""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from pathlib import Path
from shutil import which
from typing import Literal

import pytest

try:
    from celesto_core import network as _core_network
except (ImportError, OSError):  # pragma: no cover - native extension missing entirely
    _core_network = None

from celesto.host.manager import HostManager
from celesto.runtime.backends import BACKEND_FIRECRACKER, BACKEND_QEMU

# Every e2e test writes its artifact here when set (CI uploads this folder).
E2E_ARTIFACT_DIR_ENV = "CELESTO_E2E_ARTIFACT_DIR"

E2EBackend = Literal["qemu", "firecracker"]
E2ETransport = Literal["sandbox", "ssh", "vsock"]


@dataclass(frozen=True, slots=True)
class E2EVariant:
    """One backend/transport combination exercised by the real-KVM suite."""

    backend: E2EBackend
    transport: E2ETransport

    @property
    def id(self) -> str:
        return f"{self.backend}-{self.transport}"


E2E_BACKENDS: tuple[E2EBackend, ...] = (BACKEND_QEMU, BACKEND_FIRECRACKER)
E2E_VARIANTS: tuple[E2EVariant, ...] = (
    E2EVariant(BACKEND_QEMU, "ssh"),
    E2EVariant(BACKEND_QEMU, "vsock"),
    E2EVariant(BACKEND_FIRECRACKER, "ssh"),
    E2EVariant(BACKEND_FIRECRACKER, "vsock"),
)

# Boot is fast under KVM, but auto-config may build/download the rootfs and
# base kernel on the first run; give the whole start() a generous budget.
BOOT_TIMEOUT = 180.0


def kvm_ready() -> bool:
    """True when this host can actually run a hardware-accelerated VM."""
    return Path("/dev/kvm").exists() and _core_network is not None and _core_network.available()


def _kvm_accessible() -> bool:
    return Path("/dev/kvm").exists() and os.access("/dev/kvm", os.R_OK | os.W_OK)


def _qemu_binary_available() -> bool:
    arch = platform.machine().lower()
    candidates = (
        ("qemu-system-aarch64",)
        if arch in {"aarch64", "arm64"}
        else ("qemu-system-x86_64", "qemu-system-x86")
    )
    return any(which(candidate) is not None for candidate in candidates)


def backend_unavailable_reasons(backend: E2EBackend, *, sandbox_name: str) -> list[str]:
    """Return human-readable reasons the backend cannot run on this host."""
    reasons: list[str] = []
    if not kvm_ready():
        reasons.append(
            "Enable KVM and allow access: sudo modprobe kvm && sudo chmod 666 "
            f"/dev/kvm && re-run tests in sandbox '{sandbox_name}'"
        )

    if backend == BACKEND_QEMU and not _qemu_binary_available():
        reasons.append(
            "Install qemu-system for your host (e.g. sudo apt install qemu-system) "
            f"and re-run tests in sandbox '{sandbox_name}'"
        )

    if backend == BACKEND_FIRECRACKER:
        if platform.system() != "Linux":
            reasons.append(f"Run tests on a Linux host and re-run in sandbox '{sandbox_name}'")
        if Path("/dev/kvm").exists() and not _kvm_accessible():
            reasons.append(
                "Allow Firecracker to read and write /dev/kvm: sudo chmod 666 /dev/kvm "
                f"&& re-run tests in sandbox '{sandbox_name}'"
            )
        if HostManager().find_firecracker() is None:
            reasons.append(
                "Download Firecracker to ~/.celesto/bin, make it executable "
                "(chmod +x ~/.celesto/bin/firecracker), and re-run tests in "
                f"sandbox '{sandbox_name}'"
            )

    return reasons


def selected_backend(config: pytest.Config) -> str:
    return str(config.getoption("--e2e-backend"))


def require_backend_available(
    backend: E2EBackend,
    config: pytest.Config,
    *,
    sandbox_name: str | None = None,
) -> None:
    sandbox = sandbox_name or f"e2e-{backend}"
    reasons = backend_unavailable_reasons(backend, sandbox_name=sandbox)
    if not reasons:
        return

    message = (
        f"End-to-end tests for '{backend}' cannot run because {'; '.join(reasons)}; "
        f"fix that and rerun: pytest tests/e2e -k '{backend}'."
    )
    if selected_backend(config) == backend:
        pytest.fail(message)
    pytest.skip(message)


def require_e2e_backend(
    backend: E2EBackend,
    config: pytest.Config,
    *,
    sandbox_name: str,
) -> None:
    """Skip or fail unless this run can exercise *backend* on this host.

    A run that selected another backend skips. On macOS, QEMU runs with
    Hypervisor.framework, so it needs only the QEMU binary, not ``/dev/kvm``.
    Everywhere else :func:`require_backend_available` decides. When the run
    selected *backend* explicitly (as CI does), a missing requirement fails
    the test instead of skipping it.
    """
    selected = selected_backend(config)
    if selected != "all" and backend != selected:
        pytest.skip(
            f"End-to-end tests for '{backend}' are skipped because this run selected "
            f"'{selected}'; rerun all backends with: pytest tests/e2e."
        )
    if backend == BACKEND_QEMU and platform.system() == "Darwin":
        if _qemu_binary_available():
            return
        message = (
            f"End-to-end tests for 'qemu' cannot run because QEMU is not installed; "
            f"run 'brew install qemu' and rerun tests in sandbox '{sandbox_name}'."
        )
        if selected == backend:
            pytest.fail(message)
        pytest.skip(message)
    require_backend_available(backend, config, sandbox_name=sandbox_name)


def e2e_artifact_dir(tmp_path: Path) -> Path:
    """Return the folder for this test's artifact, creating it.

    Uses ``$CELESTO_E2E_ARTIFACT_DIR`` when set, so a run keeps every report
    in one place (CI uploads it); otherwise pytest's *tmp_path*.
    """
    configured = os.environ.get(E2E_ARTIFACT_DIR_ENV)
    directory = Path(configured) if configured else tmp_path
    directory.mkdir(parents=True, exist_ok=True)
    return directory

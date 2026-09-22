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

"""Celesto.

A Python SDK for running AI agents and executing untrusted code in a secure,
sandboxed environment.
"""

from importlib.metadata import version as _pkg_version

from celesto._compat import apply_legacy_environment_aliases
from celesto._terminal import TerminalConnection
from celesto.callbacks import Callback, CommandBlockedError, RunContext
from celesto.exceptions import (
    CelestoError,
    CloudAPIError,
    CommandExecutionUnavailableError,
    FirecrackerAPIError,
    HostError,
    ImageError,
    NetworkError,
    OperationTimeoutError,
    QemuDirtyBitmapStateError,
    SnapshotAlreadyExistsError,
    SnapshotNotFoundError,
    ValidationError,
    VMAlreadyExistsError,
    VMNotFoundError,
)
from celesto.facade import Celesto
from celesto.host.manager import HostManager
from celesto.images.boot import BootImage, DirectKernelBoot, FirmwareBoot
from celesto.images.builder import SSH_BOOT_ARGS, DockerRootfsBuilder, ImageBuilder
from celesto.images.manager import (
    ImageManager,
    ImageSource,
    LocalImage,
    S3ImageManifest,
    S3ImageRef,
)
from celesto.kernels import ensure_base_kernel_for_backend
from celesto.runtime.base import QemuDirtyBitmapBackup, QemuDirtyBitmapStatus
from celesto.sdk import CloudComputer, Computer, LocalComputer
from celesto.ssh import SSHClient
from celesto.types import (
    BrowserConnection,
    BrowserViewport,
    CommandEvent,
    CommandExitEvent,
    CommandOutputEvent,
    CommandResult,
    CommandStartedEvent,
    ComputerEvent,
    ComputerSandboxProtocol,
    DesktopEndpoint,
    DisplayConnection,
    DisplaySandboxProtocol,
    GuestFlushPolicy,
    GuestOS,
    InternetSettings,
    MacOSMachineConfig,
    NetworkAttachmentConfig,
    NetworkConfig,
    PublishedPort,
    QemuMachine,
    SnapshotArtifacts,
    SnapshotCapturePolicy,
    SnapshotInfo,
    SnapshotType,
    VMConfig,
    VMInfo,
    VMState,
    WorkspaceMount,
)
from celesto.vm import CelestoManager

apply_legacy_environment_aliases()

__version__ = _pkg_version("celesto")

__all__ = [
    "BrowserConnection",
    "DisplayConnection",
    # Core classes
    "Computer",
    "LocalComputer",
    "CloudComputer",
    "TerminalConnection",
    "Celesto",
    "CelestoManager",
    # Callbacks / hooks
    "Callback",
    "RunContext",
    "CommandBlockedError",
    # Image management
    "ImageManager",
    "ImageBuilder",
    "DockerRootfsBuilder",
    "BootImage",
    "DirectKernelBoot",
    "FirmwareBoot",
    "SSH_BOOT_ARGS",
    "ImageSource",
    "LocalImage",
    "S3ImageManifest",
    "S3ImageRef",
    "ensure_base_kernel_for_backend",
    # Host setup
    "HostManager",
    # SSH
    "SSHClient",
    # Data models
    "InternetSettings",
    "NetworkAttachmentConfig",
    "VMConfig",
    "VMInfo",
    "VMState",
    "NetworkConfig",
    "QemuMachine",
    "QemuDirtyBitmapBackup",
    "QemuDirtyBitmapStatus",
    "SnapshotArtifacts",
    "SnapshotCapturePolicy",
    "SnapshotInfo",
    "SnapshotType",
    "GuestFlushPolicy",
    "CommandResult",
    "PublishedPort",
    "CommandEvent",
    "CommandStartedEvent",
    "CommandOutputEvent",
    "CommandExitEvent",
    "ComputerEvent",
    "ComputerSandboxProtocol",
    "DesktopEndpoint",
    "DisplaySandboxProtocol",
    "BrowserViewport",
    "WorkspaceMount",
    "GuestOS",
    "MacOSMachineConfig",
    # Exceptions
    "CelestoError",
    "CloudAPIError",
    "CommandExecutionUnavailableError",
    "SnapshotAlreadyExistsError",
    "SnapshotNotFoundError",
    "QemuDirtyBitmapStateError",
    "ValidationError",
    "VMAlreadyExistsError",
    "VMNotFoundError",
    "NetworkError",
    "HostError",
    "ImageError",
    "FirecrackerAPIError",
    "OperationTimeoutError",
]

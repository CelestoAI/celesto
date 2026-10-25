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

"""The host↔guest transport interface shared by SSH and vsock.

``CommChannel`` is the least-common-denominator surface every caller already
uses: run a command, push/pull a file, wait until the guest answers, and
close. :class:`~celesto.ssh.SSHClient` satisfies it structurally (it predates
this protocol), and :class:`~celesto.comm.rust_http_vsock_channel.RustHttpVsockChannel`
implements it explicitly. Keeping the interface this narrow means env-var
injection (``celesto.env``) works over either transport with no code change — it
only ever calls :meth:`run` and :meth:`put_file`.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from celesto.exceptions import CelestoError
from celesto.types import CommandEvent, CommandResult

CommChannelKind = Literal["ssh", "vsock"]

MAX_RUN_OUTPUT_BYTES = 8 * 1024 * 1024
"""Host-owned cap on the output ``run`` returns in one result, on every transport."""


def run_output_too_large_error(max_bytes: int) -> CelestoError:
    """Error for a ``run`` result the host refuses to buffer whole."""
    return CelestoError(
        f"Command output (stdout and stderr together) exceeded the output limit of "
        f"{max_bytes} bytes, so it cannot be returned in one result. Use run_stream to read "
        "large output as it arrives."
    )


"""Which transport a VM uses for its control plane."""

ShellMode = Literal["login", "raw"]
"""``login`` wraps the command in the guest login shell; ``raw`` runs it
verbatim. Mirrors :data:`celesto.ssh.ShellMode`."""


@runtime_checkable
class CommChannel(Protocol):
    """Host-side handle for driving a single guest.

    Implementations keep their own connection state and (re)connect lazily,
    so a channel can be constructed before the guest is reachable and used
    once :meth:`wait_ready` returns.
    """

    kind: CommChannelKind

    def run(
        self,
        command: str,
        timeout: float = 30,
        shell: ShellMode = "login",
    ) -> CommandResult:
        """Execute *command* on the guest and return its result."""
        ...

    def run_stream(
        self,
        command: str,
        timeout: float = 30,
        shell: ShellMode = "login",
    ) -> Iterator[CommandEvent]:
        """Execute *command* and yield output as it arrives."""
        ...

    def sync(self, timeout: float = 10) -> None:
        """Flush guest filesystem buffers."""
        pass

    def put_file(self, local_path: str | Path, remote_path: str) -> None:
        """Upload a local file to *remote_path* in the guest."""
        ...

    def get_file(
        self,
        remote_path: str,
        local_path: str | Path,
        *,
        max_bytes: int | None = None,
    ) -> Path:
        """Download *remote_path* from the guest to *local_path*."""
        ...

    def wait_ready(self, timeout: float = 60.0, interval: float = 0.1) -> None:
        """Block until the guest answers, or raise on timeout."""
        ...

    def close(self) -> None:
        """Release any connection held by the channel."""
        ...

    @property
    def connected(self) -> bool:
        """Whether the channel currently holds a live connection."""
        ...

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

"""Read a Linux sandbox's identity from inside the guest.

The image's startup script (``_IDENTITY_RESET_SCRIPT`` in
``celesto.images.builder``) saves the instance ID it booted with, the machine
ID and the SSH host keys. One guest command reads all of them back, so the
host can record and compare identities without depending on guest tools
beyond ``cat``.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
from dataclasses import dataclass

# Paths written by the startup script's identity reset.
INSTANCE_ID_PATH = "/etc/celesto/instance-id"
INSTANCE_ID_MARKER_PATH = "/etc/celesto/features/instance-id"
SSH_HOST_KEY_PATH = "/etc/ssh/ssh_host_ed25519_key.pub"
MACHINE_ID_PATH = "/etc/machine-id"

# One ``key=value`` line per field. Run with ``shell="raw"`` (``/bin/sh -c``).
GUEST_IDENTITY_COMMAND = (
    f"if [ -e {INSTANCE_ID_MARKER_PATH} ]; then echo supports_instance_id=1; fi; "
    f"printf 'instance_id=%s\\n' \"$(cat {INSTANCE_ID_PATH} 2>/dev/null)\"; "
    f"printf 'machine_id=%s\\n' \"$(cat {MACHINE_ID_PATH} 2>/dev/null)\"; "
    f"printf 'host_key=%s\\n' \"$(cat {SSH_HOST_KEY_PATH} 2>/dev/null)\""
)


@dataclass(frozen=True, slots=True)
class GuestIdentityReport:
    """What a running guest reported about its identity.

    Attributes:
        supports_instance_id: The startup script understands instance IDs.
        instance_id: The instance ID the guest saved at boot.
        machine_id: The guest's machine ID.
        ssh_host_key_fingerprint: OpenSSH ``SHA256:...`` fingerprint of the
            guest's Ed25519 host key.
    """

    supports_instance_id: bool
    instance_id: str | None
    machine_id: str | None
    ssh_host_key_fingerprint: str | None


def ssh_host_key_fingerprint(public_key_line: str) -> str | None:
    """Return the ``SHA256:...`` fingerprint ``ssh-keygen -l`` shows for a key.

    Args:
        public_key_line: One OpenSSH public key line (``type base64 [comment]``).

    Returns:
        The fingerprint, or ``None`` when the line is not a public key.
    """
    fields = public_key_line.split()
    if len(fields) < 2:
        return None
    try:
        blob = base64.b64decode(fields[1], validate=True)
    except (binascii.Error, ValueError):
        return None
    digest = base64.b64encode(hashlib.sha256(blob).digest()).decode("ascii")
    return f"SHA256:{digest.rstrip('=')}"


def parse_guest_identity(stdout: str) -> GuestIdentityReport:
    """Parse the output of :data:`GUEST_IDENTITY_COMMAND`."""
    values: dict[str, str] = {}
    for line in stdout.splitlines():
        key, sep, value = line.partition("=")
        if sep and key not in values:
            values[key] = value.strip()
    host_key = values.get("host_key") or ""
    return GuestIdentityReport(
        supports_instance_id=values.get("supports_instance_id") == "1",
        instance_id=values.get("instance_id") or None,
        machine_id=values.get("machine_id") or None,
        ssh_host_key_fingerprint=ssh_host_key_fingerprint(host_key) if host_key else None,
    )

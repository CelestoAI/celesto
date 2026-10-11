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

"""A child made from a copy of a source's disk keeps the source's settings (D19).

``tests/e2e/test_create_from_disk.py`` checks this on real sandboxes, but a
real run can use only the settings its host supports (no bridge on macOS, no
tap without root). This test gives one source every setting at once and
checks the config a child is created with. Failure modes, written before
the test:

1. A copied setting is reset to its default instead of kept: CPU, memory,
   guest OS, backend, kernel and boot settings, disk size, internet policy
   (mode and allowed domains), network speed limit, network type (QEMU
   network, NAT or bridge), SSH public key or environment variables.
2. ``retain_disk_on_delete`` is copied, so every deleted child leaves its
   disk behind.
3. The source's own resources are copied: instance ID, vsock CID or socket,
   port-forward host ports, or the ``ip=`` / ``celesto.instance_id=`` boot
   arguments, so a child boots with the source's address or identity.
4. Other boot arguments are lost or reordered while those two are removed.
5. The source's stored config is changed by making the child's.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from celesto.types import (
    GuestOS,
    InternetSettings,
    NetworkAttachmentConfig,
    PortForwardConfig,
    VMConfig,
    VMInfo,
    VMState,
    VsockConfig,
)
from celesto.vm import CelestoManager

_INSTANCE_ID = "0123456789abcdef0123456789abcdef"
_SSH_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOfork user@laptop"
_BOOT_ARGS = (
    "console=ttyS0 reboot=k ip=172.16.0.2::172.16.0.1:255.255.255.252::eth0:off "
    f"panic=1 celesto.instance_id={_INSTANCE_ID} init=/init"
)
_CHILD_BOOT_ARGS = "console=ttyS0 reboot=k panic=1 init=/init"

# Every setting D19 says a child keeps, with a non-default value.
_COMMON: dict[str, Any] = {
    "vcpu_count": 3,
    "memory": 1536,
    "guest_os": GuestOS.UBUNTU,
    "disk_size_mib": 4096,
    "grow_filesystem": True,
    "env_vars": {"API_KEY": "secret", "MODE": "fork"},
    "ssh_public_key": _SSH_KEY,
    "ssh_capable": True,
    "comm_channel": "vsock",
    "boot_args": _BOOT_ARGS,
    # Not copied (D19, D20): the source's own resources and disk setting.
    "retain_disk_on_delete": True,
    "instance_id": _INSTANCE_ID,
}

_SOURCES = {
    "qemu-tap-allowed-domains": {
        **_COMMON,
        "backend": "qemu",
        "qemu_network": "tap",
        "internet_settings": InternetSettings(allowed_domains=("example.com", "pypi.org")),
        "network_rate_limit_mbps": 50,
        "vsock": VsockConfig(guest_cid=77),
        "port_forwards": [PortForwardConfig(host_port=18080, guest_port=8080)],
    },
    "firecracker-internet-off": {
        **_COMMON,
        "backend": "firecracker",
        "internet_settings": InternetSettings(mode="off"),
        "network_rate_limit_mbps": 10,
        "vsock": VsockConfig(guest_cid=79, uds_path="/tmp/src.vsock"),
    },
    "firecracker-bridge": {
        **_COMMON,
        "backend": "firecracker",
        "network_attachment": NetworkAttachmentConfig(mode="bridge", bridge="br-lab"),
        "guest_managed_networking": True,
        "network_rate_limit_mbps": 20,
        "vsock": VsockConfig(guest_cid=78, uds_path="/tmp/src.vsock"),
    },
}

_NOT_COPIED = {"vm_id", "instance_id", "retain_disk_on_delete", "vsock", "port_forwards"}


def _source_info(tmp_path: Path, values: dict[str, Any]) -> VMInfo:
    kernel = tmp_path / "vmlinux"
    kernel.touch()
    suffix = ".ext4" if values["backend"] == "firecracker" else ".qcow2"
    config = VMConfig.model_validate(
        {
            "vm_id": "src",
            "kernel_path": kernel,
            "rootfs_path": tmp_path / f"src{suffix}",
            **values,
        },
        context={"validate_paths": False},
    )
    return VMInfo(vm_id="src", status=VMState.STOPPED, config=config)


@pytest.mark.parametrize("source_id", list(_SOURCES))
def test_a_child_keeps_the_sources_settings_and_gets_its_own_resources(
    tmp_path: Path, source_id: str
) -> None:
    values = _SOURCES[source_id]
    source = _source_info(tmp_path, values)
    before = source.config.model_dump()
    manager = CelestoManager(data_dir=tmp_path / "data")

    child = manager._config_for_disk_copy(source, "src-1")

    # 1. Each D19 setting, against the value the source was given.
    assert child.vm_id == "src-1"
    assert child.vcpu_count == 3
    assert child.memory == 1536
    assert child.guest_os is GuestOS.UBUNTU
    assert child.backend == values["backend"]
    assert child.kernel_path == tmp_path / "vmlinux"
    assert child.disk_size_mib == 4096
    assert child.grow_filesystem is True
    assert child.env_vars == {"API_KEY": "secret", "MODE": "fork"}
    assert child.ssh_public_key == _SSH_KEY
    assert child.comm_channel == "vsock"
    assert child.network_rate_limit_mbps == values["network_rate_limit_mbps"]
    if source_id == "qemu-tap-allowed-domains":
        assert child.qemu_network == "tap"
        assert child.internet_settings == InternetSettings(
            allowed_domains=("example.com", "pypi.org")
        )
        assert child.network_attachment == NetworkAttachmentConfig(mode="nat")
    elif source_id == "firecracker-internet-off":
        assert child.internet_settings == InternetSettings(mode="off")
    else:
        assert child.network_attachment == NetworkAttachmentConfig(mode="bridge", bridge="br-lab")
        assert child.guest_managed_networking is True
    # Nothing else is dropped: every field outside the not-copied list matches.
    assert child.model_dump(exclude=_NOT_COPIED | {"boot_args"}) == source.config.model_dump(
        exclude=_NOT_COPIED | {"boot_args"}
    )

    # 2 and 3. Not copied.
    assert child.retain_disk_on_delete is False
    assert child.instance_id is None
    assert child.vsock is None
    assert child.port_forwards == []
    # 3 and 4. The source's address and identity leave the boot arguments;
    # the rest stay in order.
    assert child.boot_args == _CHILD_BOOT_ARGS

    # 5. The source is untouched.
    assert source.config.model_dump() == before

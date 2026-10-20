"""Backend routing for the credential proxy where no real VM can run here.

Linux TAP (Firecracker / QEMU TAP) and bridge mode can't boot on the macOS
dev host, so these isolated checks cover failure modes the macOS E2E test
(tests/e2e/test_credential_runtime.py) cannot reach:

1. The TAP DNAT rule is not scoped to the VM's own TAP, so another guest's
   traffic to the proxy address reaches this VM's proxy (D-05 lock 1).
2. The proxy listener binds a shared host address with no input drop, so
   another guest (or a host process) reaches it directly.
3. The DNAT target is the wrong address or port.
4. A TAP name is spliced into nft unchecked.
5. Bridge mode, a restricted network, or an unsupported backend silently
   "attaches" instead of failing closed with a recovery command (D-07).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from celesto.credentials.runtime import CredentialsUnsupported, _resolve_route
from celesto.host.network import NetworkManager


def _script(tap: str = "tap7") -> list[str]:
    manager = NetworkManager.__new__(NetworkManager)
    text = manager._credential_forward_script(
        tap, guest_proxy_ip="10.0.2.100", proxy_host_ip="172.16.0.1", proxy_port=40123
    )
    return text.splitlines()


def test_tap_forward_is_scoped_to_its_own_tap_and_drops_everyone_else() -> None:
    lines = _script()
    dnat = [line for line in lines if "dnat" in line]
    assert dnat == [
        'add rule inet celesto_cred_tap7 prerouting iifname "tap7" ip daddr 10.0.2.100 '
        "tcp dport 443 counter dnat ip to 172.16.0.1:40123"
    ]
    assert (
        "add rule inet celesto_cred_tap7 input ip daddr 172.16.0.1 tcp dport 40123 "
        'iifname != "tap7" counter drop'
    ) in lines


def test_tap_forward_rejects_unmanaged_interface_names() -> None:
    with pytest.raises(ValueError):
        _script('tap7" ; flush ruleset ; "')


def _vm(*, mode="nat", internet="open", egress=None, qemu_network="slirp"):
    network = SimpleNamespace(
        mode=mode,
        egress_proxy_host_port=egress,
        gateway_ip=None if mode == "bridge" else "172.16.0.1",
        tap_device="tap7",
    )
    config = SimpleNamespace(
        internet_settings=SimpleNamespace(mode=internet), qemu_network=qemu_network
    )
    return SimpleNamespace(vm_id="my-sbx", network=network, config=config)


@pytest.mark.parametrize(
    ("vm", "backend", "reason"),
    [
        (_vm(mode="bridge"), "firecracker", "bridge"),
        (_vm(internet="off"), "qemu", "restricted_network"),
        (_vm(egress=3128), "qemu", "restricted_network"),
        (_vm(), "libkrun", "backend"),
    ],
)
def test_unsupported_networks_fail_closed_with_recovery(vm, backend, reason) -> None:
    with pytest.raises(CredentialsUnsupported) as caught:
        _resolve_route(vm, backend)
    assert caught.value.details["reason"] == reason
    assert "'celesto sandbox delete my-sbx'" in caught.value.message


def test_supported_networks_pick_their_route() -> None:
    assert _resolve_route(_vm(), "qemu").kind == "slirp"
    assert _resolve_route(_vm(qemu_network="tap"), "qemu").kind == "tap"
    assert _resolve_route(_vm(), "firecracker").kind == "tap"

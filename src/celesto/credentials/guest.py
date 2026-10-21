# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""Put a sandbox's credential setup into the guest: CA, host routes, files.

Everything written here is public or a placeholder; real values never reach
the guest. Each step runs as one root ``sh`` script over the sandbox's
control channel (SSH or the guest agent), with payloads base64-encoded so no
shell quoting can change them.
"""

from __future__ import annotations

import base64
import posixpath
import shlex
from collections.abc import Callable, Iterable, Mapping
from typing import Any

from celesto.credentials._runtime_paths import PROXY_GUEST_IP, PROXY_GUEST_IPV6
from celesto.credentials.types import GuestFile
from celesto.exceptions import CelestoError

CA_PATH = "/usr/local/share/ca-certificates/celesto-sandbox.crt"
SYSTEM_BUNDLE = "/etc/ssl/certs/ca-certificates.crt"
"""Debian/Ubuntu/Alpine system bundle that ``update-ca-certificates`` rebuilds."""

HOSTS_BEGIN = "# BEGIN celesto-credentials (managed; do not edit)"
HOSTS_END = "# END celesto-credentials"

CA_ENV = {
    "NODE_EXTRA_CA_CERTS": SYSTEM_BUNDLE,
    "SSL_CERT_FILE": SYSTEM_BUNDLE,
    "REQUESTS_CA_BUNDLE": SYSTEM_BUNDLE,
}
"""``SSL_CERT_FILE`` and ``REQUESTS_CA_BUNDLE`` replace a client's whole store,
so they must be the bundle. Python ``requests`` reads only the latter (D-25)."""


def _b64(data: str | bytes) -> str:
    raw = data.encode() if isinstance(data, str) else data
    return base64.b64encode(raw).decode("ascii")


def run_script(channel: Any, script: str, *, what: str, sandbox_id: str, timeout: int = 60) -> str:
    result = channel.run(f"sh -c {shlex.quote(script)}", timeout=timeout, shell="raw")
    if result.exit_code != 0:
        raise CelestoError(
            f"Celesto couldn't finish setting up credential protection in {sandbox_id} "
            f"({what}). Run 'celesto computer stop {sandbox_id}' and "
            f"'celesto computer start {sandbox_id}' to try again.",
            {"vm_id": sandbox_id, "step": what, "exit_code": result.exit_code},
        )
    return str(result.stdout)


def hosts_block(hosts: Iterable[str]) -> str:
    """Return the managed ``/etc/hosts`` block mapping *hosts* to the proxy.

    Both families point at the proxy (the IPv6 entry is the IPv4-mapped
    address), so an AAAA-only lookup cannot skip it (D-04).
    """
    names = sorted({h.strip().lower() for h in hosts if h.strip()})
    if not names:
        return ""
    lines = [HOSTS_BEGIN]
    for name in names:
        lines.append(f"{PROXY_GUEST_IP} {name}")
        lines.append(f"{PROXY_GUEST_IPV6} {name}")
    lines.append(HOSTS_END)
    return "\n".join(lines) + "\n"


def install_ca(channel: Any, ca_cert_pem: str, *, sandbox_id: str) -> None:
    """Trust this run's proxy CA in the guest (D-14). Replaces any older one."""
    script = (
        "set -e\n"
        "command -v update-ca-certificates >/dev/null 2>&1 || exit 3\n"
        f"mkdir -p {shlex.quote(posixpath.dirname(CA_PATH))}\n"
        f"tmp=$(mktemp {shlex.quote(CA_PATH)}.XXXXXX)\n"
        f'printf %s {_b64(ca_cert_pem)} | base64 -d > "$tmp"\n'
        'chmod 644 "$tmp"\n'
        f'mv -f "$tmp" {shlex.quote(CA_PATH)}\n'
        "update-ca-certificates --fresh >/dev/null 2>&1 || update-ca-certificates >/dev/null\n"
        f"grep -q 'BEGIN CERTIFICATE' {shlex.quote(SYSTEM_BUNDLE)}\n"
    )
    run_script(channel, script, what="trusting its certificate", sandbox_id=sandbox_id, timeout=120)


def write_hosts(channel: Any, hosts: Iterable[str], *, sandbox_id: str) -> None:
    """Replace the managed ``/etc/hosts`` block; an empty *hosts* removes it."""
    block = hosts_block(hosts)
    script = (
        "set -e\n"
        "tmp=$(mktemp /etc/.celesto-hosts.XXXXXX)\n"
        f"awk -v b={shlex.quote(HOSTS_BEGIN)} -v e={shlex.quote(HOSTS_END)} "
        "'$0==b{skip=1;next} $0==e{skip=0;next} !skip' /etc/hosts > \"$tmp\" || true\n"
        + (f'printf %s {_b64(block)} | base64 -d >> "$tmp"\n' if block else "")
        + 'chmod 644 "$tmp"\n'
        # /etc/hosts can be a bind mount; fall back to rewriting in place.
        'mv -f "$tmp" /etc/hosts 2>/dev/null || { cat "$tmp" > /etc/hosts; rm -f "$tmp"; }\n'
    )
    run_script(channel, script, what="routing its hosts", sandbox_id=sandbox_id)


def write_files(channel: Any, files: Iterable[GuestFile], *, sandbox_id: str) -> None:
    """Write placeholder files atomically with their modes."""
    for item in files:
        if not posixpath.isabs(item.path) or ".." in item.path.split("/"):
            raise ValueError(f"Guest file path must be absolute: {item.path!r}")
        target = shlex.quote(item.path)
        parent = shlex.quote(posixpath.dirname(item.path))
        script = (
            "set -e\n"
            f"mkdir -p {parent}\n"
            f"tmp=$(mktemp {parent}/.celesto.XXXXXX)\n"
            f'printf %s {_b64(item.content)} | base64 -d > "$tmp"\n'
            f'chmod {item.mode & 0o7777:o} "$tmp"\n'
            f'mv -f "$tmp" {target}\n'
        )
        run_script(channel, script, what=f"writing {item.path}", sandbox_id=sandbox_id)


def install(
    channel: Any,
    *,
    sandbox_id: str,
    ca_cert_pem: str,
    hosts: Iterable[str],
    env: Mapping[str, str],
    files: Iterable[GuestFile],
    set_env: Callable[[dict[str, str]], object],
) -> None:
    """Install everything one start needs, before any user process runs.

    *set_env* writes the guest's managed env (placeholders plus the CA env
    vars), merged with what is already there.
    """
    install_ca(channel, ca_cert_pem, sandbox_id=sandbox_id)
    write_hosts(channel, hosts, sandbox_id=sandbox_id)
    write_files(channel, files, sandbox_id=sandbox_id)
    set_env({**CA_ENV, **dict(env)})

# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""User-defined secrets that stay on your machine (D-11).

A secret is a name, the exact hosts its real value may be sent to, and where
the value comes from (an env var on your machine with the same name). Celesto
stores only that definition and a random placeholder with the sandbox. The
guest sees the placeholder; the per-sandbox proxy swaps in the real value on
requests to the bound hosts. The real value is re-read on every start (D-09).
"""

from __future__ import annotations

import ipaddress
import os
import re
import secrets as _secrets
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, field_validator

from celesto.credentials.types import Binding, HeaderRule
from celesto.exceptions import ValidationError

if TYPE_CHECKING:
    from celesto.storage._protocol import StateManagerProtocol, UserSecretRecord

_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_LABEL = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
_HOST_RE = re.compile(rf"^{_LABEL}(?:\.{_LABEL})+$")
_HEADER_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
# Headers the proxy must never rewrite: routing, framing, and cookies.
_FORBIDDEN_HEADERS = frozenset(
    {"host", "content-length", "transfer-encoding", "connection", "upgrade", "cookie"}
)

SecretStatus = Literal["active", "missing", "proxy stopped"]


def _host_error(raw: str) -> ValidationError:
    text = raw.strip()
    if "*" in text:
        return ValidationError(
            f"'{text}' has a wildcard, but Celesto can only protect exact host names. "
            "Pass each host on its own, such as 'api.example.com'."
        )
    parsed = urlsplit(text if "//" in text else f"//{text}")
    hostname = (parsed.hostname or "").lower()
    if hostname and hostname != text.lower() and _HOST_RE.fullmatch(hostname):
        return ValidationError(f"'{text}' isn't a host name. Use just the host: '{hostname}'.")
    return ValidationError(
        f"'{text}' isn't a host name. Use the API's host name, such as 'api.example.com'."
    )


def normalize_host(raw: str) -> str:
    """Return *raw* as a lowercase exact host name, or raise ``ValidationError``."""
    host = raw.strip().lower().rstrip(".")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValidationError(
            f"'{raw}' is an IP address, but Celesto can only protect host names such as "
            "'api.example.com'."
        )
    if not _HOST_RE.fullmatch(host):
        raise _host_error(raw)
    return host


def validate_secret_name(name: str) -> str:
    """Return *name* if it is a valid env var name, else raise ``ValidationError``."""
    if not _NAME_RE.fullmatch(name):
        raise ValidationError(
            f"'{name}' isn't a valid secret name. Use letters, digits, and underscores, "
            "such as 'STRIPE_KEY'."
        )
    return name


def normalize_header(raw: str) -> str:
    """Return *raw* as a lowercase header name the proxy may rewrite."""
    header = raw.strip().lower()
    if not _HEADER_RE.fullmatch(header) or header in _FORBIDDEN_HEADERS:
        raise ValidationError(
            f"'{raw}' can't carry a secret. Use a header such as 'authorization' or 'x-api-key'."
        )
    return header


class Secret(BaseModel):
    """A secret that stays on your machine and is sent only to *host*.

    The real value comes from the env var with the same name as the secret, in
    the process that starts the sandbox. The computer sees only a placeholder.

    Args:
        host: The exact host name (or several) the real value may be sent to,
            such as ``"api.stripe.com"``.
        header: Optional header the program sends the placeholder in. By
            default Celesto looks in ``Authorization`` (Bearer, Basic or token) and
            ``x-api-key``.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    host: str | tuple[str, ...]
    header: str | None = None

    @field_validator("host", mode="before")
    @classmethod
    def _normalize_hosts(cls, value: object) -> object:
        items = [value] if isinstance(value, str) else list(value)  # type: ignore[call-overload]
        if not items:
            raise ValueError("Secret needs at least one host, such as host='api.example.com'.")
        hosts = tuple(dict.fromkeys(normalize_host(str(item)) for item in items))
        return hosts[0] if len(hosts) == 1 else hosts

    @field_validator("header")
    @classmethod
    def _normalize_header(cls, value: str | None) -> str | None:
        return None if value is None else normalize_header(value)

    @property
    def hosts(self) -> tuple[str, ...]:
        """All bound hosts as a tuple."""
        return (self.host,) if isinstance(self.host, str) else self.host


def header_rules(header: str | None) -> tuple[HeaderRule, ...]:
    """Return where the proxy looks for a user secret's placeholder."""
    authorization = (
        HeaderRule("authorization", "bearer"),
        HeaderRule("authorization", "basic_password"),
        HeaderRule("authorization", "token"),
    )
    if header is None:
        return (*authorization, HeaderRule("x-api-key", "raw"))
    if header == "authorization":
        return authorization
    return (HeaderRule(header, "raw"),)


def new_placeholder() -> str:
    """Return a fresh random placeholder. Not secret; unique per sandbox and secret."""
    return f"celesto-placeholder-{_secrets.token_hex(16)}"


def env_source(name: str) -> str:
    """Return the source string for a secret read from the env var *name*."""
    return f"env:{name}"


def resolve(source: str, environ: Mapping[str, str] | None = None) -> str | None:
    """Read a real value from *source* (``env:NAME``). Never stored or logged."""
    kind, _, key = source.partition(":")
    if kind != "env" or not key:
        return None
    value = (os.environ if environ is None else environ).get(key)
    return value or None


def binding_from_record(record: UserSecretRecord) -> Binding:
    """Build the proxy binding for a stored secret."""
    return Binding(
        name=record["name"],
        placeholder=record["placeholder"],
        hosts=tuple(record["hosts"]),
        headers=header_rules(record["header"]),
        source=record["source"],
    )


def binding_wire(binding: Binding) -> dict[str, Any]:
    """Return a binding as the proxy control channel expects it (no ``source``)."""
    data = asdict(binding)
    data.pop("source", None)
    data["hosts"] = list(binding.hosts)
    data["headers"] = [asdict(rule) for rule in binding.headers]
    return data


def missing_warning(name: str, sandbox: str) -> str:
    """Return the D-09 warning for a secret whose env var is not set."""
    return (
        f"{name} isn't set in this terminal, so {sandbox} can't use it. Set it, then run "
        f"'celesto computer stop {sandbox}' and 'celesto computer start {sandbox}'."
    )


def ensure_seeded(state: StateManagerProtocol, sandbox_id: str) -> None:
    """Copy ``VMConfig.secrets`` into the sandbox's stored secrets, once."""
    if not state.claim_user_secret_seed(sandbox_id):
        return
    config_secrets: Mapping[str, Secret] = getattr(state.get_vm(sandbox_id).config, "secrets", {})
    existing = {record["name"] for record in state.list_user_secrets(sandbox_id)}
    for name, secret in sorted(config_secrets.items()):
        if name in existing:
            continue
        define(state, sandbox_id, name, secret)


def define(
    state: StateManagerProtocol, sandbox_id: str, name: str, secret: Secret
) -> UserSecretRecord:
    """Store or update a secret definition; keep its placeholder if it exists."""
    from celesto.storage._protocol import UserSecretRecord

    validate_secret_name(name)
    current = {record["name"]: record for record in state.list_user_secrets(sandbox_id)}
    placeholder = current[name]["placeholder"] if name in current else new_placeholder()
    record = UserSecretRecord(
        name=name,
        hosts=list(secret.hosts),
        source=env_source(name),
        header=secret.header,
        placeholder=placeholder,
    )
    state.put_user_secret(sandbox_id, record)
    return record


def records(state: StateManagerProtocol, sandbox_id: str) -> list[UserSecretRecord]:
    """Return the stored secrets for *sandbox_id* (seeding from config first)."""
    ensure_seeded(state, sandbox_id)
    return state.list_user_secrets(sandbox_id)


def plan_for(
    sandbox_id: str,
    state: StateManagerProtocol,
    environ: Mapping[str, str] | None = None,
) -> tuple[list[Binding], dict[str, str], list[str]]:
    """Return ``(bindings, guest_env, missing_warnings)`` for a sandbox start.

    Real values are not included; read them with :func:`resolve` on each
    binding's ``source``. A secret whose env var is unset still gets its
    binding and guest placeholder, so the guest stays stable and the proxy
    simply has nothing to inject.
    """
    bindings: list[Binding] = []
    guest_env: dict[str, str] = {}
    missing: list[str] = []
    for record in records(state, sandbox_id):
        bindings.append(binding_from_record(record))
        guest_env[record["name"]] = record["placeholder"]
        if resolve(record["source"], environ) is None:
            missing.append(missing_warning(record["name"], sandbox_id))
    return bindings, guest_env, missing


# ----------------------------------------------------------------------
# Live changes through the per-sandbox proxy (W3's control channel, D-15)
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class SecretChange:
    """What happened when a secret was set or removed.

    ``applied`` is ``live`` (the running proxy has it now), ``next_start``
    (the sandbox is not running), or ``not_applied`` (the sandbox is running
    but its credential protection could not be reached).
    """

    name: str
    hosts: tuple[str, ...]
    applied: Literal["live", "next_start", "not_applied"]
    value_found: bool


@dataclass(frozen=True)
class LiveResult:
    """Whether a change reached the running proxy."""

    applied: bool


def _control(sandbox_id: str, op: str, **kw: Any) -> dict[str, Any] | None:
    """Call the proxy control channel; return None when it is not reachable."""
    try:
        from celesto.credentials import runtime
    except ImportError:
        return None
    try:
        result = runtime.control(sandbox_id, op, **kw)
    except Exception:  # proxy stopped, socket gone, or refused
        return None
    return result if isinstance(result, dict) else {}


def apply_live_set(sandbox_id: str, binding: Binding, real_value: str) -> LiveResult:
    """Hand a binding and its real value to the running proxy."""
    result = _control(
        sandbox_id, "set_binding", binding=binding_wire(binding), real_value=real_value
    )
    return LiveResult(applied=result is not None)


def apply_live_remove(sandbox_id: str, name: str) -> LiveResult:
    """Tell the running proxy to stop injecting *name* at once."""
    result = _control(sandbox_id, "remove_binding", name=name)
    return LiveResult(applied=result is not None)


def proxy_status(sandbox_id: str) -> dict[str, Any] | None:
    """Return the proxy's status, or None when it is not running."""
    return _control(sandbox_id, "status")


def _active_names(status: Mapping[str, Any]) -> set[str] | None:
    """Names the proxy can inject (has a real value for), if it reports them."""
    raw = status.get("bindings")
    if raw is None:
        return None
    missing = set(status.get("missing") or ())
    names: set[str] = set()
    for item in raw:
        if isinstance(item, str):
            names.add(item)
        elif (
            isinstance(item, Mapping)
            and isinstance(item.get("name"), str)
            and item.get("has_value", True)
        ):
            names.add(item["name"])
    return names - missing


def list_rows(
    state: StateManagerProtocol,
    sandbox_id: str,
    *,
    running: bool,
    environ: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Return what ``secret list`` shows: never values or placeholders (D-18)."""
    status = proxy_status(sandbox_id) if running else None
    active = _active_names(status) if status is not None else None
    last_used: Mapping[str, Any] = (status or {}).get("last_used") or {}
    rows: list[dict[str, Any]] = []
    for record in records(state, sandbox_id):
        name = record["name"]
        state_label: SecretStatus
        if status is None:
            state_label = "proxy stopped"
        elif active is not None:
            state_label = "active" if name in active else "missing"
        else:
            state_label = "active" if resolve(record["source"], environ) else "missing"
        used = last_used.get(name)
        rows.append(
            {
                "name": name,
                "hosts": list(record["hosts"]),
                "source": record["source"],
                "status": state_label,
                "last_used": used if isinstance(used, str) else None,
            }
        )
    return rows


__all__ = [
    "LiveResult",
    "Secret",
    "SecretChange",
    "SecretStatus",
    "apply_live_remove",
    "apply_live_set",
    "binding_from_record",
    "binding_wire",
    "define",
    "ensure_seeded",
    "env_source",
    "header_rules",
    "list_rows",
    "missing_warning",
    "new_placeholder",
    "normalize_header",
    "normalize_host",
    "plan_for",
    "proxy_status",
    "records",
    "resolve",
    "validate_secret_name",
]

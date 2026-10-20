"""Per-sandbox credential proxy.

The sandbox only ever holds placeholders. This proxy runs on the host, accepts
the sandbox's HTTPS connections for the hosts a credential is bound to, and
swaps a placeholder for its real value in the request headers just before the
request leaves for the real host. See
``docs/designs/sandbox-credential-injection.md`` (D-08).

Typical use, from the per-VM launcher::

    proxy = CredentialProxy(listen="unix:/abs/proxy.sock", log_path="/abs/credentials.log")
    proxy.set_bindings([...])
    proxy.set_resolver(lambda name: real_values.get(name))
    info = proxy.start()  # {"address": ..., "ca_cert_pem": ...}
    ...
    proxy.stop()

Callbacks run on the proxy's own threads. A resolver returns the real value for
a binding name, or ``None`` to leave the placeholder in place.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping
from typing import Any

from . import _ffi

Resolver = Callable[[str], "str | None"]
LocalHandler = Callable[
    [str, str, list[tuple[str, str]], bytes],
    tuple[int, list[tuple[str, str]], bytes],
]

_NativeProxy: Any = getattr(_ffi, "_CredentialProxy", None)


def available() -> bool:
    """Return True when this wheel includes the credential proxy."""

    return _NativeProxy is not None


def _field(item: Any, name: str) -> Any:
    if isinstance(item, Mapping):
        return item[name]
    return getattr(item, name)


def _binding(item: Any) -> dict[str, Any]:
    return {
        "name": str(_field(item, "name")),
        "placeholder": str(_field(item, "placeholder")),
        "hosts": [str(h) for h in _field(item, "hosts")],
        "headers": [
            {"header": str(_field(rule, "header")), "form": str(_field(rule, "form"))}
            for rule in _field(item, "headers")
        ],
    }


def _route(item: Any) -> dict[str, str]:
    return {key: str(_field(item, key)) for key in ("host", "path", "handler")}


class CredentialProxy:
    """One proxy for one sandbox. Holds only that sandbox's credentials."""

    def __init__(
        self,
        *,
        listen: str,
        log_path: str,
        _upstream_ca_pem: str | None = None,
        _upstream_hosts: Mapping[str, str] | None = None,
    ) -> None:
        """Create a stopped proxy.

        ``listen`` is ``"unix:/abs/path.sock"`` or ``"tcp:127.0.0.1:0"``.
        ``log_path`` receives one JSON line per injection or refusal and never
        any real value or placeholder.

        ``_upstream_ca_pem`` and ``_upstream_hosts`` (host -> ``"ip:port"``)
        exist for tests only: they trust an extra upstream CA and skip DNS.
        """

        if _NativeProxy is None:
            raise RuntimeError("This celesto-core build does not include the credential proxy.")
        self._native = _NativeProxy(
            listen,
            log_path,
            _upstream_ca_pem,
            dict(_upstream_hosts) if _upstream_hosts is not None else None,
        )

    def start(self) -> dict[str, str]:
        """Generate a fresh CA in memory and start serving.

        Returns ``{"address": str, "ca_cert_pem": str}``. The CA private key
        never leaves this process.
        """

        return dict(self._native.start())

    def set_bindings(self, bindings: Iterable[Any]) -> None:
        """Replace all bindings. Each is a ``Binding`` or a dict of its fields.

        ``source`` is ignored. Raises ``ValueError`` for an invalid binding.
        """

        self._native.set_bindings(json.dumps([_binding(b) for b in bindings]))

    def set_local_routes(self, routes: Iterable[Any]) -> None:
        """Replace all local routes. Each is a ``LocalRoute`` or a dict."""

        self._native.set_local_routes(json.dumps([_route(r) for r in routes]))

    def set_resolver(self, fn: Resolver) -> None:
        """Set the callback that returns a binding's real value at injection time."""

        self._native.set_resolver(fn)

    def set_local_handler(self, handler_id: str, fn: LocalHandler) -> None:
        """Register ``fn(method, path, headers, body) -> (status, headers, body)``."""

        self._native.set_local_handler(handler_id, fn)

    def stats(self) -> dict[str, Any]:
        """Return ``{"connections": int, "active": int, "last_used": {name: iso8601}}``."""

        return dict(self._native.stats())

    def stop(self) -> None:
        """Stop serving and drop the CA key. Safe to call more than once."""

        self._native.stop()


__all__ = ["CredentialProxy", "LocalHandler", "Resolver", "available"]

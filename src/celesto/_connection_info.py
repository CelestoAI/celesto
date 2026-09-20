"""Validate connection credentials without including them in diagnostics."""

from datetime import UTC, datetime
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from celesto.exceptions import CelestoError

DisplayMode = Literal["read_only", "read_write"]


def validate_display_mode(mode: object) -> None:
    if not isinstance(mode, str) or mode not in ("read_only", "read_write"):
        raise ValueError("mode must be 'read_only' or 'read_write'.")


def cloud_connection_info(
    gateway_url: object, token: object, expiry: object
) -> tuple[str, datetime]:
    """Only explicit access to the returned URL should reveal credentials."""
    try:
        if not isinstance(gateway_url, str) or not isinstance(token, str) or not token.strip():
            raise ValueError
        if any(c.isspace() for c in gateway_url):
            raise ValueError
        url = urlsplit(gateway_url)
        local = url.hostname in {"localhost", "127.0.0.1", "::1"}
        if (
            not url.hostname
            or url.username is not None
            or url.password is not None
            or url.fragment
            or url.scheme not in ({"https", "wss", "http", "ws"} if local else {"https", "wss"})
        ):
            raise ValueError
        _ = url.port  # Reject malformed port numbers too.
        query = parse_qsl(url.query, keep_blank_values=True)
        if any(key.lower() == "token" for key, _ in query):
            raise ValueError
        if not isinstance(expiry, str):
            raise ValueError
        expires_at = datetime.fromisoformat(expiry)
        if expires_at.tzinfo is None or expires_at.utcoffset() is None:
            raise ValueError
        expires_at = expires_at.astimezone(UTC)
        if expires_at <= datetime.now(UTC):
            raise ValueError
        scheme = {"https": "wss", "http": "ws"}.get(url.scheme, url.scheme)
        return urlunsplit(
            (scheme, url.netloc, url.path, urlencode([*query, ("token", token)]), "")
        ), expires_at
    except (ValueError, TypeError, OverflowError):
        raise CelestoError(
            "Cloud returned invalid or expired connection details; request a new connection."
        ) from None

"""Which Celesto surface is making cloud requests.

The cloud backend records the surface that created each computer from the
``X-Celesto-Client`` header. Library callers are the SDK; the CLI entrypoint
switches this to ``cli`` for the length of one command. It lives in its own
module so the CLI can set it without importing the cloud HTTP client.
"""

from contextvars import ContextVar
from typing import Literal

ClientOrigin = Literal["sdk", "cli"]

client_origin: ContextVar[ClientOrigin] = ContextVar("celesto_client_origin", default="sdk")

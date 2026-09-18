# Copyright 2026 Celesto AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""Transient core state interfaces.

The SDK and HTTP API use :class:`MemoryStateManager`, which has no database
dependency. Persistent SQLite inventory is owned by :mod:`celesto.cli.state`.
"""

from __future__ import annotations

from celesto.storage._base import (
    IP_POOL_END,
    IP_POOL_START,
    SSH_PORT_END,
    SSH_PORT_START,
    ip_to_pool_index,
    pool_index_to_ip,
)
from celesto.storage._memory import MemoryStateManager
from celesto.storage._protocol import StateManagerProtocol

__all__ = [
    "IP_POOL_END",
    "IP_POOL_START",
    "SSH_PORT_END",
    "SSH_PORT_START",
    "MemoryStateManager",
    "StateManagerProtocol",
    "ip_to_pool_index",
    "pool_index_to_ip",
]

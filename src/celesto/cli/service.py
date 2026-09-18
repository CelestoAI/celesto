# Copyright 2026 Celesto AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""CLI composition root for persistent sandbox operations."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from celesto.storage import StateManagerProtocol
from celesto.vm import resolve_data_dir

if TYPE_CHECKING:
    from celesto.facade import Celesto
    from celesto.types import VMConfig
    from celesto.vm import CelestoManager


class CLIService:
    """Wire SDK handles to the CLI-owned SQLite inventory."""

    def __init__(self, data_dir: Path | None = None) -> None:
        from celesto.cli.state import create_cli_state_manager

        self.data_dir = resolve_data_dir(data_dir)
        self._state_manager = create_cli_state_manager(self.data_dir / "smolvm.db")

    def state_manager(self) -> StateManagerProtocol:
        """Return the inventory shared by this CLI service's handles."""
        return self._state_manager

    def manager(self, **kwargs: Any) -> CelestoManager:
        """Create a low-level manager backed by CLI inventory."""
        from celesto.vm import CelestoManager

        kwargs["state_manager"] = self.state_manager()
        return CelestoManager(**kwargs)

    def create_vm(self, config: VMConfig | None = None, **kwargs: Any) -> Celesto:
        """Create an SDK handle whose lifecycle is persisted for the CLI."""
        from celesto.facade import Celesto

        kwargs["state_manager"] = self.state_manager()
        return Celesto(config, **kwargs)

    def vm_from_id(self, vm_id: str, **kwargs: Any) -> Celesto:
        """Reconnect a CLI handle from persistent inventory."""
        from celesto.facade import Celesto

        kwargs["state_manager"] = self.state_manager()
        return Celesto.from_id(vm_id, **kwargs)

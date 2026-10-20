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

"""Run the real start decision on top of a stubbed manager.

``Celesto.start()`` asks the manager to choose between "already running",
"resume" and "boot" from the current inventory, inside the computer's
lifecycle lock. Facade tests stub the manager with ``MagicMock`` and set up
``start``/``resume``/``async_start``. :func:`use_real_start_decision` makes
the stub's ``start_from_current_state`` run the real manager code, with a
real lock, and route each action to those stubbed calls. The stub's
inventory is whatever it last reported for the computer.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import DEFAULT, MagicMock

from celesto.vm import CelestoManager


def use_real_start_decision(mock_sdk: MagicMock, lock_dir: Path | None = None) -> None:
    """Make *mock_sdk*'s start-from-current-state use the real manager code."""
    tracked: dict[str, Any] = {}

    def current(_vm_id: str) -> Any:
        if "info" in tracked:
            return tracked["info"]
        if mock_sdk.create.called:
            return mock_sdk.create.return_value
        return mock_sdk.get.return_value

    def remember(info: Any) -> Any:
        tracked["info"] = info
        return info

    manager = CelestoManager.__new__(CelestoManager)
    manager.data_dir = lock_dir or Path(tempfile.mkdtemp(prefix="celesto-start-decision-"))
    manager.state = SimpleNamespace(get_vm=current)
    manager._start_locked = lambda vm_id, boot_timeout=30.0: remember(
        mock_sdk.start(vm_id, boot_timeout=boot_timeout)
    )
    manager._resume_locked = lambda vm_id: remember(mock_sdk.resume(vm_id))

    async def async_start_locked(vm_id: str, boot_timeout: float = 30.0) -> Any:
        return remember(await mock_sdk.async_start(vm_id, boot_timeout=boot_timeout))

    manager._async_start_locked = async_start_locked

    mock_sdk.start_from_current_state = MagicMock(side_effect=manager.start_from_current_state)
    mock_sdk.async_start_from_current_state = manager.async_start_from_current_state
    # Later reads see the state the last start or resume produced.
    mock_sdk.get.side_effect = lambda vm_id: tracked.get("info", DEFAULT)

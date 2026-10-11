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

"""Stop and delete with a sandbox name that can't exist.

``stop`` and ``delete`` take a lock file named after the sandbox before they
look it up. Failure modes, written before the code:

1. A name with ``..`` or ``/`` makes the lock file land outside Celesto's
   locks folder, creating files elsewhere on the machine.
2. Such a name gets an error other than the not-found error any unknown
   sandbox name gets.
3. The async versions behave differently from the sync ones.
4. Another caller of the lock helper passes a name that leaves the locks
   folder, and the helper opens it anyway.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from celesto.exceptions import VMNotFoundError
from celesto.storage._memory import MemoryStateManager
from celesto.vm import CelestoManager

# "{tmp}" stands for the test's own folder, so an absolute name stays inside it.
_ESCAPING_NAMES = ["../../escaped", "../escaped", "sub/escaped", "{tmp}/escaped", ".."]


def _manager(tmp_path: Path) -> CelestoManager:
    data_dir = tmp_path / "home" / "data"
    return CelestoManager(data_dir=data_dir, state_manager=MemoryStateManager(data_dir))


def _files_outside_locks(tmp_path: Path, manager: CelestoManager) -> list[Path]:
    locks = manager.data_dir / "locks"
    return [
        path
        for path in tmp_path.rglob("*")
        if path.is_file() and "lock" in path.name and not path.is_relative_to(locks)
    ]


@pytest.mark.parametrize("name", _ESCAPING_NAMES)
@pytest.mark.parametrize("operation", ["stop", "delete", "async_stop", "async_delete"])
def test_stop_and_delete_of_an_impossible_name_report_not_found_and_write_nothing(
    tmp_path: Path, name: str, operation: str
) -> None:
    manager = _manager(tmp_path)
    name = name.format(tmp=tmp_path)

    with pytest.raises(VMNotFoundError) as caught:
        result = getattr(manager, operation)(name)
        if operation.startswith("async_"):
            asyncio.run(result)

    assert str(caught.value) == f"VM '{name}' not found"
    assert _files_outside_locks(tmp_path, manager) == []


@pytest.mark.parametrize("lock_name", ["../escaped.lock", "a/../../escaped.lock", "{tmp}/x.lock"])
def test_the_lock_helper_refuses_names_outside_the_locks_folder(
    tmp_path: Path, lock_name: str
) -> None:
    manager = _manager(tmp_path)

    with pytest.raises(ValueError):
        manager._acquire_operation_lock(lock_name.format(tmp=tmp_path))

    assert _files_outside_locks(tmp_path, manager) == []

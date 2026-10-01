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

"""The public ``fork()`` / ``fork_many()`` when a child fails or a warning appears.

``tests/e2e/test_sandbox_fork_cli.py`` proves the happy path on real
sandboxes, where every child boots and the source never stays paused. These
tests force what a real run can't. Failure modes, written before the code:

1. ``fork()`` returns a failed child, or ``None``, instead of raising.
2. ``fork()`` raises with a message other than the child's own (the words
   the CLI shows), or a type other than ``CelestoError``.
3. ``fork()`` drops a batch warning (such as the source staying paused), or
   emits it as a plain ``UserWarning`` that can't be filtered by Celesto's
   class, or points it at Celesto's code instead of the caller's line.
4. ``fork()`` / ``fork_many()`` don't pass the name or boot timeout through.
5. ``fork_many()`` raises for a per-child failure instead of returning it.
6. The async twins behave differently from the sync methods.
7. A valid name asked for with ``name=`` that is too long to number the
   children is called an invalid name, instead of saying how long it can be.

The fork engine is real; the disk copy, hypervisor and guest agent are
replaced at their boundaries (the ``world`` fixture), except for the warning
case, where the engine's result is supplied directly because a resume that
fails can't be produced through those boundaries.
"""

from __future__ import annotations

import asyncio
import warnings
from typing import Any

import pytest

from celesto import Celesto, CelestoError, CelestoWarning, ForkBatch, ForkResult
from celesto.types import VMState
from tests.vm.test_fork_children import _World, world  # noqa: F401 - fixture

_TIMEOUT_MESSAGE = (
    "Sandbox 'exp' didn't start within 45 seconds and was removed. "
    "Run the fork again with '--boot-timeout 90'."
)
_PAUSED_WARNING = (
    "Sandbox 'src' stayed paused after the fork. Run 'celesto sandbox resume src' to continue it."
)


def _call(use_async: bool, method: str, source: Celesto, *args: Any, **kwargs: Any) -> Any:
    if use_async:
        return asyncio.run(getattr(source, f"async_{method}")(*args, **kwargs))
    return getattr(source, method)(*args, **kwargs)


@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
def test_fork_returns_the_named_child(world: _World, use_async: bool) -> None:  # noqa: F811
    source = world.add_source("firecracker", VMState.STOPPED)

    child = _call(use_async, "fork", source, "exp", boot_timeout=45)

    assert isinstance(child, Celesto)
    assert child.vm_id == "exp"
    assert world.created == ["exp"]


@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
def test_fork_raises_the_childs_message_when_it_fails(
    world: _World,  # noqa: F811
    use_async: bool,
) -> None:
    source = world.add_source("firecracker", VMState.STOPPED)
    world.behavior["exp"] = "timeout"

    with pytest.raises(CelestoError) as caught:
        _call(use_async, "fork", source, "exp", boot_timeout=45)

    assert str(caught.value) == _TIMEOUT_MESSAGE
    assert world.deleted == ["exp"]


@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
def test_fork_many_returns_a_failed_child_instead_of_raising(
    world: _World,  # noqa: F811
    use_async: bool,
) -> None:
    source = world.add_source("firecracker", VMState.STOPPED)
    world.behavior["exp-2"] = "timeout"

    batch = _call(use_async, "fork_many", source, 2, name="exp", parallel=1, boot_timeout=45)

    assert isinstance(batch, ForkBatch)
    assert [(child.name, child.ok) for child in batch.children] == [
        ("exp-1", True),
        ("exp-2", False),
    ]
    assert batch.children[1].error == _TIMEOUT_MESSAGE.replace("'exp'", "'exp-2'")
    assert batch.source_state == VMState.STOPPED


@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
def test_fork_emits_batch_warnings_as_celesto_warnings_at_the_callers_line(
    world: _World,  # noqa: F811
    use_async: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = world.add_source("firecracker", VMState.STOPPED)
    child = Celesto.from_id("src", state_manager=world.state, data_dir=world.manager.data_dir)
    batch = ForkBatch(
        children=(ForkResult(name="exp", ok=True, sandbox=child),),
        warnings=(_PAUSED_WARNING,),
        source_state=VMState.PAUSED,
    )

    def fake(*args: Any, **kwargs: Any) -> ForkBatch:
        return batch

    async def async_fake(*args: Any, **kwargs: Any) -> ForkBatch:
        return batch

    monkeypatch.setattr(Celesto, "_fork_many", fake)
    monkeypatch.setattr(Celesto, "_async_fork_many", async_fake)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = _call(use_async, "fork", source, "exp")

    assert result is child
    assert [(w.category, str(w.message)) for w in caught] == [(CelestoWarning, _PAUSED_WARNING)]
    assert issubclass(CelestoWarning, UserWarning)
    if not use_async:
        assert caught[0].filename == __file__


def test_a_valid_name_too_long_to_number_says_how_long_it_can_be(
    world: _World,  # noqa: F811
) -> None:
    source = world.add_source("firecracker", VMState.STOPPED)
    name = "a" * 63

    with pytest.raises(CelestoError) as caught:
        source.fork_many(3, name=name)

    assert str(caught.value) == (
        f"'{name}' is too long to number 3 forks. "
        "Choose a name of up to 62 characters with '--name'."
    )
    assert world.created == []

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

"""Tests for the sandbox ID generator."""

from __future__ import annotations

import re

import pytest

from celesto._naming import MAX_PREFIX_LENGTH, SCIENTISTS, generate_sandbox_id
from celesto.types import _IDENTIFIER_PATTERN


def test_custom_prefix_keeps_scientist_and_suffix() -> None:
    sandbox_id = generate_sandbox_id(prefix="agent")
    prefix, scientist, suffix = sandbox_id.split("-")
    assert prefix == "agent"
    assert scientist in SCIENTISTS
    assert re.fullmatch(r"[a-z0-9]{6}", suffix)


def test_longest_allowed_prefix_always_passes_vm_id_validation() -> None:
    # Every scientist must fit, or creation would fail only on some random picks.
    prefix = "a" * MAX_PREFIX_LENGTH
    for scientist in SCIENTISTS:
        assert re.fullmatch(_IDENTIFIER_PATTERN, f"{prefix}-{scientist}-abc123")


def test_too_long_prefix_fails_every_time_with_clear_message() -> None:
    with pytest.raises(ValueError, match=f"at most {MAX_PREFIX_LENGTH} characters"):
        generate_sandbox_id(prefix="a" * (MAX_PREFIX_LENGTH + 1))

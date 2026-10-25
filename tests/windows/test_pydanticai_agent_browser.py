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

"""Unit tests for the PydanticAI agent-browser example helpers."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "examples" / "agent_tools" / "pydanticai_agent_browser.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("pydanticai_agent_browser", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_parser_accepts_optional_input_override() -> None:
    module = _load_module()

    args = module._build_parser().parse_args(["--input", "Open example.com"])

    assert isinstance(args, argparse.Namespace)
    assert args.input == "Open example.com"


def test_resolve_prompt_falls_back_to_demo_prompt() -> None:
    module = _load_module()

    assert module._resolve_prompt(None) == module.DEMO_PROMPT
    assert module._resolve_prompt("Open example.com") == "Open example.com"


@pytest.mark.asyncio
async def test_model_tool_cannot_execute_host_shell(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Untrusted model arguments never gain command execution on the operator machine."""
    module = _load_module()
    tools: list[Callable[..., Awaitable[str]]] = []

    class Agent:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def tool(self, **kwargs: object) -> Callable[[Callable[..., Awaitable[str]]], None]:
            return lambda fn: tools.append(fn)

    class ModelRetryError(Exception):
        pass

    class BrowserError(Exception):
        pass

    dependencies: dict[str, object] = {
        "pydantic_ai:Agent": Agent,
        "pydantic_ai:ModelRetry": ModelRetryError,
        "playwright.async_api:Error": BrowserError,
    }
    monkeypatch.setattr(module, "_require_dependency", lambda path, _hint: dependencies[path])
    module._build_agent()
    marker = tmp_path / "host-command-ran"

    async def title() -> str:
        return "Fixture"

    async def snapshot() -> str:
        return "Fixture content"

    page = SimpleNamespace(
        title=title,
        is_closed=lambda: False,
        url="https://example.com/",
        locator=lambda _selector: SimpleNamespace(aria_snapshot=snapshot),
    )
    ctx = SimpleNamespace(deps=module.BrowserCliDeps(page=page))
    with pytest.raises(ModelRetryError, match="Unknown browser action"):
        await tools[0](ctx, f"touch {marker}")
    assert not marker.exists(), "A model-selected command executed on the operator machine"
    assert "Fixture content" in await tools[0](ctx, "observe")

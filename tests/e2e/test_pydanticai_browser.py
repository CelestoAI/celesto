"""Exercise the example's registered tool with real PydanticAI and Chromium."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pydantic_ai.messages import ModelMessage, ModelResponse
    from pydantic_ai.models.function import AgentInfo

pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bad_operation",
    [
        {"action": "navigate", "value": "file:///etc/passwd"},
        {"action": "click", "role": "button", "name": "Missing button"},
        {"action": "fill", "role": "textbox", "name": "Missing field", "value": "text"},
        {"action": "scroll", "value": "sideways"},
    ],
)
async def test_registered_browser_tool_recovers_from_model_mistakes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, bad_operation: dict[str, str]
) -> None:
    """Value: tool errors are retried; normal browser work still completes.

    Fails when input or locator errors escape the agent, or sync browser work
    crosses threads. No existing test invokes this example through PydanticAI.
    Uses the real agent/tool and browser, with a deterministic model, no VM.
    """
    from playwright.async_api import async_playwright
    from pydantic_ai.messages import (
        ModelResponse,
        RetryPromptPart,
        TextPart,
        ToolCallPart,
        ToolReturnPart,
    )
    from pydantic_ai.models.function import FunctionModel

    path = Path(__file__).resolve().parents[2] / "examples/agent_tools/pydanticai_agent_browser.py"
    spec = importlib.util.spec_from_file_location("pydantic_browser_e2e", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    monkeypatch.setenv("OPENAI_API_KEY", "unused-local-model")
    attempted: list[dict[str, str]] = []
    retries: list[str] = []
    operations = [bad_operation, {"action": "click", "role": "button", "name": "Ready"}]

    def model(messages: list[ModelMessage], _info: AgentInfo) -> ModelResponse:
        if attempted:
            parts = messages[-1].parts
            if len(attempted) == 1:
                retry = next(
                    part
                    for part in parts
                    if isinstance(part, RetryPromptPart)
                    or (
                        isinstance(part, ToolReturnPart)
                        and getattr(part, "outcome", None) == "retried"
                    )
                )
                retries.append(str(retry.content))
        if len(attempted) == len(operations):
            return ModelResponse(parts=[TextPart("Recovered and clicked Ready")])
        operation = operations[len(attempted)]
        attempted.append(operation)
        return ModelResponse(parts=[ToolCallPart("browser_operation", operation)])

    agent = module._build_agent()
    async with async_playwright() as runtime:
        browser = await runtime.chromium.launch(
            executable_path=os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"), headless=True
        )
        try:
            page = await browser.new_page()
            await page.set_content("<button onclick=\"this.textContent='Clicked'\">Ready</button>")
            # A missing locator must not stall the agent for Playwright's 30s default.
            page.set_default_timeout(20_000)
            with agent.override(model=FunctionModel(model)):
                result = await agent.run(
                    "Exercise browser recovery", deps=module.BrowserCliDeps(page)
                )
            assert result.output == "Recovered and clicked Ready"
            assert await page.get_by_role("button", name="Clicked").count() == 1
            assert len(retries) == 1
            assert all("20000ms" not in retry for retry in retries)
            await page.close()
            with pytest.raises(RuntimeError, match="browser is closed"):
                await module.browser_operation(
                    type("Context", (), {"deps": module.BrowserCliDeps(page)})(), "observe"
                )
        finally:
            await browser.close()
            (tmp_path / "pydanticai-browser-recovery.json").write_text(
                json.dumps({"attempted": attempted, "retries": retries}, indent=2)
            )

# Browser agent examples

Give an agent a disposable browser to read websites, interact with pages, and save a screenshot. Celesto starts and stops the computer for each run.

## PydanticAI

Install the dependencies and check that Celesto can run on your machine:

```bash
pip install celesto pydantic-ai playwright
export OPENAI_API_KEY=...
celesto doctor
```

Run the news demo or supply a task:

```bash
python examples/agent_tools/pydanticai_agent_browser.py
python examples/agent_tools/pydanticai_agent_browser.py --input "Open https://example.com"
```

The agent can navigate, observe, click, fill, and scroll in the session's browser. The application owns the session and saves the final screenshot to `artifacts/pydanticai-agent-browser/final.png`. Page content and model output cannot select shell commands, browser connection addresses, or screenshot destinations.

## OpenAI computer use

Install `openai` alongside `celesto` and `playwright`, then run:

```bash
python examples/agent_tools/computer_use_browser.py \
  --start-url https://example.com \
  --task "Summarize the main heading."
```

Page requests are limited to the starting domain and any domains supplied with `--allowed-domain`. Add a domain explicitly when a site needs resources from another domain. Chromium makes the requests inside the sandbox; each redirect is checked before the browser follows it, and the address bar shows the final URL.

This example blocks new-tab navigations, embedded frames, workers, and outgoing WebSocket connections. These features create separate connections that the page policy cannot safely protect. Open the desired page directly with `--start-url` when a site relies on another tab or an embedded page.

HTML documents are limited to 8 MiB. The example reads each document through the browser connection to apply its worker and frame policy before scripts run; page HTTP requests remain inside the sandbox. Larger documents stop the task.

<div align="center">

# Celesto AI

## Give AI agents secure, persistent computers

![Celesto AI banner](./open-muse/banner-dark.png)

### [Try OpenMuse](./open-muse/README.md)

<p align="left">OpenMuse is an open-source computer coworker that can browse the web, use apps, and continue tasks after your laptop turns off. <strong>Celesto powers OpenMuse.</strong></p>

</div>

---

<div align="center">

<img src="https://ik.imagekit.io/gradsflow/celestoai/logo/celesto%20cover%20low_vFigbRaJI.png" alt="Celesto AI" />

[![CodeQL](https://github.com/CelestoAI/SmolVM/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/CelestoAI/SmolVM/actions/workflows/github-code-scanning/codeql)
[![Run Tests](https://github.com/CelestoAI/SmolVM/actions/workflows/pytest.yml/badge.svg)](https://github.com/CelestoAI/SmolVM/actions/workflows/pytest.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-orange.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-orange.svg)](https://www.python.org/downloads/)

[Quickstart](#quickstart) · [Runtime options](#choose-a-runtime) · [Examples](#examples) · [Security](#security) · [Performance](#performance) · [Docs](https://docs.celesto.ai) · [Discord](https://discord.gg/KNb5UkrAmm)

</div>

---

Celesto gives AI agents isolated computers for code, browsers, and desktop apps. Start a sandbox on your machine for development, then run the same workload in Celesto Cloud for remote or production use.

Each sandbox runs in its own virtual machine, starts in about 500 ms, and can preserve files and state across sessions. The VM boundary provides stronger isolation than a process-level container when an agent must run untrusted code.

## Quickstart

### 1. Install Celesto

For a local sandbox, install Celesto and prepare your machine:

```bash
curl -fsSL https://celesto.ai/install.sh | bash
```

For Celesto Cloud, install the Python package. Cloud sandboxes do not require local virtualization software:

```bash
pip install 'celesto==0.0.15a0'
```

<details>
<summary>Manual local setup</summary>

Install Celesto with Python 3.11 or newer, prepare the host, then check the setup:

```bash
pip install 'celesto==0.0.15a0'
celesto setup
celesto doctor
```

On macOS, setup uses Homebrew to install [QEMU](https://www.qemu.org/docs/master/system/i386/microvm.html). On Linux, setup may ask for `sudo`.

</details>

### 2. Run a local sandbox

`Computer` starts a local sandbox by default:

```python
from celesto import Computer

computer = Computer()
result = computer.run("echo 'Hello from Celesto!'")

print(result.stdout)
computer.stop()
```

### 3. Move the same code to Celesto Cloud

Set your API key:

```bash
export CELESTO_API_KEY="your-api-key"
```

Then change the provider:

```python
computer = Computer(provider="cloud")
```

| Provider | Best for | Host requirements |
| --- | --- | --- |
| Local | Development, tests, and private workloads on your machine | Local virtualization setup |
| Cloud | Remote tasks, persistent workspaces, and production workloads | Python package and `CELESTO_API_KEY` |

### Use the CLI

Create a local sandbox and run a command:

```bash
celesto sandbox create --name my-sandbox
celesto sandbox exec my-sandbox -- python --version
celesto sandbox stop my-sandbox
```

Use these commands for inspection or interactive access:

```bash
celesto sandbox list
celesto sandbox shell my-sandbox
celesto sandbox logs my-sandbox
```

Add `--follow` to stream logs. Use `celesto sandbox ssh my-sandbox` when you need an SSH session. See the [CLI reference](docs/reference/cli.md) for every command and shell completion.

## Choose a runtime

Celesto exposes one default API and focused APIs for browser and desktop work:

| Runtime | Use it when an agent needs | Python API | CLI |
| --- | --- | --- | --- |
| Shell sandbox | Commands, code, and files | `Computer()` | `celesto sandbox` |
| Browser | Chromium, CDP, screenshots, or a live viewer | `Celesto.browser()` | `celesto browser` |
| Linux computer | A full desktop and multiple GUI apps | `Celesto.computer()` | `celesto computer` |
| Windows sandbox | PowerShell or Windows software | `Celesto(os="windows", ...)` | `celesto sandbox create --os windows` |
| macOS desktop | App or installer tests on Apple Silicon | — | `celesto sandbox --os macos` |

Use `Computer` for the common command sandbox path. Use the `Celesto` factories for focused browser and desktop runtimes. Use `Celesto(...)` directly when you need low-level VM options such as the backend, communication channel, guest OS, mounts, or network policy.

## Core capabilities

| Capability | What it provides |
| --- | --- |
| Fast start | A ready microVM in about 500 ms, without an image pull on each start |
| VM isolation | A separate virtual machine for each sandbox |
| Local or cloud | The same `Computer` API across development and production |
| Persistent state | Files and state that survive across sessions |
| Host mounts | Read-only or writable access to selected local directories |
| Snapshots | Pause and restore memory, disk, and active processes |
| Network policy | Disable outbound access or allow specific IPv4 ranges on Linux with Firecracker |
| Multiple operating systems | Linux, Windows 11, and macOS preview support |

## Browser

Use a browser sandbox when an agent only needs Chromium. Celesto exposes a CDP endpoint for automation and, in visible mode, URLs for live view and screen control.

```python
from celesto import Celesto

with Celesto.browser(headless=False) as browser:
    print(browser.cdp_url)
    print(browser.viewer_url)
    print(browser.display_url)
```

- `cdp_url`: connect Playwright or another CDP client.
- `viewer_url`: watch the browser from another browser.
- `display_url`: connect a VNC client or computer-use agent.

Use `headless=True` when the agent only needs CDP. Start a visible browser from the CLI with:

```bash
celesto browser start --live
```

See [examples/browser_sandbox.py](examples/browser_sandbox.py) for a complete example.

## Linux computer

Use a Linux computer when an agent needs a visible desktop with more than a browser. The default image includes Chromium, a terminal, a file manager, and a text editor.

```python
from celesto import Celesto

with Celesto.computer() as computer:
    print(computer.display.viewer_url)
    print(computer.browser.cdp_url)

    computer.files.write("/workspace/task.txt", "Review this file")
    print(computer.run("ls -la /workspace").stdout)
```

The API groups screen access under `computer.display` and Chromium access under `computer.browser`. If Chromium closes while the desktop stays active, call `computer.browser.launch()`.

The first start builds the image locally and requires Docker. Later starts reuse the cached image.

```bash
celesto computer start --name assistant
celesto computer open assistant
celesto computer delete assistant
```

See the [Linux computer guide](docs/guides/computers.md) for Python and TypeScript examples.

## Windows sandbox

Use a Windows sandbox when an agent must run PowerShell or Windows software. Celesto can boot Windows 11 from a baseline image, upload files, set environment variables, and start multiple guests from the same image.

```python
from celesto import Celesto

with Celesto(
    os="windows",
    image="~/.smolvm/images/win11.qcow2",
    ssh_user="smolvm",
    ssh_password="smolvm",
) as vm:
    print(vm.run("Write-Output 'hello from windows'").stdout)
```

Create an image from a Windows ISO:

```bash
celesto windows build-image \
    --iso ./Win11.iso \
    --virtio-win-iso ./virtio-win.iso \
    --output ~/.smolvm/images/win11.qcow2
```

Windows guests require a Linux host with KVM. Host mounts, network controls, and snapshots remain Linux-only. See the [Windows guide](https://docs.celesto.ai/smolvm/guides/windows-guests) for image setup and guest requirements.

## macOS desktop preview

On an Apple Silicon Mac, Celesto can create a temporary macOS desktop for app and installer tests without changes to your main system.

Prepare the reusable local image:

```bash
celesto setup --macos
```

Create and open a desktop:

```bash
celesto sandbox create --os macos --name test-mac
celesto sandbox desktop test-mac
```

The first setup downloads macOS from Apple, requires about 50 GB, and takes 20–40 minutes. The image stays on the Mac that created it. Celesto supports at most two macOS guests at once. See the [macOS desktop guide](docs/guides/macos.md) for limits, shared folders, and cleanup.

## Common workflows

### Mount a host directory

Give a local sandbox access to an existing project without a copy step:

```bash
celesto sandbox create --name my-sandbox --mount ~/Projects/my-app
celesto sandbox shell my-sandbox
ls /workspace
```

Host mounts are read-only by default. The sandbox can read the source files, but writes under `/workspace` stay in the VM overlay and do not change the host copy.

Choose a guest path or mount multiple directories:

```bash
celesto sandbox create \
    --mount ~/Projects/my-app:/code \
    --mount ~/data:/mnt/data
```

Add `--writable-mounts` only when the sandbox must change the host files:

```bash
celesto sandbox create \
    --mount ~/Projects/my-app \
    --writable-mounts
```

The flag applies to every mount in that command. Do not combine a writable project directory with a directory that must remain unchanged.

The same option exists in Python:

```python
from celesto import Celesto

with Celesto(mounts=["~/Projects/my-app"], writable_mounts=True) as vm:
    vm.run("echo hello > /workspace/from-sandbox.txt")
```

### Upload one file

Copy a config, script, or small input into a live sandbox:

```bash
celesto sandbox file upload my-sandbox ./prompt.txt /tmp/prompt.txt
```

Or upload a file to a temporary sandbox from Python:

```python
from celesto import Celesto

with Celesto() as vm:
    vm.upload_file("./prompt.txt", "/tmp/prompt.txt")
```

The destination must be an absolute guest path. Celesto replaces any file that already exists at that path.

### Restrict network access

Sandboxes have internet access by default. On Linux with Firecracker, use `vsock` to keep command and file-transfer access while you disable outbound network access:

```python
from celesto import Celesto

with Celesto(
    backend="firecracker",
    comm_channel="vsock",
    internet_settings={"mode": "off"},
) as vm:
    print(vm.run("echo hello").stdout)
```

Use `mode="restricted"` with `allowed_cidrs` to allow specific IPv4 addresses or ranges. The restricted modes require private network mode and do not support host mounts or exposed ports. Explicit command output and file downloads still work when outbound access is off.

An `allowed_domains` list resolves domains during setup and permits the resulting IP addresses. It does not check the hostname on each connection. DNS servers do not receive automatic access. See the [network guide](docs/guides/networking.md) for supported combinations.

### Start a code agent

Run a supported code agent in its own sandbox so it can edit and execute code without direct access to your host environment:

```bash
celesto codex start
celesto claude start
celesto pi start
celesto hermes start
celesto opencode start
celesto openclaw start --name openclaw-work --no-attach
```

Open the private OpenClaw dashboard after the sandbox starts:

```bash
celesto openclaw open-ui openclaw-work
```

The first OpenClaw start can take several minutes while Celesto installs its supported Node.js runtime and pinned OpenClaw release. See the [agent presets guide](docs/guides/agent-presets.md) for credentials and dashboard access.

<a href="https://youtu.be/j1qyrTsI0Jw"><img src="https://img.youtube.com/vi/j1qyrTsI0Jw/maxresdefault.jpg" alt="Code agents in a Celesto sandbox" width="480" /></a>

## Examples

### Start here

| Goal | Example |
| --- | --- |
| Run code in a sandbox | [quickstart_sandbox.py](examples/quickstart_sandbox.py) |
| Start a browser sandbox | [browser_sandbox.py](examples/browser_sandbox.py) |
| Pass environment variables | [env_injection.py](examples/env_injection.py) |

### Agent framework integrations

| Framework or task | Example |
| --- | --- |
| OpenAI Agents | [openai_agents_tool.py](examples/agent_tools/openai_agents_tool.py) |
| LangChain | [langchain_tool.py](examples/agent_tools/langchain_tool.py) |
| PydanticAI shell tool | [pydanticai_tool.py](examples/agent_tools/pydanticai_tool.py) |
| PydanticAI sandbox across turns | [pydanticai_reusable_tool.py](examples/agent_tools/pydanticai_reusable_tool.py) |
| PydanticAI browser automation | [pydanticai_agent_browser.py](examples/agent_tools/pydanticai_agent_browser.py) |
| Computer use | [computer_use_browser.py](examples/agent_tools/computer_use_browser.py) |

Each example includes any extra package command it requires.

## Security

Each sandbox runs in its own virtual machine, which provides a stronger isolation boundary than process-level containers. Isolation still depends on secure host, hypervisor, image, credential, mount, and network configuration.

Celesto trusts a new local sandbox on its first connection to simplify development. Do not expose sandbox ports to the public internet without authentication and network controls. Treat writable mounts, forwarded credentials, and host-accessible services as explicit trust decisions.

See [SECURITY.md](SECURITY.md) for the security policy, threat model, and disclosure process.

## Performance

The benchmark suite measures cold start, time to interactive, pause and resume, and snapshot create and restore. It uses the public Python SDK with the native host backend: Firecracker on Linux and QEMU on macOS.

```bash
uv run python scripts/benchmarks/bench.py
```

See the [benchmark guide](scripts/benchmarks/README.md) for flags, output, and metric definitions.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) to set up a development environment and submit a change.

## License

Apache 2.0. See [LICENSE](LICENSE) for details.

---

<div align="center">

Built with 🧡 by [Celesto AI](https://celesto.ai)

</div>

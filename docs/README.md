# Celesto documentation

Celesto gives an AI agent a disposable computer for running code, using a browser, and doing work without changing your machine. Start with installation, then choose the workflow you need.

## Get started

- [Install Celesto](installation.md) — prepare your machine and check it is ready.
- [Glossary](../GLOSSARY.md) — the one word these docs use for each idea, such as computer, desktop, and browser session.
- [Run a computer](guides/sandboxes.md) — create, use, and remove an isolated computer.
- [CLI reference](reference/cli.md) — scan every current command and its purpose.
- [OpenMuse example](../open-muse/README.md) — chat with a Pi agent while watching its disposable browser.
- [OpenMuse Research example](../examples/open-muse-research/README.md) — run a structured TypeScript research workflow inside a temporary Celesto computer.
- [Agent tool examples](../examples/agent_tools/README.md) — connect an agent framework to a disposable computer.
- [TypeScript guide](typescript/index.md) — use Celesto from Node.js and browse the API reference.

## Guides

- [Run locally or in the cloud](local-first.md) — choose where computers run and migrate from cloud-first Python defaults.
- [Python cloud computers](python-cloud.md) — run commands, connect to browsers and screens, publish HTTP applications, and clean up resources.
- [Browser sessions](guides/browser.md) — run Chromium and connect with a browser or Playwright.
- [Computers with a desktop](guides/computers.md) — run a visible desktop with Chromium, a terminal, files, and a text editor.
- [Snapshots](guides/snapshots.md) — save and restore supported computer state.
- [Networking](guides/networking.md) — share a local port, limit outbound domains, or connect a computer to an existing bridge.
- [Secure local access](security.md) — use private control links, verify SSH identity, and prepare for security updates.
- [macOS desktops](guides/macos.md) — open a disposable Mac desktop on Apple Silicon.
- [Windows computers](guides/windows.md) — build and use a Windows image.

## Contributors

- [Architecture](contributing/architecture.md) — find the part of the codebase that owns a behavior.
- [Python SDK design and status](designs/celesto-sdk.md) — review the public `Computer` contract, implemented capabilities, and deferred work.
- [Local-first provider design](designs/local-first-providers.md) — review provider selection, lifecycle ownership, and implementation verification.
- [Public-egress release gate](deep-dive/public-egress-release-gate.md) — track the broader backend release target and remaining validation beyond current QEMU-only source support.
- [October 2026 security scan remediation](deep-dive/security-scan-2026-10.md) — trace the 35 findings to source changes and release requirements.
- [macOS runtime spike](contributing/macos-spike.md) — see verified behavior and release blockers for the desktop preview.
- [Native core](contributing/native-core.md) — work on the optional Rust acceleration package.

Pages link to the implementation and relevant tests when they make a claim about current behavior. Those links are evidence for maintainers, not prerequisites for using Celesto.

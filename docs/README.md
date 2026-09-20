# Celesto documentation

Celesto gives an AI agent a disposable computer for running code, using a browser, and doing work without changing your machine. Start with installation, then choose the workflow you need.

## Get started

- [Install Celesto](installation.md) — prepare your machine and check it is ready.
- [Run a sandbox](guides/sandboxes.md) — create, use, and remove an isolated computer.
- [CLI reference](reference/cli.md) — scan every current command and its purpose.
- [OpenMuse example](../open-muse/README.md) — chat with a Pi agent while watching its disposable browser.
- [OpenMuse Research example](../examples/open-muse-research/README.md) — run a structured TypeScript research workflow inside a temporary Celesto.

## Guides

- [Run locally or in the cloud](local-first.md) — choose where computers run and migrate from cloud-first Python defaults.
- [Python cloud computers](python-cloud.md) — run commands, connect to browsers and screens, publish HTTP applications, and clean up resources.
- [Agent presets](guides/agent-presets.md) — start Codex, Claude Code, Pi, Hermes, OpenClaw, or OpenCode in a sandbox.
- [OpenClaw dashboard](guides/agent-presets.md#open-openclaws-dashboard) — start OpenClaw, open its private dashboard, and safely replace an older sandbox.
- [Browser sandboxes](guides/browser.md) — run Chromium and connect with a browser or Playwright.
- [Linux computers](guides/computers.md) — run a visible desktop with Chromium, a terminal, files, and a text editor.
- [Snapshots](guides/snapshots.md) — save and restore supported sandbox state.
- [Networking](guides/networking.md) — share a local port, limit outbound domains, or connect a sandbox to an existing bridge.
- [macOS desktops](guides/macos.md) — open a disposable Mac desktop on Apple Silicon.
- [Windows guests](guides/windows.md) — build and use a Windows image.

## Contributors

- [Architecture](contributing/architecture.md) — find the part of the codebase that owns a behavior.
- [Python SDK design and status](designs/celesto-sdk.md) — review the public `Computer` contract, implemented capabilities, and deferred work.
- [Local-first provider design](designs/local-first-providers.md) — review provider selection, lifecycle ownership, and implementation verification.
- [Public-egress release gate](deep-dive/public-egress-release-gate.md) — verify both VM backends, browser routing, attack cases, and image pins before exposing public-only networking.
- [macOS runtime spike](contributing/macos-spike.md) — see verified behavior and release blockers for the desktop preview.
- [Native core](contributing/native-core.md) — work on the optional Rust acceleration package.

Pages link to the implementation and relevant tests when they make a claim about current behavior. Those links are evidence for maintainers, not prerequisites for using Celesto.

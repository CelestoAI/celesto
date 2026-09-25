# Changelog

## 0.1.2 — 2026-09-25

### Added

- Stop and resume the same cloud computer from Python, including after reconnecting.
- Control local CLI and SDK telemetry capture.

### Fixed

- Create cloud computers on compute pools by sending the required idempotency key.
- Wait for package publication before running the installer smoke check.

## 0.1.1 — 2026-09-23

### Added

- Choose a fixed execution location with `LocalComputer` or `CloudComputer`, while keeping the same computer API.
- Create local desktop computers with `celesto computer create` and open their terminals with `celesto computer terminal ID`. Use `--cloud` explicitly for cloud create, list, terminal, and delete operations.
- Connect automation tools to the browser and viewers to the screen of the same local or cloud `Computer` with `browser()` and `display()`. Display connections default to read-only; see [connection usage](docs/python-cloud.md#connect-to-the-browser-or-screen).

### Changed

- `Computer()` and `Computer.get(id)` now run locally by default. Cloud applications must use `provider="cloud"` or `CloudComputer`; explicit `local=True` and `local=False` remain supported. See the [migration guide](docs/local-first.md).

### Fixed

- Keep sandbox creation output clear when several SSH ports are busy; record one summary after choosing a free port.
- Find Homebrew's disk preparation tools automatically when growing sandbox disks on macOS.

## 0.0.15a0 — 2026-09-19

### Added

- Run commands on a local computer or Celesto Cloud with `from celesto import Computer`.
- Stream command output with `Computer.run_stream()`.
- Keep computers across Python sessions with `lifetime="persistent"` and reconnect with `Computer.get()`.

### Changed

- Publish the Python package as `celesto`. Install this alpha with `pip install 'celesto==0.0.15a0'`.
- Use `celesto` for all CLI commands, installation, updates, and shell completion.
- Use `CELESTO_RUNTIME` to override the local executable used by the TypeScript SDK.
- Update installation guides, examples, and release checks for the new package name.
- Rename the native package to `celesto-core`, the TypeScript package to
  `@celestoai/celesto`, and the guest agent to `celesto-guest-agent`.
- New state and configuration use `~/.celesto` and `CELESTO_*`; legacy
  `~/.smolvm` state and `SMOLVM_*` variables are read during the transition.

### Removed

- The `smolvm` executable alias and old Python import path. This is a breaking release.
- An obsolete OpenAI Agents example that depended on an unavailable integration.

Published images from before this release retain their SmolVM guest protocol and
should be rebuilt before using the renamed guest agent.

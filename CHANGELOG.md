# Changelog

## Unreleased

### Added

- Connect automation tools to the browser and viewers to the screen of the same local or cloud `Computer` with `browser()` and `display()`. Display connections default to read-only; see [connection usage](docs/python-cloud.md#connect-to-the-browser-or-screen).

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

### Removed

- The `smolvm` executable alias and old Python import path. This is a breaking release.
- An obsolete OpenAI Agents example that depended on an unavailable integration.

The native `smolvm-core` package and published VM images are unchanged. The separate
TypeScript preview package remains `@celestoai/smolvm`.

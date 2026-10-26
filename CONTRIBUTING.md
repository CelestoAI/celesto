# Contributing to Celesto

Thanks for your interest in contributing to Celesto.

Celesto is developed in the open at [CelestoAI/Celesto](https://github.com/CelestoAI/Celesto), and we welcome bug reports, fixes, tests, docs improvements, and feature work.

## Security First

If you think you found a security vulnerability, do not open a public issue.

Use GitHub private vulnerability reporting:

- https://github.com/CelestoAI/Celesto/security/advisories/new

For policy details, see [SECURITY.md](SECURITY.md).

## Ways to Contribute

- Report bugs with clear repro steps and environment details.
- Propose features through GitHub issues before large implementation work.
- Improve docs and examples.
- Submit code changes with tests.

## Development Setup

1. Fork and clone the repository.
1. Create a feature branch from `main`.
1. Install dependencies with `uv`.

```bash
uv sync --extra dev --extra dashboard --extra server
```

The test suite includes dashboard and local API checks, so development setup
includes their dependencies.

### Runtime Prerequisites (for backend/runtime work)

Runtime prerequisites vary by platform:

**Linux (Firecracker backend):**

Run the setup script to install Firecracker, configure KVM permissions, and validate host prerequisites:

```bash
uv run celesto setup
uv run celesto doctor
```

**macOS (QEMU backend):**

Just install QEMU via Homebrew; no additional setup is needed:

```bash
brew install qemu
uv run celesto doctor  # Verify QEMU and Hypervisor.framework
```

In both cases, `celesto doctor` is your validation step — it confirms that your machine is ready to run sandboxes.

**Note on setup scripts:** The repo-level shell scripts in `scripts/` remain the implementation detail behind `celesto setup`; use them directly only if you are intentionally working on the setup flow itself.

Health check:

```bash
uv run celesto doctor
uv run celesto doctor --json --strict
```

## Quality Checks

Run these before opening a PR:

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
uv run mypy src
```

Optional pre-commit setup:

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

The mypy hook uses the project environment, including the development, dashboard,
and server dependencies, so it checks the same library types used at runtime.
Development dependencies require mypy 2.3.1 or newer. TypeDoc owns the generated
files under `docs/typescript/api/`; regenerate them with `cd ts && npm run docs`
instead of formatting them with mdformat.

Notes:

- Type annotations are expected for new code (`mypy` runs in strict mode).
- Keep tests deterministic and avoid requiring privileged host setup unless the test explicitly targets runtime integration paths.

For the browser security checks, install Node.js 24, build the dashboard, and
install Chromium before running the tests:

```bash
npm ci --prefix ui
npm run build --prefix ui
uv run --with playwright --with websockets --with 'pydantic-ai-slim[openai]' python -m playwright install --with-deps chromium
uv run --with playwright --with websockets --with 'pydantic-ai-slim[openai]' pytest -m e2e tests/e2e/test_browser_examples_security.py tests/e2e/test_dashboard_browser_security.py tests/e2e/test_pydanticai_browser.py
```

Ordinary Linux E2E jobs build an unreleased Ubuntu candidate from a copy of a
SHA-verified published image, installing the current startup script and guest
agent. A temporary CI catalog entry serves that candidate on the runner's
loopback address through the normal image download and cache path. Each job
retains the compressed candidate, SHA-256 manifest, and source provenance for
three days. These runs do not validate a published image release; the explicit
`policy_release_validation` workflow mode continues to use published assets.

## Pull Request Guidelines

- Keep PRs focused and small enough to review.
- Include a clear description of what changed and why.
- Link related issues (for example: `Fixes #123`).
- Add or update tests for behavior changes.
- Update `README.md` or other docs when user-visible behavior changes.
- Ensure CI is green before requesting final review.

## Commit Style

- Use clear, imperative commit messages.
- Avoid mixing unrelated refactors with functional changes.

## Review and Merge

- Maintainers review PRs on a best-effort basis.
- A maintainer will merge after review and passing checks.
- Releases are handled by maintainers (tag-driven publish workflow).

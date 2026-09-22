# Celesto

Celesto gives AI agents disposable computers. Each sandbox is a lightweight
virtual machine that starts in seconds, can run code, browse the web, and
perform system-level tasks, then disappears without affecting the host.

## Development

### Commands

- Run tests: `pytest`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`

Tests live in `tests/`.

### Release checklist

For guest-agent or published-image changes:

1. Build and smoke-test the new image release.
2. Update `IMAGES_RELEASE_TAG` and the rootfs SHA pins in
   `src/celesto/images/published.py`.
3. Update `_GUEST_AGENT_RELEASE_SHA256` in
   `src/celesto/images/builder.py` using the
   `celesto-guest-agent-linux-<arch>.sha256` release assets. This pin is
   separate from the rootfs manifest.
4. Verify both installation paths:
   - `uv run celesto ...` from a source checkout may build or use the local
     guest-agent binary.
   - `celesto ...` installed with `uv tool` downloads the standalone
     guest-agent release binary.
5. Run the focused tests.
6. Only then tag the Celesto package release. Use either `v<version>` or
   `celesto-v<version>`; both formats publish the Python package and dashboard.

### CLI design

- New commands use `celesto <noun> <verb>`, such as `celesto codex start`.
- The noun identifies a resource, such as a sandbox, harness, or browser
  session. The verb identifies an action, such as `start`, `stop`, or `ssh`.
- Register each new resource as a top-level subcommand and place its actions
  beneath it. Do not overload a global verb.
- Do not add new top-level aliases without discussion. The existing aliases
  are:
  - `celesto prune`, which delegates to `celesto image prune`.
  - `celesto images`, which delegates to `celesto image list` and mirrors
    `docker images` for familiarity.
- `celesto completion <shell>` is an intentional top-level meta-command. It
  acts on the CLI itself, so the noun-verb rule does not apply.

## Writing

- Use progressive disclosure: begin with the essential information and add
  complexity only when the reader needs it.
- Lead with what the user can do and why it matters, not implementation
  details.
- Write the first paragraph of every page in plain English without jargon.
- Assume no prior knowledge. The reader may be a beginner engineer or a
  non-developer.
- Introduce only concepts the page needs. Explain technical terms immediately
  in simple language.
- Prefer short, concrete sentences over dense explanations.

### Errors and warnings

Treat every user-facing error or warning as product copy, including CLI output,
panels, JSON `error` payloads, and JSON `warnings` entries.

Each message must:

- State the fact in plain English. Avoid internal terms such as "mount",
  "host", "tap device", and "validator", even when they appear in flag names.
- Give the exact recovery command with the actual sandbox name, not a
  placeholder.
- Stay short. Prefer one sentence; use two only when necessary.
- Avoid state-dependent consequences you cannot guarantee. State the problem
  and recovery, then let the user judge the impact.
- Be self-contained. Do not put recovery guidance only in human output or a
  separate hint that JSON consumers will not receive.

Bad—uses internal vocabulary and gives no recovery path:

```text
workspace mount missing on host: /Users/aniket/conductor/workspaces/Celesto/lome
```

Bad—too long and incorrectly claims that a running sandbox cannot start:

```text
This sandbox was set up to share the folder '...' with you, but that
folder no longer exists on your machine. The sandbox cannot start
until you put the folder back, or delete the sandbox with
'celesto sandbox delete sbx-einstein'.
```

Good—short, always true, and actionable:

```text
Shared folder is missing on your machine:
'/Users/aniket/conductor/workspaces/Celesto/lome'. Restore it, or run
'celesto sandbox delete sbx-einstein' to remove the sandbox.
```

## Skill routing

Use the matching skill whenever a request fits one of these categories. When
in doubt, use the skill.

| Request | Skill |
| --- | --- |
| Product ideas or brainstorming | `/office-hours` |
| Strategy or scope | `/plan-ceo-review` |
| Architecture | `/plan-eng-review` |
| Design system or plan review | `/design-consultation` or `/plan-design-review` |
| Full review pipeline | `/autoplan` |
| Bugs or errors | `/investigate` |
| Site behavior QA or testing | `/qa` or `/qa-only` |
| Code or diff review | `/review` |
| Visual polish | `/design-review` |
| Ship, deploy, or pull request | `/ship` or `/land-and-deploy` |
| Save progress | `/context-save` |
| Resume context | `/context-restore` |
| Backlog-ready specification or issue | `/spec` |

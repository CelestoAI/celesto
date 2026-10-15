# Start an AI coding agent

An agent preset starts a fresh computer, installs one coding agent, and can carry over the credentials and small configuration files that agent needs. It is the quickest way to give an agent a disposable place to work.

## Start an agent

For example, start Codex:

```bash
celesto codex start --name codex-work
```

Other available presets use the same pattern:

```bash
celesto claude start --name claude-work
celesto pi start --name pi-work
celesto hermes start --name hermes-work
celesto openclaw start --name openclaw-work
celesto opencode start --name opencode-work
```

Each command accepts computer options such as `--mount`, `--memory`, and `--disk-size`. Add `--no-attach` if you want to start the computer without opening the agent session.

## Open OpenClaw's dashboard

Celesto installs OpenClaw 2026.9.1 with a supported Node.js 24 runtime. Start it without attaching to the terminal:

For this release, creating a new OpenClaw computer can take several minutes because Celesto installs Node.js and OpenClaw after the computer starts. The command shows each installation step while you wait. A future published image will restore the faster prebuilt path.

```bash
celesto openclaw start --name openclaw-work --no-attach
```

List running computers when you need to find its name:

```bash
celesto openclaw list
# NAME              STATUS   PID
# openclaw-work     running  12345
```

This command shows running OpenClaw computers. Add `--all` to include every state, or `--status STATUS` to choose one state.

Use the generic preset filter when you are working with your full list of computers:

```bash
celesto computer list --preset openclaw
# NAME              PRESET     STATUS   PID
# openclaw-work     openclaw   running  12345
```

Computers created by older Celesto releases do not appear in either filtered list. Manually prepared computers are also excluded. Both remain available through `celesto computer list --all`, where the Preset column shows `-`.

Then open its private dashboard through a localhost-only connection:

```bash
celesto openclaw open-ui openclaw-work
```

Celesto starts the OpenClaw gateway if needed, creates a local port forward, and opens the one-time dashboard link in your browser. If you are working on a remote or headless machine, print the link instead:

```bash
celesto openclaw open-ui openclaw-work --no-browser
```

Close the local connection with the exact command printed by `openclaw open-ui`. You can also list active connections with `celesto computer port list openclaw-work`.

OpenClaw currently supports Ubuntu computers in Celesto.

## Replace an older OpenClaw computer

Updating Celesto changes newly created computers, but it does not replace OpenClaw inside an existing computer. Save the old computer before deleting it so you can recover files that were not stored on your machine:

```bash
celesto computer snapshot create openclaw-work --snapshot-id openclaw-work-before-openclaw-upgrade
# Created snapshot 'openclaw-work-before-openclaw-upgrade' from computer 'openclaw-work'.
```

Delete the old computer after the snapshot succeeds:

```bash
celesto computer delete openclaw-work
```

Then create a fresh computer with the version pinned by your installed Celesto release:

```bash
celesto openclaw start --name openclaw-work --no-attach
```

If you need the old computer again, delete its replacement and restore the saved snapshot with `celesto computer snapshot restore openclaw-work-before-openclaw-upgrade`.

## Credentials and configuration

Set the provider key in your shell on your machine before starting the preset. For example:

```bash
export OPENAI_API_KEY=your-key
celesto codex start --name codex-work
```

OpenCode supports multiple providers. You can forward common provider keys such as `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `GEMINI_API_KEY`, and `OPENROUTER_API_KEY`, or authenticate from inside the computer with `opencode auth login`.

Presets copy only the configuration they need where possible. Review what you put in configuration folders on your machine before starting a computer, especially when they contain credentials.

OpenClaw is an exception: every new OpenClaw computer starts with a fresh configuration. Celesto does not copy `~/.openclaw/openclaw.json`, `~/.openclaw/.env`, or any other OpenClaw state from your machine. It forwards `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `OPENCLAW_GATEWAY_TOKEN`, and `OPENCLAW_GATEWAY_PASSWORD` only when those variables are set in the shell that starts Celesto.

Run onboarding inside the computer when you need configuration beyond those credentials:

```bash
celesto computer shell openclaw-work
openclaw onboard
```

## Implementation notes

The command registry is in [`src/celesto/presets/__init__.py`](../../src/celesto/presets/__init__.py). Each preset declares its installer, forwarded environment variables, and copied files: [Codex](../../src/celesto/presets/codex.py), [Claude Code](../../src/celesto/presets/claude_code.py), [Pi](../../src/celesto/presets/pi.py), [Hermes](../../src/celesto/presets/hermes.py), [OpenClaw](../../src/celesto/presets/openclaw.py), and [OpenCode](../../src/celesto/presets/opencode.py). Preset behavior is covered in [`tests/presets/test_presets.py`](../../tests/presets/test_presets.py).

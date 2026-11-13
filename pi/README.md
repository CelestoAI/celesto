# Celesto for Pi

Run Pi's coding tools away from your laptop while keeping its interface and
conversation history local. A Celesto computer is an isolated remote computer
that holds your project and runs the tools. Model credentials are the secrets
Pi uses to access an AI model. The extension does not forward Pi’s model authentication.

This package is maintained in the [Celesto repository](https://github.com/CelestoAI/celesto/tree/main/pi). See the [Cloud guide](https://github.com/CelestoAI/celesto/blob/main/docs/python-cloud.md) for Celesto authentication and computer lifecycle details.

## Quickstart

Before starting, install [Pi](https://github.com/earendil-works/pi) and
configure it with a model provider. You also need Node.js 22.19 or newer and a
Celesto API key.

Install the extension:

```bash
pi install npm:@celestoai/pi
```

Sign in once with the Celesto CLI:

```bash
pip install celesto
celesto auth login
```

Alternatively, export `CELESTO_API_KEY` or add it to the project's local `.env` file:

```bash .env
CELESTO_API_KEY="your-celesto-api-key"
```

The extension checks the shell environment first, then `.env`, then credentials saved by `celesto auth login` in `~/.celesto/credentials`. A saved login retains its configured Cloud API origin.

From the project you want to work on, start Pi:

```bash
pi --celesto
```

The extension creates an empty `$HOME/workspace` on a Celesto computer and
runs Pi's `read`, `write`, `edit`, and `bash` tools there. Computers created by
the extension use a persistent home, so `$HOME` survives stop and restore. The
extension does not copy anything from your machine automatically.

## Copy a project explicitly

From inside Pi, copy the current local project to the Celesto workspace:

```text
/celesto push
```

This explicit command replaces the remote workspace. It refuses to copy your filesystem root or home directory. Start Pi from a project directory before running it.

After pushing, copy changes in either direction explicitly:

```text
/celesto sync
```

The sync command preserves independently changed files under `.celesto-conflicts/` instead of overwriting local work. Local sync requires hard-link support; unsupported filesystems report an error before moving an existing file. Push and sync wait for earlier remote `bash`, `write`, and `edit` operations to finish, and those tools wait while a transfer runs. Pi never syncs files automatically when it exits.

Sync coordinates Pi's own tools. Other programs that replace workspace directories while sync runs can redirect its shell operations outside the workspace. Pause those programs before syncing. The path checks and writes are separate operations.

## Check the computer

```text
/celesto status
```

This shows the computer name, workspace, cleanup behavior, and current sync revision.

## Keep the computer

When you quit Pi, the extension deletes the active session's computer if it created that computer and you have not marked it to keep. It does not sync automatically. Run `/celesto sync` first if you want local copies of remote changes. Keep the active computer for later use with:

```text
/celesto keep
```

The command prints the exact `celesto computer delete <id> --cloud` command to use when you no longer need it.

Starting a new session, resuming another session, forking, or reloading preserves the previous session's computer and saved workspace metadata. Computers belonging to inactive sessions remain available. Resume a session and quit Pi to apply that session's saved cleanup setting, or delete its computer explicitly with `celesto computer delete <id> --cloud`. Quitting Pi does not clean up every inactive session's computer.

## Reuse an existing computer

Get a computer name from `celesto computer create --cloud` or `celesto computer list --cloud`, then pass it to Pi:

```bash
pi --celesto --celesto-computer curie
```

The extension never deletes caller-owned computers. If this Pi session originally created the selected computer, its saved cleanup setting still applies. Existing files in `$HOME/workspace` remain untouched unless you explicitly run `/celesto push` or `/celesto sync`. A non-empty legacy `/workspace` is moved into `$HOME/workspace` automatically when the home workspace is empty.

## Files excluded from explicit transfers

For `/celesto push` and `/celesto sync`, the extension reads `.gitignore` and then applies `.celestoignore` overrides. It also excludes common secrets, dependency directories, build output, files larger than 25 MB, and symbolic links. Sync downloads also skip hard links. `.git` remains available so Pi can inspect branches and diffs.

Add project-specific patterns to `.celestoignore`:

```gitignore
fixtures/private/
*.large-test-data
```

The extension does not automatically forward its authentication credentials or model-provider credentials. `CELESTO_API_KEY` is used locally to contact Celesto Cloud. Explicit transfers use overridable filename filters: `.gitignore` or `.celestoignore` negations can include files such as `.env`, so review those rules before pushing secrets.

## Command output

Cloud command output is buffered until completion. The extension uses the current `/exec` API, and explicit transfers use chunks that fit its 10,000-character command limit. Pi cancellation also requests termination of the remote process group.

## Development

From this repository, run `npm ci` and `npm run check` inside `pi/`. The tests use isolated HTTP and filesystem fixtures. Set `PI_TEST_ARTIFACT_DIR` to an absolute directory to retain the HTTP transcript.

## Current scope

This first version uses compressed archives and base64 file transfer for explicit push and sync commands. It intentionally does not override Pi's `grep`, `find`, or `ls` tools yet. Native workspace transfer requires future Celesto backend support.

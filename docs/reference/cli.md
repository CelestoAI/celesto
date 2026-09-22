# CLI reference

The CLI creates and manages disposable sandboxes. Run `celesto COMMAND --help` for the current options on your installed version; this page helps you choose the right command.

## Prepare the host

| Command | Use it to |
| --- | --- |
| `celesto setup` | Install or check local runtime dependencies. Add `--macos` to prepare the macOS desktop runtime. |
| `celesto doctor` | Check whether this machine can run sandboxes. Use `--backend vz` to check macOS desktop support. |
| `celesto bridge check BRIDGE` | Check an existing Linux bridge before connecting a sandbox to it. |
| `celesto update` | Upgrade to the latest stable release. |
| `celesto prune` | Remove stale cached images (alias for `celesto image prune`). |

On Linux, `celesto setup` stores Firecracker—the program that starts a sandbox—in `~/.celesto/bin`. Use `--firecracker-dir` to choose another folder for one setup run:

```bash
celesto setup --firecracker-dir "$HOME/.local/bin"
```

Set `CELESTO_FIRECRACKER_DIR` when future commands also need to find a folder that is not on `PATH`. See [Install Celesto](../installation.md) for Fedora Atomic and build-machine setup.

## Work with sandboxes

Run these in the order you need them:

| Command | Use it to |
| --- | --- |
| `celesto sandbox create` | Create a sandbox. Add `--network bridge --bridge BRIDGE` only when the sandbox should appear as a separate computer on that network. |
| `celesto sandbox list` / `info` | Find or inspect sandboxes. Add `--preset PRESET` to list sandboxes created by one agent preset. |
| `celesto sandbox shell` / `ssh` | Open a shell. `shell` uses Celesto's fast control channel when available; `ssh` explicitly uses SSH. |
| `celesto sandbox desktop` | Open a running macOS sandbox in Screen Sharing. Add `--start` to start it first. |
| `celesto sandbox exec` | Run one command inside a running sandbox and print its output — handy for scripts and agents. Put the command after `--`, e.g. `celesto sandbox exec my-sandbox -- ls -la`. Add `--start` to start the sandbox first if it isn't running. |
| `celesto sandbox logs` | Show a sandbox's boot and console logs. Add `--follow` to keep printing new lines. |
| `celesto sandbox start` / `stop` | Start or stop a sandbox. |
| `celesto sandbox pause` / `resume` | Temporarily freeze and continue a running sandbox. |
| `celesto sandbox delete` | Remove one or more sandboxes. |
| `celesto sandbox prune` | Delete disks and logs left behind by sandboxes that no longer exist. Add `--dry-run` to list those files without deleting them. Disks you asked Celesto to save are kept unless you add `--include-saved`. |

### Sandbox data and connections

| Command | Use it to |
| --- | --- |
| `celesto sandbox file upload` / `download` | Copy a file in or out. |
| `celesto sandbox env set` / `unset` / `list` | Manage persistent environment variables. |
| `celesto sandbox port expose` / `close` / `list` | Manage local port forwarding. |
| `celesto sandbox snapshot create` / `restore` / `list` / `delete` | Save and restore supported sandbox state. |

## Start a prepared agent

`celesto codex start`, `celesto claude start`, `celesto pi start`, `celesto hermes start`, `celesto openclaw start`, and `celesto opencode start` each create a sandbox and install that agent.

- Create and install OpenClaw with `celesto openclaw start`.
- Find an OpenClaw sandbox with `celesto openclaw list`, or use the generic `celesto sandbox list --preset openclaw`. Add `--all` to include every state or `--status STATUS` to choose one state.
- Open the dashboard with `celesto openclaw open-ui SANDBOX`. It starts or reuses the gateway and connects it over localhost only. Add `--host-port PORT` to choose the dashboard's local port, `--no-browser` to print the one-time link, or `--json` for structured output.
- Sandboxes created by older Celesto releases and manually prepared sandboxes remain visible through `celesto sandbox list --all`, but they do not appear in filtered results.
- The current OpenClaw fallback installation can take several minutes. See [Agent presets](../guides/agent-presets.md#open-openclaws-dashboard) for the complete workflow and safe upgrade steps.

## Manage downloaded images

The first time you start a sandbox or agent, Celesto downloads the files it boots from and keeps them on disk so later starts are fast. These commands manage that storage, and they work like Docker's image commands if you know those:

| Command | Use it to |
| --- | --- |
| `celesto image pull <preset>` | Download an image ahead of time, for example before going offline. |
| `celesto image pull --all` | Download every image available for this machine in one go. |
| `celesto images` (or `image list` / `image ls`) | See which images are downloaded, when, and how much space they use. |
| `celesto image inspect <name>` | See one image in detail: files, checksums, and where it came from. |
| `celesto image build -t NAME .` | Build a custom image from a Dockerfile (needs Docker installed). |
| `celesto image build --os macos --ipsw latest -t NAME` | Prepare a reusable macOS image locally from an Apple restore file. |
| `celesto image save <name> -o FILE` / `image load -i FILE` | Copy an image to a machine without internet access. |
| `celesto image rm <name>` | Remove a downloaded image to free disk space. |
| `celesto image prune` | Remove images left behind by older Celesto versions. |

Images are stored in `~/.celesto/images`. To keep them somewhere else, set the `CELESTO_IMAGE_DIR` environment variable — sandboxes read it too, so images you pull are found when a sandbox starts. The `--image-dir` option points a single `celesto image` command at a different folder; sandboxes do not read that folder.

## Browsers, computers, local services, and Windows

| Command | Use it to |
| --- | --- |
| `celesto browser start` / `open` / `list` / `logs` / `stop` | Manage browser sandboxes. |
| `celesto computer create` | Create and start a local desktop computer; add `--cloud` to run in Celesto Cloud. |
| `celesto computer terminal COMPUTER_ID` | Open an interactive terminal using the ID printed by `create` or `list`; add `--cloud` for a cloud computer. Exiting keeps the computer. |
| `celesto computer start` / `open` / `list` / `logs` / `delete` | Manage complete Linux desktop computers. |
| `celesto computer templates` | List the available desktop templates. |
| `celesto ui` | Start the local dashboard. |
| `celesto server start` | Start the local HTTP API. |
| `celesto windows build-image` | Build a Windows qcow2 image. |

Computer commands select local execution by default; `--local` makes that choice explicit.
Use `--cloud` for cloud `create`, `list`, `terminal`, and `delete` commands; it cannot be combined with `--local`.
The existing `start`, `open`, `logs`, and `templates` commands remain local-only.
See [Run locally or in the cloud](../local-first.md) for setup, examples, and current cloud limits.

## Shell completion

Turn on tab completion so your shell can finish `celesto` commands, options, and the names of your existing sandboxes as you type. One command sets it up:

```bash
celesto completion bash --install   # also works with: zsh, fish
```

Open a new shell afterward, then type `celesto sandbox ssh` followed by a space and press Tab to complete a sandbox name.

Prefer to wire it up yourself? Run the same command without `--install` to print the script, then load it your own way:

```bash
# bash — add to ~/.bashrc
eval "$(celesto completion bash)"

# zsh — add to ~/.zshrc
eval "$(celesto completion zsh)"

# fish — create the folder once, then write the completion file
mkdir -p ~/.config/fish/completions
celesto completion fish > ~/.config/fish/completions/celesto.fish
```

## Common options

`--json` is available on commands that return structured output. `--backend` selects `auto`, `firecracker`, `qemu`, `libkrun`, or `vz` where the command supports that runtime. The `vz` choice is only for macOS guests on Apple Silicon. `--boot-timeout` controls how long an operation waits for a ready sandbox.

**Implementation notes:** the command definitions are the source of truth in [`src/celesto/cli/commands/app.py`](../../src/celesto/cli/commands/app.py), including available flags and help text. The CLI command surface is tested by [`tests/cli/test_cli.py`](../../tests/cli/test_cli.py).

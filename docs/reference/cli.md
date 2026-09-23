# CLI reference

The CLI creates and manages disposable computers. Run `celesto COMMAND --help` for the current options on your installed version; this page helps you choose the right command. `celesto sandbox` is an equivalent spelling for every `celesto computer` subcommand.

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

## Work with computers

Run these in the order you need them:

| Command | Use it to |
| --- | --- |
| `celesto computer create` | Create a minimal local computer. Add `--desktop` for a Linux desktop, `--os macos` or `--os windows` for another guest system, or `--cloud` for Celesto Cloud. Add `--network bridge --bridge BRIDGE` when a local computer should appear on an existing network bridge. |
| `celesto computer list` / `info` | Find or inspect local computers. Add `--desktop` to list managed Linux desktops, `--cloud` for cloud computers, or `--preset PRESET` for computers created by one agent preset. |
| `celesto computer shell` / `ssh` | Open a shell. `shell` uses Celesto's fast control channel when available; `ssh` explicitly uses SSH. |
| `celesto computer desktop` | Open a running macOS sandbox in Screen Sharing. Add `--start` to start it first. |
| `celesto computer exec` | Run one command and return its exit code. Put the command after `--`, e.g. `celesto computer exec demo -- ls -la`. Add `--start` to start a stopped local computer first, `--desktop` for a managed Linux desktop ID, or `--cloud` for a cloud computer. |
| `celesto computer logs` | Show a sandbox's boot and console logs. Add `--follow` to keep printing new lines. |
| `celesto computer start` / `stop` | Start or stop a sandbox. |
| `celesto computer pause` / `resume` | Temporarily freeze and continue a running sandbox. |
| `celesto computer delete` | Remove one or more local computers. Add `--desktop` for a managed Linux desktop ID, or `--cloud` for a cloud computer. |
| `celesto computer prune` | Delete disks and logs left behind by sandboxes that no longer exist. Add `--dry-run` to list those files without deleting them. Disks you asked Celesto to save are kept unless you add `--include-saved`. |

### Computer data and connections

| Command | Use it to |
| --- | --- |
| `celesto computer file upload` / `download` | Copy a file in or out. |
| `celesto computer env set` / `unset` / `list` | Manage persistent environment variables. |
| `celesto computer port expose` / `close` / `list` | Manage local port forwarding. |
| `celesto computer snapshot create` / `restore` / `list` / `delete` | Save and restore supported sandbox state. |

## Start a prepared agent

`celesto codex start`, `celesto claude start`, `celesto pi start`, `celesto hermes start`, `celesto openclaw start`, and `celesto opencode start` each create a sandbox and install that agent.

- Create and install OpenClaw with `celesto openclaw start`.
- Find an OpenClaw sandbox with `celesto openclaw list`, or use the generic `celesto computer list --preset openclaw`. Add `--all` to include every state or `--status STATUS` to choose one state.
- Open the dashboard with `celesto openclaw open-ui SANDBOX`. It starts or reuses the gateway and connects it over localhost only. Add `--host-port PORT` to choose the dashboard's local port, `--no-browser` to print the one-time link, or `--json` for structured output.
- Sandboxes created by older Celesto releases and manually prepared sandboxes remain visible through `celesto computer list --all`, but they do not appear in filtered results.
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

## Desktops, cloud computers, browsers, and services

| Command | Use it to |
| --- | --- |
| `celesto browser start` / `open` / `list` / `logs` / `stop` | Manage browser sandboxes. |
| `celesto auth login` | Save a cloud API key for later `--cloud` commands. |
| `celesto computer create --desktop --name NAME` | Start a local Linux desktop with a viewer and Chromium. |
| `celesto computer list --desktop` / `open NAME` / `delete NAME --desktop` | Find, open, or delete that desktop by its desktop ID. |
| `celesto computer create --cloud` / `list --cloud` / `info ID --cloud` | Create, find, or inspect cloud computers. |
| `celesto computer start ID --cloud` / `stop ID --cloud` | Resume or stop a cloud computer. Without `--cloud`, `start` and `stop` act on local computers. |
| `celesto computer port publish` / `unpublish` | Publish or unpublish a cloud computer's port on a public URL. Local `port expose` only forwards to your machine. |
| `celesto computer templates` | List the available desktop templates. |
| `celesto ui` | Start the local dashboard. |
| `celesto server start` | Start the local HTTP API. |
| `celesto windows build-image` | Build a Windows qcow2 image. |

Computer commands select local execution by default; `--local` makes that choice explicit.
Use `--cloud` for cloud `create`, `list`, `info`, `start`, `stop`, `ssh`, `exec`, and `delete` commands; it cannot be combined with `--local`.
Cloud `list` requests at most 50 computers by default; add `--limit NUMBER` to request more. If the response fills the limit, Celesto warns that more computers may exist, and JSON output sets `possibly_truncated` to `true`.
The existing `open`, `logs`, and `templates` commands remain local-only.
See [Run locally or in the cloud](../local-first.md) for setup, examples, and current cloud limits.

## Shell completion

Turn on tab completion so your shell can finish `celesto` commands, options, and the names of your existing sandboxes as you type. One command sets it up:

```bash
celesto completion bash --install   # also works with: zsh, fish
```

Open a new shell afterward, then type `celesto computer ssh` followed by a space and press Tab to complete a sandbox name.

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

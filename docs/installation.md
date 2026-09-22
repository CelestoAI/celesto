# Install Celesto

Install Celesto and the tools your machine needs to run sandboxes, then check that everything is ready.

## Recommended: one-command installation

On Linux or macOS, run:

```bash
curl -fsSL https://celesto.ai/install.sh | bash
```

The URL redirects to the [installer on GitHub](https://github.com/CelestoAI/Celesto/blob/main/scripts/install.sh).
It installs `uv` if needed, uses it to install the Celesto CLI with server support
in a separate Python environment, runs `celesto setup`, then runs `celesto doctor`.
Running it again upgrades the existing Celesto uv tool installation.

- **macOS:** install [Homebrew](https://brew.sh) first. Setup installs QEMU, the program that runs Linux sandboxes on your Mac.
- **Linux:** enable KVM (hardware virtualization) first. Setup installs Firecracker and missing system packages, and configures runtime permissions. It may ask for `sudo`. Package installation supports apt and dnf; see the Fedora Atomic notes below for systems that require a reboot.

If your terminal cannot find `celesto` afterward, run `uv tool update-shell` and
restart your terminal. If `uv` is also missing from your terminal's search path,
restart the terminal first after its installation.

Docker is optional. To include it:

```bash
curl -fsSL https://celesto.ai/install.sh | bash -s -- --with-docker
```

If you have already installed the system packages, skip package installation:

```bash
curl -fsSL https://celesto.ai/install.sh | bash -s -- --skip-deps
```

This still installs the CLI and configures the machine; on Linux it also downloads
Firecracker if missing. It is not a dry run. To only inspect an existing
installation, run `celesto setup --check-only` and `celesto doctor`.

The CLI's separate environment does not make `import celesto` available in your
Python projects. Install the package in each project that uses the Python API,
as shown below; machine setup only needs to be done once.

## Manual installation with pip

Use Python 3.11 or newer in your project's environment:

```bash
pip install 'celesto==0.0.15a0'
```

Pip installs Python packages only. If you have not used the one-command installer,
complete the machine setup below as well. For TypeScript or local server use,
install `celesto[server]==0.0.15a0` instead.

The Python package is now named `celesto`, and Python code imports from `celesto`
(for example, `from celesto import Computer`). The retired `smolvm` Python import
and command are not installed by this release.

The native helper is named `celesto-core`. It is installed automatically on
supported Linux and macOS systems; most users do not need Rust installed.

### Upgrade from SmolVM

New Celesto installations write configuration under `~/.celesto` and use
`CELESTO_*` environment variables. Existing `~/.smolvm` image, runtime, and
state directories are read when no Celesto directory exists, so upgrade before
deleting the old directory. `SMOLVM_*` variables continue to work temporarily,
but replace each with its `CELESTO_*` equivalent before the next major release.

## Prepare your machine

On macOS, install [Homebrew](https://brew.sh) first. Setup installs QEMU if missing:

```bash
celesto setup
celesto doctor
```

On Linux, `setup` installs or checks the runtime dependencies and configures what Celesto needs to run sandboxes. It may ask for administrator permission.

```bash
celesto setup
celesto doctor
```

`celesto doctor` reports problems and their recovery steps. Add `--strict` when a warning should fail an automated check.

### Choose where Firecracker is stored

On Linux, Firecracker is the program that starts a sandbox. Celesto stores it in `~/.celesto/bin` by default, which works without changing system folders.

Choose another folder for one setup run with:

```bash
celesto setup --firecracker-dir "$HOME/.local/bin"
```

If that folder is not already on `PATH`, set it for future Celesto commands:

```bash
export CELESTO_FIRECRACKER_DIR="$HOME/.local/bin"
celesto setup
```

This setting changes only the Firecracker location. Images still use `CELESTO_IMAGE_DIR`, and sandbox state still uses `CELESTO_DATA_DIR`.

### Fedora Atomic desktops

Silverblue, Bluefin, and other Fedora Atomic systems can use the normal setup command when the required host tools are already installed. Celesto does not change the rpm-ostree deployment automatically. If a tool is missing, setup prints the exact `rpm-ostree` command and asks you to reboot before retrying.

### Prepare macOS desktop support

Apple Silicon Mac users can install the separate local desktop runtime:

```bash
celesto setup --macos
celesto doctor --backend vz
```

This is only needed for macOS guests. Linux guests on a Mac continue to use QEMU.

## Build-machine setup

Use this only when preparing a reusable machine image on a builder that cannot run virtualization itself:

```bash
celesto setup --for-bake --runtime-user ubuntu
```

After booting that image on the real runtime machine, run `celesto doctor` before accepting work.

## What Celesto selects automatically

When you do not choose a backend, Celesto picks the best one that is actually installed on your machine. It prefers Firecracker on Linux and QEMU on macOS, but if that one is missing it falls back to another installed backend, so it never picks something your machine cannot run. If nothing suitable is installed, `celesto sandbox create` stops right away and tells you what to install — before downloading anything. You can inspect a specific choice with `celesto doctor --backend qemu` or `celesto doctor --backend firecracker`.

**Implementation notes:** supported setup platforms and packaged setup scripts are defined in [`src/celesto/host/setup.py`](../src/celesto/host/setup.py); backend selection is in [`src/celesto/runtime/backends.py`](../src/celesto/runtime/backends.py) and is covered by [`tests/host/test_setup.py`](../tests/host/test_setup.py) and [`tests/test_backends.py`](../tests/test_backends.py).

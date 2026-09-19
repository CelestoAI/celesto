# Install Celesto

Install Celesto, prepare the machine that will run sandboxes, and confirm that it is ready. You need Python 3.11 or newer; supported host setup is Linux and macOS.

## Install the package

Install the alpha release explicitly:

```bash
pip install 'celesto==0.0.15a0'
```

The Python package is now named `celesto`, and Python code imports from `celesto`
(for example, `from celesto import Computer`). Old `smolvm` Python imports are no
longer supported. Use the `celesto` command; the `smolvm` command is no longer
installed.

The `smolvm-core` package name is unchanged. It is installed automatically on
supported Linux and macOS systems; most users do not need Rust installed.

## Prepare your machine

On macOS, install QEMU first, then let Celesto check the rest of the setup:

```bash
brew install qemu
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

On Linux, Firecracker is the program that starts a sandbox. Celesto stores it in `~/.smolvm/bin` by default, which works without changing system folders.

Choose another folder for one setup run with:

```bash
celesto setup --firecracker-dir "$HOME/.local/bin"
```

If that folder is not already on `PATH`, set it for future Celesto commands:

```bash
export SMOLVM_FIRECRACKER_DIR="$HOME/.local/bin"
celesto setup
```

This setting changes only the Firecracker location. Images still use `SMOLVM_IMAGE_DIR`, and sandbox state still uses `SMOLVM_DATA_DIR`.

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

**Implementation notes:** supported setup platforms and packaged setup scripts are defined in [`src/celesto/host/setup.py`](../src/celesto/host/setup.py); backend selection is in [`src/celesto/runtime/backends.py`](../src/celesto/runtime/backends.py) and is covered by [`tests/test_setup.py`](../tests/test_setup.py) and [`tests/test_backends.py`](../tests/test_backends.py).

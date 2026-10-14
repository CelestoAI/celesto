# macOS computers

A macOS computer gives you a temporary Mac desktop in a window for opening apps, testing installers, and working with files without changing your everyday system. This preview runs locally on an Apple Silicon Mac.

## Prepare your Mac

Install the tested desktop runtime and check that it is ready:

```bash
celesto setup --macos
celesto doctor --backend vz
```

You need an Apple Silicon Mac running macOS 14 or newer. The image folder must be on an APFS volume, the normal file system used by modern Macs.

## Create and open a desktop

The first macOS computer prepares macOS from an Apple restore file. Celesto asks before downloading it because preparation needs about 50 GB of free space and can take 20–40 minutes. A progress bar follows the download, macOS installation, and desktop setup phases. If installation fails after the download finishes, the next attempt reuses that restore file instead of downloading it again.

```bash
celesto computer create --os macos --name test-mac
# Next: celesto sandbox desktop test-mac
```

Open the desktop:

```bash
celesto computer desktop test-mac
```

Celesto opens the built-in Screen Sharing app. The connection stays on your Mac and uses a temporary password that is not printed.

## Copy and paste

Copy and paste works in both directions between your Mac and the computer's desktop. Copy on one side, paste on the other.

Anything you copy on your Mac is readable inside the computer while it runs. If you would rather keep the two clipboards separate, turn it off when you create the computer:

```bash
celesto computer create --os macos --name private-mac --no-clipboard
```

The choice is saved with the computer, so stopping and starting it keeps the same setting.

## Share files

Add one folder from your Mac when you create the computer:

```bash
celesto computer create --os macos --name shared-mac --mount "$PWD"
```

The folder is read-only unless you add `--writable-mounts`. Use Finder inside the computer to open the shared folder.

## Install and use apps

Inside the desktop, macOS works normally. You can open a downloaded `.dmg`, drag an app into Applications, respond to permission prompts, and restart the computer when an installer requires it. Celesto does not turn off System Integrity Protection, Gatekeeper, or macOS permission prompts.

Stop the computer when you are done for now:

```bash
celesto computer stop test-mac
```

Delete it to discard its private disk:

```bash
celesto computer delete test-mac
```

The reusable base image remains, so creating the next macOS computer is much faster. Remove that image separately with `celesto image rm macos-latest`.

## Prepare an image ahead of time

You can perform the long preparation step before creating a computer:

```bash
celesto image build --os macos --ipsw latest -t macos-latest
```

The restore file comes from Apple and the finished image stays on your Mac. Celesto does not support saving, loading, or publishing macOS images.

## Preview limits

- Only Apple Silicon Macs are supported.
- Each macOS computer uses 4 CPU cores, 8 GB of memory, and an 80 GB logical disk; custom resource sizes are not enabled yet.
- At most two macOS computers can run at once.
- Shell, exec, file transfer, and SSH tunnels are not enabled for macOS computers in this preview; desktop access works independently.
- Bridge networking, outbound-domain rules, pause and resume, snapshots, and browser sessions are not supported for macOS computers yet.
- The base image and each macOS computer are tied to your Mac. Review [Apple's current software license agreements](https://www.apple.com/legal/sla/) and use hardware you own or control for permitted development and testing.

**Implementation notes:** macOS image ownership is in [`src/celesto/macos/images.py`](../../src/celesto/macos/images.py), runtime translation is in [`src/celesto/macos/lume.py`](../../src/celesto/macos/lume.py), and lifecycle integration is covered by [`tests/macos/test_vm_macos.py`](../../tests/macos/test_vm_macos.py) and [`tests/runtime/test_runtime_vz.py`](../../tests/runtime/test_runtime_vz.py).

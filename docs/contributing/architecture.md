# Architecture

Celesto turns a requested sandbox into a guest image, a runtime process, and a small amount of local state. This map helps contributors find the code that owns a behavior before changing it.

## Main layers

| Layer | Responsibility | Code |
| --- | --- | --- |
| Public API | Instance-oriented `Celesto` lifecycle, commands, files, mounts, ports, and snapshots. | [`src/celesto/facade.py`](../../src/celesto/facade.py) |
| Lifecycle manager | Persists state and creates, starts, stops, deletes, and restores sandbox resources. | [`src/celesto/vm.py`](../../src/celesto/vm.py) |
| Runtime adapters | Start QEMU, Firecracker, libkrun, or Apple Virtualization.framework and handle backend-specific work. | [`src/celesto/runtime/`](../../src/celesto/runtime) |
| Guest communication | Chooses and implements SSH or vsock control. | [`src/celesto/comm/`](../../src/celesto/comm) |
| Images | Finds, builds, caches, and prepares boot images, including local-only macOS bundles. | [`src/celesto/images/`](../../src/celesto/images), [`src/celesto/macos/`](../../src/celesto/macos) |
| Host services | Checks the host and manages networking, disks, and setup. | [`src/celesto/host/`](../../src/celesto/host) |
| State | Stores sandbox, snapshot, and browser-session metadata in SQLite or Postgres. | [`src/celesto/storage/`](../../src/celesto/storage) |
| Interfaces | Registers the CLI, browser sessions, dashboard, and HTTP API. | [`src/celesto/cli/`](../../src/celesto/cli), [`src/celesto/browser.py`](../../src/celesto/browser.py), [`src/celesto/server/`](../../src/celesto/server) |

## A normal sandbox lifecycle

1. The CLI or Python API creates a `VMConfig`.
2. `CelestoManager` materializes an isolated disk and records sandbox state.
3. The selected runtime starts the guest.
4. `Celesto` waits for the selected control channel, then performs commands or file operations. A macOS desktop instead becomes ready when its loopback display is available; SSH may follow later.
5. Stop or delete releases runtime resources; delete also removes managed state unless the configuration says otherwise.

This flow is implemented primarily by [`Celesto`](../../src/celesto/facade.py) and [`CelestoManager`](../../src/celesto/vm.py), and exercised by [`tests/test_facade.py`](../../tests/test_facade.py), [`tests/test_vm.py`](../../tests/test_vm.py), and [`tests/test_async_lifecycle.py`](../../tests/test_async_lifecycle.py).

## Backend and control-channel selection

`auto` selects Apple Virtualization.framework (`vz`) for a macOS guest on Apple Silicon. Linux guests still prefer QEMU on macOS and Firecracker on Linux. Automatic control-channel selection uses supported vsock when available and SSH otherwise; Windows guests use SSH in automatic mode. An explicit vsock request for Windows or macOS is rejected instead of falling back to SSH. These are current implementation details, so update this document with [`runtime/backends.py`](../../src/celesto/runtime/backends.py) and [`comm/select.py`](../../src/celesto/comm/select.py) whenever selection rules change.

## How to change behavior safely

Start from the public API or CLI test that describes the user-visible outcome. Then follow the call into the owning layer above. Add or update a focused test in `tests/` with the code change, and update the relevant user guide if the observable behavior changes.

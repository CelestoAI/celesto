# celesto-core

`celesto-core` is the Rust helper package that lets Celesto do local VM setup faster.
Most users install `celesto`; it pulls in the matching `celesto-core` wheel automatically.

```bash
pip install 'celesto==0.0.15a0'
```

Install `celesto-core` directly only when you are developing the native helper package or testing a package release.

## Work On celesto-core From Source

Use the source checkout when you are changing the Rust helpers or their Python wrappers:

```bash
uv sync --extra dev
uv sync --reinstall-package celesto-core
uv run python -m celesto_core
```

The last command should print the capability report for the extension you just built. Run it again after changing Rust or wrapper code so you know Python is loading the current local build.

For Rust-only checks, run:

```bash
cargo test -p celesto-core
```

If that command cannot find `libpython`, install the Python development package for the interpreter you are using, then rerun the test. Local Python installs that ship only a versioned shared library may also need `LIBRARY_PATH` pointed at the directory containing `libpythonX.Y.so`.

## Check What Is Available

Run this command to see which native helpers your current wheel can use:

```bash
python -m celesto_core
```

It prints a JSON report with four capability flags:

- `networking`: Linux TAP devices, routes, and sysctls can use direct Rust calls.
- `disk_io`: disk image copy and decompression helpers are available.
- `qmp`: QEMU monitor control is available.
- `firecracker_api`: Firecracker API socket control is available.

## Public Python Modules

Import the module for the job you want to do:

```python
from celesto_core import capabilities, disk, firecracker, network, qmp
```

Use `capabilities.detect()` when you need one structured result:

```python
from celesto_core import capabilities

print(capabilities.detect().as_dict())
```

Use `network` for Linux networking setup:

```python
from celesto_core import network

network.prepare_tap("tap0", owner_uid=1000, host_ip="172.16.0.1", prefix_len=32)
network.add_route("172.16.0.2", 32, "tap0")
```

These calls require permission to change Linux networking directly, usually root or `CAP_NET_ADMIN`. If Celesto does not have that permission, the main `celesto` package falls back to `ip`, `nft`, and `sysctl` subprocesses so the sandbox can still work.

Use `disk` for sparse disk images:

```python
from celesto_core import disk

method = disk.clone_or_sparse_copy("base.ext4", "sandbox.ext4")
print(method)
```

Use `qmp` for QEMU control:

```python
from pathlib import Path
from celesto_core import qmp

with qmp.QMPClient(Path("/tmp/qmp.sock")) as client:
    client.connect()
    print(client.query_status())
```

Use `firecracker` for Firecracker API socket requests:

```python
from pathlib import Path
from celesto_core import firecracker

client = firecracker.FirecrackerClient(Path("/tmp/firecracker.socket"))
print(client.request("GET", "/"))
```

## Migrate From The Old Flat API

This alpha refactor removes the old top-level helper aliases. Import the module for the area you need instead:

| Old form | New form |
| --- | --- |
| `celesto_core.has_native_networking()` | `celesto_core.network.available()` |
| `celesto_core.has_native_disk_io()` | `celesto_core.disk.available()` |
| `celesto_core.has_native_qmp()` | `celesto_core.qmp.available()` |
| `celesto_core.has_native_firecracker_api()` | `celesto_core.firecracker.available()` |
| `celesto_core.configure_tap(...)` | `celesto_core.network.configure_tap(...)` |
| `celesto_core.create_tap(...)`, `delete_tap(...)`, `add_route(...)`, `write_sysctl(...)` | `celesto_core.network.<function>(...)` |
| `celesto_core._QmpClient` | `celesto_core.qmp.QMPClient` |
| raw `_firecracker_*` helpers | `celesto_core.firecracker.FirecrackerClient` |

## Private Extension Boundary

The compiled PyO3 module is `celesto_core._ffi`. Treat it as an implementation detail.

Public callers should import `celesto_core.network`, `celesto_core.disk`, `celesto_core.qmp`, or `celesto_core.firecracker`. The private module can change without a compatibility alias during the alpha period.

## Rust Library Shape

The Rust crate exposes the same core areas:

- `celesto_core::disk`
- `celesto_core::firecracker` on Unix
- `celesto_core::qmp`
- `celesto_core::network` on Linux

The Python bindings live in a separate Rust binding module so the Rust library modules stay readable and testable.

## Versioning And Release Tags

`celesto-core` uses date-based versions in `YYYY.M.D` form, such as `2026.9.22`. This keeps the same version valid for Cargo, maturin, and Python package metadata.

Release tags use the same version with a `core-v` prefix:

```bash
git tag core-v2026.9.22
git push origin core-v2026.9.22
```

The publish workflow checks that the tag matches `celesto-core/Cargo.toml` before it builds wheels and publishes them to PyPI.

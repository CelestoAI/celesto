# Save and restore a sandbox

A snapshot saves a supported sandbox so you can bring it back later. Create the sandbox without workspace mounts or extra drives when you know you will need a snapshot.

## Create a snapshot

Create a named snapshot from a sandbox:

```bash
celesto sandbox snapshot create demo --snapshot-id demo-before-change
```

List saved snapshots:

```bash
celesto sandbox snapshot list --vm-id demo
```

Restore the snapshot when you need it:

```bash
celesto sandbox snapshot restore demo-before-change
```

## Choose a snapshot type

`full` is the default and saves disk plus running-state information. `diff` stores only changes from the base image, so it needs that base image to remain available. `disk` saves a self-contained disk without RAM, so restore starts the guest from disk rather than resuming it.

```bash
celesto sandbox snapshot create demo --snapshot-type disk
```

A live snapshot leaves a running QEMU sandbox available, but it must be a disk snapshot:

```bash
celesto sandbox snapshot create demo --snapshot-type disk --resume-source --live-only
```

## Current limits

Snapshots do not support Windows guests, workspace mounts, extra drives, shared disks, or raw QEMU disks. Snapshot creation can pause a sandbox unless you use the live-only command above.

**Implementation notes:** snapshot types and their meanings are defined in [`src/celesto/types.py`](../../src/celesto/types.py); support checks and restore behavior are in [`src/celesto/vm.py`](../../src/celesto/vm.py); the facade flushes a guest before a disk snapshot in [`src/celesto/facade.py`](../../src/celesto/facade.py). See [`tests/test_snapshot.py`](../../tests/test_snapshot.py) and [`tests/test_snapshot_qemu.py`](../../tests/test_snapshot_qemu.py).

## Save and restore from Python

Give creation and restore the same inventory so both can find the snapshot. The default SDK inventory lives in memory: `data_dir` controls where files are stored, but does not reconnect snapshot records between SDK objects or processes.

This Linux Firecracker example saves and restores a sandbox with outbound access off. Commands still work through the direct connection:

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from celesto import Celesto
from celesto.storage import MemoryStateManager

with TemporaryDirectory() as directory:
    workdir = Path(directory)
    inventory = MemoryStateManager(workdir)
    with Celesto(
        backend="firecracker",
        comm_channel="vsock",
        internet_settings={"mode": "off"},
        data_dir=workdir,
        state_manager=inventory,
    ) as vm:
        snapshot = vm.snapshot(snapshot_type="disk")

    with Celesto.from_snapshot(
        snapshot.snapshot_id,
        backend="firecracker",
        data_dir=workdir,
        state_manager=inventory,
    ) as restored:
        print(restored.run("echo restored").stdout)
```

Restore inherits the saved network policy. Reconnecting by `vm_id` also requires the original inventory and cannot change the policy. Use the CLI's persistent inventory for workflows that must continue across processes.

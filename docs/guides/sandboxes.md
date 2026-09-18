# Run a sandbox

A sandbox is a short-lived computer that Celesto creates for code or an agent. Give it a name so you can use the same name in later commands.

## Create and use one

```bash
celesto sandbox create --name demo
```

Open a shell in the sandbox:

```bash
celesto sandbox shell demo
```

When you are finished, stop or delete it:

```bash
celesto sandbox stop demo
celesto sandbox delete demo
```

Use `celesto sandbox list` to see your sandboxes, including their current state. `celesto sandbox info demo` shows one sandbox in detail.

## Keep work on your machine

Mount a host directory when an agent needs the files in it. Mounts are read-only by default, so sandbox changes stay in the sandbox.

```bash
celesto sandbox create --name project --mount "$PWD:/workspace"
```

Allow the sandbox to write back only when you intend to share those changes:

```bash
celesto sandbox create --name project --mount "$PWD:/workspace" --writable-mounts
```

## Move files and settings

Copy a file into the sandbox:

```bash
celesto sandbox file upload demo ./input.txt /tmp/input.txt
```

Set an environment variable that later sandbox commands can use:

```bash
celesto sandbox env set demo API_URL=https://example.com
```

Share a service running on sandbox port 3000 with your machine. Without a host port, Celesto selects one:

```bash
celesto sandbox port expose demo 3000
celesto sandbox port list demo
```

## Python

The same basic lifecycle is available from Python:

```python
from celesto import Celesto

with Celesto() as vm:
    result = vm.run("echo hello")
    print(result.stdout)
```

## Limits and implementation notes

Workspace mounts currently use QEMU; when mounts are requested without an explicit backend, Celesto selects QEMU. The default disk mode is isolated, which gives each sandbox its own writable disk. See [`src/celesto/facade.py`](../../src/celesto/facade.py), [`src/celesto/types.py`](../../src/celesto/types.py), and the behavior tests in [`tests/test_workspace.py`](../../tests/test_workspace.py), [`tests/test_facade.py`](../../tests/test_facade.py), and [`tests/test_cli.py`](../../tests/test_cli.py).

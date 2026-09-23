# Run a minimal computer

A minimal computer is an isolated machine for code or an agent. Give it a name so you can use the same name in later commands. `celesto sandbox` is an equivalent spelling for every `celesto computer` command.

## Create and use one

```bash
celesto computer create --name demo
```

Open a shell in the sandbox:

```bash
celesto computer shell demo
```

When you are finished, stop or delete it:

```bash
celesto computer stop demo
celesto computer delete demo
```

Use `celesto computer list` to see your sandboxes, including their current state. `celesto computer info demo` shows one sandbox in detail.

## Keep work on your machine

Mount a host directory when an agent needs the files in it. Mounts are read-only by default, so sandbox changes stay in the sandbox.

```bash
celesto computer create --name project --mount "$PWD:/workspace"
```

Allow the sandbox to write back only when you intend to share those changes:

```bash
celesto computer create --name project --mount "$PWD:/workspace" --writable-mounts
```

## Move files and settings

Copy a file into the sandbox:

```bash
celesto computer file upload demo ./input.txt /tmp/input.txt
```

Set an environment variable that later sandbox commands can use:

```bash
celesto computer env set demo API_URL=https://example.com
```

Share a service running on sandbox port 3000 with your machine. Without a host port, Celesto selects one:

```bash
celesto computer port expose demo 3000
celesto computer port list demo
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

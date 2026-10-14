# Run a minimal computer

A minimal computer is an isolated, disposable virtual machine for code or an agent. It has no desktop, so you work with it through commands and a shell. Give it a name so you can use the same name in later commands. `celesto sandbox` is an equivalent spelling for every `celesto computer` command.

## Create and use one

```bash
celesto computer create --name demo
```

Open a shell in the computer:

```bash
celesto computer shell demo
```

When you are finished, stop or delete it:

```bash
celesto computer stop demo
celesto computer delete demo
```

Use `celesto computer list` to see your computers, including their current state. `celesto computer info demo` shows one computer in detail.

## Keep work on your machine

Share a folder from your machine when an agent needs the files in it. Shared folders are read-only by default, so changes made inside the computer stay there.

```bash
celesto computer create --name project --mount "$PWD:/workspace"
```

Allow the computer to write back only when you intend to share those changes:

```bash
celesto computer create --name project --mount "$PWD:/workspace" --writable-mounts
```

## Move files and settings

Copy a file into the computer:

```bash
celesto computer file upload demo ./input.txt /tmp/input.txt
```

Set an environment variable that later commands in the computer can use:

```bash
celesto computer env set demo API_URL=https://example.com
```

Share a service running on port 3000 inside the computer with your machine. If you do not choose a port on your machine, Celesto selects one:

```bash
celesto computer port expose demo 3000
celesto computer port list demo
```

## Python

The same basic lifecycle is available from Python:

```python
from celesto import Celesto

with Celesto() as computer:
    result = computer.run("echo hello")
    print(result.stdout)
```

## Limits and implementation notes

Shared folders (`--mount`) currently use QEMU; when you request one without an explicit backend, Celesto selects QEMU. The default disk mode is isolated, which gives each computer its own writable disk. See [`src/celesto/facade.py`](../../src/celesto/facade.py), [`src/celesto/types.py`](../../src/celesto/types.py), and the behavior tests in [`tests/windows/test_workspace.py`](../../tests/windows/test_workspace.py), [`tests/vm/test_facade.py`](../../tests/vm/test_facade.py), and [`tests/cli/test_cli.py`](../../tests/cli/test_cli.py).

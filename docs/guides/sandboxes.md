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

## Fork a sandbox

Forking makes a new sandbox that starts as a copy of an existing one. Use it to set a sandbox up once (install tools, clone a project) and then hand identical copies to several agents or experiments. Each copy is its own sandbox: changes in one never reach the others or the original.

```bash
celesto computer fork demo
# demo-1  created
```

The new sandbox is running and ready to use, like any other:

```bash
celesto computer shell demo-1
```

### Make several copies

Add `--count` to make up to 10 copies at once:

```bash
celesto computer fork demo --count 3
# demo-2  created
# demo-3  created
# demo-4  created
```

Celesto starts 4 copies at the same time. Use `--parallel` to change that, for example `--parallel 1` on a small machine. If a copy is slow to start, give it more time with `--boot-timeout` (in seconds, 30 by default).

### Choose the names

Without a name, copies continue the numbering after the original's name, so a second fork of `demo` continues from `demo-5`. Choose a name with `--name`:

```bash
celesto computer fork demo --name experiment
# experiment  created
```

With `--count`, the copies are numbered after that name: `--name exp --count 3` makes `exp-1`, `exp-2`, and `exp-3`.

If a name you asked for already exists, the fork stops before it copies anything. That makes `--name` the safe choice for scripts and agents: if a fork is retried, it can't make extra copies.

### What each copy gets

Each copy starts with the original's files and settings: CPU, memory, disk size, internet rules, SSH key, and environment variables. Environment variables often hold secrets such as API keys, and any secrets saved in files on the disk are copied too. Fork only sandboxes whose secrets you are happy to share with every copy.

Each copy gets its own name, network address, SSH port, SSH host keys, and machine ID. Programs that were running in the original are not running in the copy; it starts fresh from the copied disk.

The original keeps running while it is copied. With the Firecracker engine (the default on Linux), Celesto pauses it for the moment its files are copied and prints `Pausing demo while its files are copied…`. You can also fork a stopped sandbox.

`celesto computer info demo-1` shows where a copy came from, in the `Forked From` and `Forked At` rows.

### What can't be forked

Celesto refuses to fork, and tells you what to do instead, when the sandbox:

- is paused. Resume it first with `celesto computer resume demo`.
- shares a folder from your machine (`--mount`).
- was created from an image older than this release. Create a new sandbox and fork that one.
- runs macOS or Windows. These sandboxes can't be forked yet.
- uses the libkrun engine, which Celesto picks when QEMU isn't installed. Create the sandbox again with `--backend qemu` to fork it.
- runs in Celesto Cloud. Fork works only on sandboxes on your machine for now.

A fork also stops before copying anything when there isn't enough disk space or there aren't enough free ports for every copy.

### Use fork from a script

Add `--json` for one entry per copy:

```bash
celesto computer fork demo --name exp --count 2 --json
```

```json
{
  "ok": false,
  "command": "sandbox.fork",
  "exit_code": 1,
  "data": {
    "source": "demo",
    "children": [
      {
        "name": "exp-1",
        "ok": true,
        "status": "created",
        "sandbox": {"name": "exp-1", "preset": null, "status": "running", "pid": 4242, "ip_address": "10.0.2.15", "ssh_port": 2223, "warnings": []},
        "error": null
      },
      {
        "name": "exp-2",
        "ok": false,
        "status": "failed",
        "sandbox": null,
        "error": "Sandbox 'exp-2' didn't start within 30 seconds and was removed. Run the fork again with '--boot-timeout 60'."
      }
    ],
    "warnings": [],
    "source_state": "running"
  },
  "error": {"code": "fork_failed", "message": "Sandbox 'exp-2' didn't start within 30 seconds and was removed. Run the fork again with '--boot-timeout 60'."}
}
```

Each copy succeeds or fails on its own. A copy that fails is removed, and the others are kept. The command exits with code 0 only when every copy was created, and 1 otherwise. When a fork is refused before anything is copied, `data` is `null` and `error.message` says how to fix it. `warnings` lists problems that didn't stop the fork, such as the original staying paused, and `source_state` is the original's state afterwards, or `null` if it was deleted while the fork finished. Notices such as `Pausing demo while its files are copied…` go to standard error, so the JSON stays readable.

## Python

The same basic lifecycle is available from Python:

```python
from celesto import Celesto

with Celesto() as vm:
    result = vm.run("echo hello")
    print(result.stdout)
```

Fork a sandbox with `fork()`. It returns the new sandbox, already running, and raises `CelestoError` with the same message the CLI shows if the fork fails:

```python
source = Celesto.from_id("demo")
copy = source.fork("experiment")
print(copy.run("ls /root").stdout)
```

Use `fork_many()` for several copies. It returns a `ForkBatch`: `children` holds one `ForkResult` per copy (`name`, `ok`, `sandbox` when it worked, `error` when it didn't), plus `warnings` and `source_state`. It raises only when the fork is refused before any copy is made.

```python
batch = source.fork_many(3, name="exp")
for child in batch.children:
    print(child.name, "created" if child.ok else child.error)
```

`fork()` reports problems that didn't stop the fork, such as the original staying paused, as a `CelestoWarning`. Python shows it by default; turn it into an error with `warnings.simplefilter("error", celesto.CelestoWarning)`. `async_fork()` and `async_fork_many()` do the same from async code.

## Limits and implementation notes

Workspace mounts currently use QEMU; when mounts are requested without an explicit backend, Celesto selects QEMU. The default disk mode is isolated, which gives each sandbox its own writable disk. See [`src/celesto/facade.py`](../../src/celesto/facade.py), [`src/celesto/types.py`](../../src/celesto/types.py), and the behavior tests in [`tests/test_workspace.py`](../../tests/test_workspace.py), [`tests/test_facade.py`](../../tests/test_facade.py), and [`tests/test_cli.py`](../../tests/test_cli.py).

# Run locally or in the cloud

Celesto runs computers on your machine by default. Choose the cloud explicitly when you want Celesto to run them for you.

## Python

```python
from celesto import Computer

with Computer() as computer:
    print(computer.run("echo hello").stdout)
```

For cloud execution, set `CELESTO_API_KEY` and pass `provider="cloud"`.
Alternatively, choose a fixed location through your import:

```python
from celesto import CloudComputer as Computer

with Computer() as computer:
    print(computer.run("echo hello").stdout)
```

Use `LocalComputer` for an explicitly local import. These classes share lifecycle,
command, streaming, and terminal behavior. Public port publishing and terminal
reattachment remain cloud-only. Local folder sharing is not a cloud upload.

`Computer.get(id)` reconnects locally; `CloudComputer.get(id)` reconnects in the
cloud. Reconnection does not create a replacement computer or take ownership of
automatic deletion. Local lookup accepts desktop IDs from `celesto computer list`
and existing VM IDs. Browser-only session IDs are rejected.

`start()` explicitly provisions a new handle; construction alone does not.
`close()` releases connections without deleting the computer. Use `delete()` to
remove it, or use an ephemeral computer in a `with` block for automatic deletion.

## Command line

Create a local desktop computer without a cloud account:

```console
celesto computer create
# Started computer 'computer-…'.
```

Copy the computer ID printed by that command, then open its terminal:

```console
celesto computer terminal COMPUTER_ID
```

For a single command, use `exec` instead. It starts a stopped local computer
and returns the command's exit code:

```console
celesto computer exec COMPUTER_ID -- python --version
```

Exiting the terminal keeps the computer and its files. Remove it when finished:

```console
celesto computer delete COMPUTER_ID
```

To create a cloud computer, run `celesto auth login` or set `CELESTO_API_KEY`, then run:

```console
celesto computer create --cloud
# Created cloud computer '…'.
```

Use `--cloud` on subsequent `list`, `terminal`, `exec`, and `delete` commands too.
For example, run `celesto computer exec COMPUTER_ID --cloud -- python --version`.
The cloud-only `computer run` command also accepts a single shell string.
Cloud listing requests up to 50 computers by default. Use `--limit NUMBER` to
request more. A full response may omit additional computers because the service
does not provide pagination; Celesto warns when that is possible. JSON output
includes `possibly_truncated` so scripts can detect it.
Cloud terminal attachment reports connection success or failure; the current
gateway adapter does not expose a remote shell exit code. `--boot-timeout` on
`terminal` applies only to local computers.
Unflagged commands always select local execution; `--local` is an explicit
equivalent. The two flags cannot be combined. Existing `computer start` remains
the configurable local desktop workflow when no ID is given. Pass a computer ID
to `celesto computer start` to resume a cloud computer. Cloud `open`, `logs`, and
`templates` are not exposed by this CLI yet.

## Migrating from cloud-first versions

The default of `Computer()` and `Computer.get(id)` changed from cloud to local.
Change cloud applications to `CloudComputer`, or add `provider="cloud"` to
construction and reconnection. Explicit `local=True` and `local=False` remain
supported; conflicting selectors are rejected. Credentials never change the
default, and a failed operation never falls back to another location.

These changes apply to the source checkout and its next release. Existing
resources, saved data, and image caches are not migrated or deleted.

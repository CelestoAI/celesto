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

Create a minimal local computer without a cloud account:

```console
celesto computer create --name demo
# Created VM 'demo'.
```

Use its name to open a shell or run a single command:

```console
celesto computer shell demo
celesto computer exec demo -- python --version
```

`exec` returns the command's exit code. If the computer is stopped, add `--start`:

```console
celesto computer exec demo --start -- python --version
```

Exiting the shell keeps the computer and its files. Remove it when finished:

```console
celesto computer delete demo
```

For a visible Linux desktop, request it explicitly. The create output includes
the desktop ID used by the next commands:

```console
celesto computer create --desktop --name assistant
celesto computer list --desktop
celesto computer open assistant
celesto computer delete assistant --desktop
```

To create a cloud computer, run `celesto auth login` or set `CELESTO_API_KEY`, then run:

```console
celesto computer create --cloud
# Created cloud computer '…'.
```

Use `--cloud` on subsequent `list`, `start`, `stop`, `info`, `ssh`, `exec`, and `delete` commands too.
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
equivalent. The two flags cannot be combined. `computer start COMPUTER_ID` starts
an existing local computer; add `--cloud` to start a cloud computer. Cloud `open`,
`logs`, and `templates` are not exposed by this CLI yet. `celesto sandbox` is an
equivalent spelling for every `celesto computer` subcommand, including cloud
operations.

## Migrating from cloud-first versions

The default of `Computer()` and `Computer.get(id)` changed from cloud to local.
Change cloud applications to `CloudComputer`, or add `provider="cloud"` to
construction and reconnection. Explicit `local=True` and `local=False` remain
supported; conflicting selectors are rejected. Credentials never change the
default, and a failed operation never falls back to another location.

These changes apply to the source checkout and its next release. Existing
resources, saved data, and image caches are not migrated or deleted.

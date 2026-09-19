# Python cloud computers

Run commands on a Celesto Cloud computer using the same Python interface as local execution. Your machine does not boot a virtual machine when you use the cloud.

Install `celesto==0.0.15a0` and set `CELESTO_API_KEY` in your environment.

```bash
pip install 'celesto==0.0.15a0'
```

```python
from celesto import Computer

with Computer() as comp:
    result = comp.run("echo hello")
    print(result.stdout)
```

The constructor validates configuration without contacting the server. Entering the block creates a computer and waits for it to run. Each command returns `stdout`, `stderr`, and `exit_code`; nonzero command exit codes do not raise an exception. Cloud commands support up to 10,000 characters and a timeout of 1–300 seconds.

## Stream command output

Use `run_stream()` when output should be handled as it arrives. It has the same
interface for cloud and local computers and does not change the buffered `run()` API.

```python
from celesto import CommandExitEvent, CommandOutputEvent, Computer

with Computer() as comp:
    for event in comp.run_stream("python agent.py"):
        if isinstance(event, CommandOutputEvent):
            print(event.data, end="")
        elif isinstance(event, CommandExitEvent):
            print(f"exit code: {event.exit_code}")
```

The iterator normally begins with a `CommandStartedEvent`, yields `CommandOutputEvent`
objects whose `type` is `"stdout"` or `"stderr"`, and ends with one
`CommandExitEvent`. If you stop early, close the iterator to close its connection.
The command must not be assumed to have stopped until the computer reports that separately.

## Open an interactive terminal

Use `terminal()` when a person needs an interactive shell rather than a single
command. `attach()` connects the current process's terminal and blocks until the
shell exits or you detach.

```python
from celesto import Computer

with Computer() as comp:
    terminal = comp.terminal()
    terminal.attach()
```

Press Ctrl+] to detach without ending the cloud shell. A cloud terminal has a
durable ID that can be used to request fresh short-lived connection credentials:

```python
terminal_id = terminal.terminal_id
assert terminal_id is not None
comp.terminal(terminal_id=terminal_id).attach()
```

Reattachment works only while the computer and terminal session still exist.
The connection token is intentionally private and does not appear in
`TerminalConnection` representations. Terminal connection creation and
WebSocket attachment are never retried automatically; this avoids duplicating a
session or replaying terminal input after an ambiguous network failure.

`Computer(local=True).terminal()` has the same `attach()` API but no durable
terminal ID because the current local transport does not support reattachment.

The block deletes the computer on exit, even if your code raises. Cleanup waits until the API reports deletion or no longer finds the computer. A cleanup error remains visible and you can retry `comp.delete()`. If both your code and cleanup fail, Python reports both in an exception group.

## Keep and reconnect

```python
comp = Computer(lifetime="persistent")
comp.run("echo hello")
computer_id = comp.id
reconnected = Computer.get(computer_id)
reconnected.run("echo again")
reconnected.delete()
```

Persistent and reconnected handles cannot enter a `with` block. Reconnecting never creates or starts a replacement computer. Outside a block, both lifetimes require explicit deletion. Neither lifetime adds server-side expiry or guarantees cleanup after a process crash or network loss. Cloud service policies still apply.

Persistence here means retaining the computer resource; it does not enable an external disk. `external_volume_enabled=True` is a separate cloud option for disk retention across stop/restore, not a lifecycle setting.

## Connection and creation options

Pass `api_key=` to override `CELESTO_API_KEY`, and `organization_id=` to select an organization. `base_url=` defaults to `https://api.celesto.ai` and must be the server origin without `/v1`. HTTPS is required except for localhost development servers. Credentials go only to that explicitly selected origin; redirects are not followed.

Cloud creation accepts `vcpus`, `ram_mb`, `disk_size_mb`, `image`, `template_id`, `template_version`, and `external_volume_enabled`. Local options such as `mounts` and `data_dir` are not cloud options and are rejected. `startup_timeout` and `cleanup_timeout` default to 120 seconds and bound polling; individual network timeout limits are not a guarantee against every stalled or trickling response.

HTTP failures raise `CloudAPIError` with a `status_code`. Missing computers raise `VMNotFoundError`. Transport failures raise `CelestoError`: creation or command execution may have succeeded even when its response was lost. No creation or command request is automatically replayed. Inspect the cloud dashboard before retrying an operation with an unknown outcome.

## Live smoke test

The live test creates one billable cloud computer, runs commands, reconnects to it,
and checks that context exit deletes it. It is skipped by default. With
`CELESTO_API_KEY` already set, opt in explicitly:

```bash
CELESTO_LIVE_TEST=1 uv run --extra dev pytest tests/test_cloud_live.py -q -s
```

The test retries cleanup on failure but cannot guarantee cleanup if the process
is killed or a create response is lost. Check the cloud dashboard in those cases.

The manually dispatched **Celesto cloud installed-wheel smoke** GitHub Actions
workflow builds the wheel, installs it in a clean environment, and runs the same
test. Add `CELESTO_API_KEY` as a repository secret before running the workflow.
Run it from the `main` branch. The workflow records the created computer ID and
makes a final cleanup attempt even when the test fails.

## Generated client

The private `_celesto_cloud_api` package contains generated requests and models. It ships
inside the same Python distribution as `celesto`; it is not a separate PyPI package or a
public SDK interface. The public `Computer` keeps these types out of its API and uses the
generated ordinary command endpoint. Streaming uses a small handwritten SSE adapter because
generated OpenAPI clients buffer `text/event-stream` responses. Terminal session
creation uses the generated HTTP endpoint, while terminal WebSocket I/O uses a
small handwritten bounded adapter. Browser and file APIs are not exposed by this
wrapper yet.

The generator consumes the committed `openapi/cloud.json` snapshot. After updating that snapshot from the backend's exported document, regenerate with:

```bash
bash scripts/generate_cloud_client.sh
```

Review and commit the snapshot and generated diff together. The script pins `openapi-python-client==0.29.1` and replaces only `src/_celesto_cloud_api`. Never hand-edit those generated files. No schema export service, custom templates, or separate SDK publication is needed.

# Python cloud computers

Run commands on a Celesto Cloud computer using the same Python interface as local execution. Your machine does not boot a virtual machine when you use the cloud.

Install the existing `smolvm` package from this checkout and set `CELESTO_API_KEY` in your environment. The distribution name and native installation dependencies have not changed in this increment.

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

## Publish an application

Give an HTTP application inside your cloud computer a public URL. Start the
application first, listening on `0.0.0.0` and a port from `1024` to `65535`.
For example, this serves a small demo page from its own directory:

```python
from celesto import Computer

with Computer() as comp:
    comp.run(
        "mkdir -p /tmp/demo && printf 'Hello from Celesto' > /tmp/demo/index.html"
    )
    comp.run(
        "nohup python3 -m http.server 8000 --bind 0.0.0.0 --directory /tmp/demo "
        ">/tmp/demo.log 2>&1 </dev/null &"
    )
    route = comp.publish_port(8000)
    print(route.url)
    print(comp.published_ports())
    input("Press Enter to remove the public route and delete the computer. ")
    removed = comp.unpublish_port(8000)
    print(removed.status)
```

Publishing makes the application accessible from the internet; add authentication
to the application if it needs access control. The route does not start your
application or guarantee it is ready to respond. These methods publish HTTP
applications, not arbitrary TCP or UDP services. Celesto system ports are reserved
and may be rejected by the service even within the allowed range.

Each result is a `PublishedPort`, importable from `celesto`, with `computer_id`,
`port`, `status`, and optional `id`, `url`, and `created_at` (the service's timestamp
string). Missing metadata is `None`. Results are immutable snapshots; call
`published_ports()` for current routes. URLs are omitted from `repr()` and printed
objects; access `.url` explicitly. Unpublishing removes the route without stopping
the application, and succeeds even when that port has no route.

All three methods are cloud-only. Local calls raise `CelestoError` before starting
a computer. Invalid port arguments raise `ValueError` before allocation. On a fresh
cloud handle, each valid method creates the computer if needed; use
`Computer.get(computer_id)` to manage an existing computer's routes. Publish and
unpublish requests are never automatically replayed: after an uncertain outcome,
inspect `published_ports()` or the cloud dashboard before retrying.

## Connection and creation options

Pass `api_key=` to override `CELESTO_API_KEY`, and `organization_id=` to select an organization. `base_url=` defaults to `https://api.celesto.ai` and must be the server origin without `/v1`. HTTPS is required except for localhost development servers. Credentials go only to that explicitly selected origin; redirects are not followed.

Cloud creation accepts `vcpus`, `ram_mb`, `disk_size_mb`, `image`, `template_id`, `template_version`, and `external_volume_enabled`. Local options such as `mounts` and `data_dir` are not cloud options and are rejected. `startup_timeout` and `cleanup_timeout` default to 120 seconds and bound polling; individual network timeout limits are not a guarantee against every stalled or trickling response.

HTTP failures raise `CloudAPIError` with a `status_code`. Missing computers raise `VMNotFoundError`. Transport failures raise `CelestoError`: creation or command execution may have succeeded even when its response was lost. No creation or command request is automatically replayed. Inspect the cloud dashboard before retrying an operation with an unknown outcome.

## Live smoke test

The live test creates one billable cloud computer, runs commands, reconnects to it,
publishes and fetches a test HTTP application, removes its route, and checks that
context exit deletes the computer. It is skipped by default. With
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
generated ordinary command and published-port endpoints. Streaming uses a small handwritten SSE adapter because
generated OpenAPI clients buffer `text/event-stream` responses. Browser, terminal, and file
APIs are not exposed by this wrapper yet.

The generator consumes the committed `openapi/cloud.json` snapshot. After updating that snapshot from the backend's exported document, regenerate with:

```bash
bash scripts/generate_cloud_client.sh
```

Review and commit the snapshot and generated diff together. The script pins `openapi-python-client==0.29.1` and replaces only `src/_celesto_cloud_api`. Never hand-edit those generated files. No schema export service, custom templates, or separate SDK publication is needed.

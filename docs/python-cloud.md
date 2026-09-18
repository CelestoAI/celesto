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

## Generated client

The private `celesto._generated` package contains generated requests and models. It is not a public SDK interface. The public `Computer` keeps these types out of its API and uses the ordinary command endpoint; streaming, browser, terminal, and file APIs are not exposed by this wrapper yet.

The generator consumes the committed `openapi/cloud.json` snapshot. After updating that snapshot from the backend's exported document, regenerate with:

```bash
bash scripts/generate_cloud_client.sh
```

Review and commit the snapshot and generated diff together. The script pins `openapi-python-client==0.29.1` and replaces only `src/celesto/_generated`. Never hand-edit those generated files. No schema export service, custom templates, or separate SDK publication is needed.

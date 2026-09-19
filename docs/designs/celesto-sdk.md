# Celesto SDK

Celesto gives an agent a computer, either on the user's machine or in the cloud. The same Python code runs commands and manages that computer in either location.

Status: Local first release shipped; core cloud Computer integration implemented on a follow-up branch.
Date: 2026-09-18

## Implementation update — 2026-09-19

The current increment uses `openapi-python-client==0.29.1` against a full schema
downloaded from the running backend. A pinned Ruff formatter makes regeneration
repeatable. This supersedes the isolated-export and filtered-artifact machinery
proposed below; no custom export framework was added.

The private client is in `_celesto_cloud_api`; the public `Computer` now routes
cloud create/get/run/delete through it. Local behavior remains unchanged.
Streaming is documented correctly in the schema but not exposed by the public
wrapper yet. Server-side expiry, a cloud-only dependency/distribution split,
TypeScript, and the other cloud APIs remain deferred. See [Python cloud usage](../python-cloud.md)
for implemented behavior and limitations; the historical proposal below is not
a claim that those deferred features exist.

## Historical first release scope (local-only)

These bullets record the original local-only release, not the current cloud
implementation described above. Its cloud failure and deferral requirements
were superseded by the 2026-09-19 implementation update.

- Keep the distribution named `smolvm`; replace its Python import namespace with `celesto` without an import shim.
- Provide `Computer(local=True)` for local execution. `Computer()` fails with a local-only explanation until cloud support ships.
- Default to ephemeral and delete on context exit. Persistent computers require explicit deletion and cannot enter a context. Defer automatic expiry and crash cleanup.
- Defer provisioning until context entry or the first command; `id` is `None` beforehand. `Computer.get(id, local=True)` reconnects without creating a replacement or taking context ownership.
- Reuse the existing on-disk CLI inventory so computers remain inspectable and persistent computers can be reconnected after process exit.
- Rename the advanced Python interfaces to `Celesto`, `CelestoManager`, and `CelestoError`.
- Add the `celesto` executable while retaining `smolvm` for the existing TypeScript bridge. Preserve runtime protocol messages, native dependencies, guest image contents, data paths, and environment variables.
- Backend changes, OpenAPI generation, cloud integration, TypeScript/OpenMuse migration, and retirement of the separate SDK repository are later work.

The following sections retain the longer-term proposal as context, not first-release requirements.

## Agreed decisions

- Rename the product and SDK to Celesto. Make a clean API break without a deprecated SmolVM compatibility package.
- This repository becomes the home of the `celesto` Python package. Use `CelestoAI/sdk` as a migration source and retire it after the replacement ships; repository deletion is not part of this work.
- Focus this release on Python. Defer TypeScript and OpenMuse migration to a later release.
- Generate the cloud HTTP client from the backend's OpenAPI description, and build the handwritten public SDK above it.
- Design the public API afresh. Existing implementations can be reused, but their public names and lifecycle rules are not constraints.
- Use `from celesto import Computer` as the primary entry point.
- `Computer()` selects cloud. `Computer(local=True)` selects execution on this machine. Never silently switch locations when credentials or local prerequisites are missing.
- Default to `lifetime="ephemeral"`. Persistence is explicit: `Computer(lifetime="persistent")`.
- A `with` block owns an ephemeral computer and deletes it when the block exits, including when its body raises an exception.
- Reject persistent computers in a `with` block. Persistence means surviving the creating Python process, until explicitly deleted; local execution still depends on the machine remaining available.

## Public examples

These examples describe the proposed API, not functionality already shipped.

```python
from celesto import Computer

with Computer() as comp:
    result = comp.run("echo hello")
    print(result.stdout)
```

```python
with Computer(local=True) as comp:
    result = comp.run("echo hello")
```

```python
comp = Computer(local=True, lifetime="persistent")
comp.run("echo hello")
computer_id = comp.id
# The computer survives the Python process.
# Delete it explicitly when it is no longer needed:
comp.delete()
```

`run()` executes a command inside the computer. It does not interpret natural-language instructions or provide an agent model. Files such as `agent.py` must already exist there or be uploaded through the eventual file API.

## Proposed construction and cleanup contract

Use deferred provisioning so validation can happen before allocating resources. The constructor validates configuration only. Context entry or the first operation needing a running computer provisions it and waits for readiness. Reading `id` before provisioning returns `None`; after provisioning it is a stable identifier. There is no hidden allocation just to inspect an attribute.

This makes `with Computer(lifetime="persistent")` fail before creating a billable computer. Entering an already provisioned persistent handle also raises, but must not delete the existing computer. Deleting a handle that was never provisioned is a no-op that closes that handle.

Creation failures trigger bounded cleanup. If allocation may have succeeded despite a lost response, reconcile using an operation identifier; do not blindly repeat creation. A failed readiness check must not return a usable computer. Report any unresolved resource identity so cleanup can be retried.

`delete()` is idempotent and retryable after a cleanup failure. After deletion, operations fail clearly instead of creating a replacement. Exiting a context waits for confirmed deletion with a bounded timeout. If deletion fails, report that failure; if the body also raised, retain both errors rather than masking the original exception. Never claim successful deletion when only a deletion request was accepted.

Context cleanup cannot guarantee deletion after a hard process crash or a network partition. Ephemeral computers therefore need expiry enforced outside the client process, by the local supervisor or cloud service. Garbage collection and exit hooks are not the lifetime mechanism.

Proposed expiry behavior: a documented, configurable inactivity timeout refreshed by accepted operations; in-flight commands prevent idle expiry. Browser and desktop connections need a defined activity signal before those features ship. A finite maximum lifetime must bound abandoned or hung operations, including client death during an active command. Exact defaults, limits, and how expiry terminates active work must be settled against cloud capabilities before release. Persistent computers do not use ephemeral expiry.

Reconnect should retrieve an existing computer by ID and explicit location without creating one when it is missing. The exact reconnect spelling is not yet approved. IDs alone must not determine which server receives credentials.

## One contract across local and cloud

Keep provider-specific work behind the public `Computer` object. The local implementation can reuse the current VM runtime; the cloud implementation needs to target the actual cloud service contract. A cloud-only SDK install should not require native virtualization dependencies; a local installation extra is the proposed distribution mechanism.

Both implementations must agree on command result fields (`stdout`, `stderr`, `exit_code`), timeout units, command failure handling, readiness, lifetime, deletion, and missing-resource errors. Final `run()` options and error types require an implementation specification. Commands must not be replayed automatically after an ambiguous transport failure.

Capabilities can differ, but unsupported options must fail explicitly. Local folder sharing must not silently become cloud file upload. Images, OS availability, browser/display access, networking, and persistence support need capability checks instead of pretending every provider supports every feature.

A remote self-hosted service is distinct from `local=True`, which means this machine. Support an explicit endpoint configuration when the remote service contract is available. Validate incompatible local/endpoint settings and keep cloud credentials away from local execution.

## Existing implementation evidence

- `src/smolvm/facade.py` implements Python VM construction and command execution.
- `ts/src/index.ts` exposes client-owned local sandbox, browser, and computer collections.
- `open-muse/server/computer-provider.ts` already adapts local and cloud computers, but local reconnect is absent and deletion behavior differs.
- `pyproject.toml` publishes `smolvm` and requires native `smolvm-core` dependencies.

These are reusable implementation inputs, not evidence that the new contract already works.

Inspection of `CelestoAI/sdk` confirms that its Python `Computer` provisions immediately and its context exit only closes the HTTP client. Both behaviors change under this proposal. Its Python package is already named `celesto`.

Inspection of `CelestoAI/backend` confirms FastAPI setup in `src/celesto_api/main.py`, typed public computer routes in `src/celesto_api/v1/computers.py`, and Pydantic request/response definitions in `src/celesto_core/schemas/computer.py`. Production disables `/openapi.json`. The inspected create request has `external_volume_enabled`, not an explicit resource lifetime or idle expiry field. Disk preservation across stop/restore must not be confused with resource lifetime. Service expiry enforcement remains to be investigated.

## OpenAPI generation boundary

OpenAPI is the machine-readable API description. Swagger UI is a way to display it; it is not needed to generate a client.

```text
Backend route and model definitions
              |
     versioned public OpenAPI artifact
              |
     generated private Python client
              |
         cloud provider  ---- Computer ---- local provider
```

Export the description from FastAPI in backend CI, using `app.openapi()` or FastAPI's schema builder over the selected public routes. The export must run without starting the application lifespan, migrations, workers, or live service connections. Inspect import-time initialization before choosing the exact export command. Do not require opening the production schema endpoint.

Start with public computer operations and their referenced schemas, security definitions, and errors. Exclude internal host registration, heartbeat, telemetry, and other operator routes. Preserve an explicit operation inventory and stable unique operation IDs. Define missing error responses, streaming media types, and authentication declarations in the backend source instead of patching the exported JSON by hand.

Recommended first generator trial: OpenAPI Generator, because it supports both Python now and TypeScript later. Pin its exact version and configuration after testing against the real schema. Generate into private `_celesto_cloud_api` code, never over the handwritten package entry point or `Computer`. `openapi-python-client` is a Python-focused fallback if its generated output handles this schema better. A shared OpenAPI artifact does not require every future language to use the same generator.

Generated code owns endpoint paths, payload serialization, request/response models, and ordinary HTTP calls. The cloud adapter owns readiness polling, lifecycle orchestration, result/error normalization, and retry policy. `Computer` owns the public local/cloud contract. Generated models remain private so backend schema changes do not automatically redefine the public SDK.

Command streaming and browser/terminal WebSockets require a separate tested protocol layer where the generator cannot express their semantics. OpenAPI generation does not implement context cleanup, expiry, reconnection, or safe command retries. Do not regenerate those behaviors from endpoint names.

Commit a reviewed schema snapshot with its backend revision/hash, generator config, and generated source. Backend CI exports and validates the artifact; SDK CI regenerates from the pinned artifact and fails on drift, then runs type checks and provider contract tests. Backend schema updates should produce reviewable SDK diffs. SDK builds must not fetch an unversioned live schema.

Before retiring the SDK repository, inventory its non-computer APIs and decide which transfer to this repository. Generation must not silently drop existing agents, deployments, or delegated-access functionality merely because this first facade targets computers.

References: [backend](https://github.com/CelestoAI/backend), [existing Python wrapper](https://github.com/CelestoAI/sdk/blob/main/src/celesto/sdk/computer.py), [FastAPI schema export](https://fastapi.tiangolo.com/how-to/extending-openapi/), [OpenAPI Generator Python](https://openapi-generator.tech/docs/generators/python/), [TypeScript Fetch](https://openapi-generator.tech/docs/generators/typescript-fetch/).

## Migration and delivery

1. Export and validate the backend's public computer OpenAPI artifact. Trial the pinned generator on the actual schema. Inspect the cloud service's creation, execution, expiry, reconnection, and deletion contracts; define common result/error types and expiry defaults.
2. Implement the new Python `Computer` object and shared contract tests against both providers. Reuse local runtime internals where appropriate. Add any required supervisor/service work for expiry and persistence.
3. Rename Python imports, CLI entry points, user-facing documentation, examples, and release metadata. Keep CLI noun-verb organization under `celesto`. Inventory native packages, guest binaries, image artifacts, environment variables, installation paths, and saved state separately; do not blindly rewrite published asset names or discard existing disks.
4. Defer TypeScript and OpenMuse changes. Preserve the versioned OpenAPI artifact for a later TypeScript generator and facade; resource behavior must eventually agree across languages.
5. Update build/release workflows and publish verified packages through the existing package and GitHub release channels. No publication or release tagging is authorized by this design document. For image/guest-agent changes, complete the repository's image build, smoke, manifest, and SHA-pin checklist before tagging the package.

No compatibility package is planned. Publish migration instructions explaining new imports, commands, defaults, and how existing local resources can be inspected or removed. A clean API break does not authorize deleting user data.

## Verification criteria

- The cloud and local quickstarts pass the same behavioral tests.
- Defaults select cloud and ephemeral lifetime; missing credentials never trigger local fallback.
- Persistent context entry fails before allocation on a fresh handle.
- Normal context exit and exceptional exit delete ephemeral computers; cleanup failures remain visible and retryable.
- Killing the client demonstrates supervisor/service expiry independently of Python cleanup hooks.
- Persistent computers survive client exit and can be reconnected without duplicating them.
- Lost create/delete responses, command transport failures, expired resources, and repeated deletion have defined, tested outcomes.
- Cloud-only installation works without native VM dependencies. Installed-wheel and source-checkout local paths both pass smoke tests.

## Next implementation prerequisite

Implement a reproducible schema export from `CelestoAI/backend`, validate generated Python against it, and verify service lifetime/deletion guarantees before promising parity. Backend route/schema inspection is complete; no schema artifact has yet been exported and no SDK implementation has been changed.

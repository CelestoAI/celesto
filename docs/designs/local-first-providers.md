# Local-first computers

Celesto runs computers on your machine by default. Cloud execution is an explicit choice, and shared operations behave the same in either location.

## Implementation plan

1. Preserve the existing Computer lifecycle facade and extract provider-specific operations into local and cloud adapters behind a Protocol.
2. Default Computer and Computer.get to local; add fixed LocalComputer and CloudComputer entry points. Preserve explicit legacy local booleans, reject conflicting selectors, and never infer a provider from credentials or IDs.
3. Resolve local desktop session IDs as well as existing VM IDs. Reconnection never provisions a replacement or acquires cleanup ownership.
4. Add local-first computer create and terminal commands; select cloud explicitly for create, terminal, list, and delete. Preserve existing desktop start behavior and reject unsupported cloud actions explicitly.
5. Migrate cloud examples and tests to explicit selection, document the breaking default, and run lifecycle, transport, terminal, and CLI regression checks.

## Ownership and flow

```text
Computer / LocalComputer / CloudComputer
  -> validate selector and configuration
  -> provider adapter (no provisioning yet)
  -> context entry or first operation -> allocate and start
  -> shared cleanup policy -> provider deletion -> close connection

get(id) -> selected provider lookup -> persistent handle (no creation)
```

The facade owns lifetime, startup-failure cleanup, and retryable deletion. Adapters own readiness, identity mapping, capability checks, and transport. Existing local VM and generated cloud code are reused. No provider fallback, mutation replay, or global mutable provider setting is introduced.

## Verification

- Default and explicit local paths never construct a cloud client, even with credentials set.
- Cloud selection and fixed subclasses remain cloud-bound during reconnection.
- Conflicting selectors, unsupported capabilities, and invalid options fail before allocation.
- Existing context, cleanup failure, command streaming, and transport uncertainty tests pass.
- Desktop IDs resolve locally; browser IDs and missing IDs fail without cloud lookup.
- CLI default/explicit selection, terminal exit status, readiness, timeout, and handle closure are tested.
- Real local/cloud provisioning is a separate smoke check; mocked HTTP tests do not prove service availability.

## Not in scope

New file-transfer APIs, server expiry, generated-client changes, package splitting, release publication, and GitHub issue edits are separate work. Browser/display connections shipped upstream in #558 and are preserved through the provider contract.

## Implementation result

Implemented the shared facade, typed provider contract, local/cloud adapters,
typed specialized constructors, desktop reconnection, and CLI routing described
above. The existing cloud transport and local runtime remain in place. Both
fixed-provider classes preserve their provider and return their own type on get().

The CLI exposes cloud create/list/terminal/delete. Existing start/open/logs/templates
remain local operations and explicitly reject cloud selection. Cloud terminal
attachment does not report a remote shell exit code because the existing adapter
does not expose one. Cloud listing follows the API's default limit of 50.

Rebased onto origin/main at f64a00d (#558). Browser/display methods delegate
through the provider contract; local template preparation, capability probing,
connection locking, and forward cleanup are preserved. Upstream connection tests
now target the adapter boundary rather than the removed facade internals.

Verification: 631 focused SDK, generated-client, connection, terminal, and CLI tests passed;
one opt-in live-cloud test skipped. Ruff and strict mypy checks for the new provider
modules, SDK facade, and cloud CLI handler passed. The final run includes the
OpenClaw tests with the required filesystem access. One real-VM test was deselected;
real VM and billable cloud smoke tests were not run. A wheel build also passed.

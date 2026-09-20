# Published ports

An agent can share an HTTP application running inside its cloud computer with a public URL. It can inspect those routes and remove them without stopping the application.

Scope: the published-ports portion of [issue #552](https://github.com/CelestoAI/celesto/issues/552), M3.

## Contract

- `Computer.publish_port(port: int) -> PublishedPort`
- `Computer.published_ports() -> list[PublishedPort]`
- `Computer.unpublish_port(port: int) -> PublishedPort`
- Reject booleans, non-integers, and ports outside `1024..65535` before provisioning. The server owns reserved-port policy.
- Reject all three operations on local computers before starting a VM. Use `CelestoError` with an actionable cloud alternative.
- Valid cloud operations use existing deferred provisioning and deleted/failed-handle checks. Listing and unpublishing also provision a fresh handle; reconnect with `Computer.get(id)` to inspect an existing computer.
- Return a handwritten, immutable `PublishedPort` with `computer_id`, `port`, `status`, and optional `id`, `url`, `created_at`. Preserve the service's status string and timestamp string. Normalize missing metadata to `None`.
- Do not automatically retry requests. A lost mutation response has an uncertain outcome; callers should inspect routes before deciding whether to retry.
- Omit URLs from representations and do not expose arbitrary port error response bodies, validation inputs, or generated extra fields.

## What already exists

The committed OpenAPI snapshot and generated client contain all three endpoints and their request/response models. Reuse them unchanged. `_CloudComputer._call` supplies authentication, organization selection, public errors, and a single-request transport. `Computer._ensure_started` supplies lifecycle behavior. The backend lists active routes and treats removal of an absent route as successful.

## Architecture and test map

```text
Computer.publish_port / unpublish_port
  -> validate port -- invalid --> ValueError, no allocation
Computer.published_ports
  -> provider guard -- local --> CelestoError, no VM start
  -> existing lifecycle -- deleted/failed --> CelestoError, no replacement
  -> generated HTTP request (one attempt, organization header)
       -> transport failure --> sanitized CelestoError, no replay
       -> HTTP error --> CloudAPIError / missing computer --> VMNotFoundError
       -> malformed payload --> sanitized CelestoError
       -> normalize documented fields --> PublishedPort / list[PublishedPort]
```

Architecture: no new service, dependency, transport, or backend change. Code quality: one shared input validator and one response converter. Test coverage: public-facade tests use real generated clients over mocked HTTP; cover bounds, absent/null metadata, multiple/empty results, reconnection, local rejection, lifecycle guards, malformed payloads, HTTP errors, and uncertain outcomes. Performance: one request per operation after initial provisioning, linear conversion of list results, no cache that could hide route changes.

The opt-in live smoke starts a test HTTP application, publishes it, fetches its response through the public URL with bounded readiness polling, reconnects and lists routes, unpublishes, and deletes the computer. Live execution depends on configured credentials and the existing explicit opt-in.

## NOT in scope

- Interactive terminals, browser/display, file transfer, and expiry: separate capabilities in the epic.
- Local tunneling: the issue explicitly requires unsupported local publication to fail.
- Raw TCP/UDP forwarding: these backend routes publish HTTP applications.
- Backend policy duplication or OpenAPI regeneration changes: the existing API already supplies the contract.
- Package publication or release tags: not needed for implementing the capability.

## Implementation tasks

- [x] Add the public result type and three facade/cloud operations.
- [x] Cover success, validation, lifecycle, normalization, and failure paths with pytest.
- [x] Extend the opt-in live smoke and update cloud usage examples and SDK status.
- [x] Run focused SDK tests, lint, and generated-client drift verification.

Validation: the full suite passed 2,592 tests with 16 skipped and 50 deselected.
The focused published-port suite passed 161 tests with one existing e2e test
deselected. Ruff passed. `scripts/generate_cloud_client.sh` produced no
generated-client or schema diff. Live URL reachability remains unverified until
the billable smoke is enabled.

Sequential implementation, no parallelization opportunity. Remaining epic milestones are already tracked in #552; no additional TODO is needed.

## GSTACK REVIEW REPORT

| Review | Runs | Status | Findings |
| --- | --- | --- | --- |
| Architecture | 1 | Complete | Reuse generated transport and lifecycle |
| Code quality | 1 | Complete | Normalize optional fields and sanitize errors |
| Tests | 1 | Passed locally | Full suite: 2,592 passed; billable live smoke skipped |
| Performance | 1 | Complete | No polling or caching added to SDK operations |
| Outside voice | 0 | Skipped | Focused implementation using the existing architecture |

VERDICT: Published-port scope implemented and verified locally; live cloud verification remains opt-in.

NO UNRESOLVED DECISIONS

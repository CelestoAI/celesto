# Browser and display connections

Agents will be able to connect to the browser or watch the screen of the same computer where they run commands. The Python interface will work locally and in the cloud, with explicit errors when a computer does not support a browser or screen.

Status: Implemented in the working tree on 2026-09-20; not released. Full local/cloud scope approved by the user.
Issue: [Celesto #552, milestone M2](https://github.com/CelestoAI/celesto/issues/552).
Inspected SDK revision: `6cd1044`. Backend and previous SDK sources inspected from their default branches on 2026-09-20; recheck those contracts when implementing.

## Scope

Implement `Computer.browser()` and `Computer.display(mode=...)`, handwritten result types, cloud credential issuance, local attachment to the existing VM, enforced display modes, and connection tests/documentation. Cloud and local work share one public contract and one implementation PR. M2 is complete only after both providers pass acceptance tests.

Preserve deferred creation, current command behavior, existing local defaults, explicit reconnection, retryable deletion, and persistent ownership. Connection methods do not create a second VM, replace a stopped computer, change command users, or take ownership of attached resources.

## What already exists

| Existing component | Reuse and constraint |
|---|---|
| `src/celesto/sdk.py` | Owns creation, attach and deletion; new methods enter through this lifecycle. |
| `src/celesto/_cloud.py` | Generated HTTP calls, organization headers, safe errors; extend for connection issuance. |
| Generated browser/display endpoints and models | Both POST endpoints already exist in `openapi/cloud.json` and `_celesto_cloud_api`; no schema change required for the current wire shape. |
| Backend `v1/computers.py` | Checks template, image version, permissions and host protocol before minting a token. Cloud remains the authority. |
| `src/celesto/browser.py` | Image/config preparation, guest launch, readiness and local forwarding. Extract reusable pieces without reusing the factory's VM ownership. |
| `src/celesto/facade.py::expose_local()` | Loopback forwarding and cleanup. Respect existing network restrictions. |
| `src/celesto/images/builder.py` | Existing X server, Chromium, VNC and WebSocket bridge startup scripts. Extend their lifecycle instead of writing a new RFB proxy. |
| `src/celesto/images/published.py` | Published `linux-desktop` images across supported runtime/architecture combinations. |
| Existing TypeScript SDK connection mapper | Confirms gateway authentication uses an encoded `token` query parameter. Reference only; no TypeScript migration. |

Important findings:

- `Celesto.browser()` and `Celesto.computer()` are factories, not attachment methods. Calling them from an existing public `Computer` would allocate a different VM.
- The default cloud image name `ubuntu-desktop-24.04` is an alias for backend template `scratch`; it does not establish graphical capability. The cloud graphical template is `browser-agent`.
- Local startup currently uses writable `x11vnc` on port 5900 and websockify on 6080. There is no mode-specific enforcement in that path.
- Existing `start_session` calls `stop_session`. Reusing it on every connection request would restart Chromium and lose active work.
- Cloud `409` covers both unsupported templates and non-running computers. Status alone cannot justify an issuance retry.

## Public contract

```python
from datetime import datetime
from typing import Literal

class BrowserConnection:
    url: str
    expires_at: datetime | None

class DisplayConnection:
    url: str
    expires_at: datetime | None
    mode: Literal["read_only", "read_write"]

Computer.browser() -> BrowserConnection
Computer.display(
    *, mode: Literal["read_only", "read_write"] = "read_only"
) -> DisplayConnection
```

Implement immutable handwritten value types in `types.py`, exported from `celesto`. Prefer frozen dataclasses with `url=field(repr=False)`; generated responses never escape `_cloud.py`. These objects contain connection information, not an owned Playwright client or display session. They need no `close()` or context manager.

- `BrowserConnection.url` is a WebSocket address usable with Playwright `chromium.connect_over_cdp()`.
- `DisplayConnection.url` is an RFB-over-WebSocket address usable with noVNC. It is not an HTML viewer page. A hosted viewer is outside M2.
- Cloud expiry is the timezone-aware server timestamp, normalized to UTC. It describes credential validity for attachment; do not promise active sockets disconnect at that instant without gateway evidence.
- Local `expires_at=None` explicitly means there is no timed credential. Local access lasts only while the service and local forwarding remain available. Do not fabricate an expiry from a browser session timeout or implement a local token service solely for cosmetic parity.
- Each cloud call reauthorizes and obtains fresh connection data. Local calls probe/reuse services and rediscover addresses. No automatic background refresh or browser action replay.
- Validate `mode` before provisioning. Reject every value except the two strings, including `None` and booleans.
- Hide URLs from `repr`, `str`, logs and SDK exceptions. Explicit access to `.url` yields the credential-bearing string; document that callers must not log it. Avoid convenience serialization that emits credentials by default. Never include raw generated response representations or validation input in an exception.

Usage after implementation:

```python
from celesto import Computer

with Computer(template_id="browser-agent") as computer:
    browser = computer.browser()
    display = computer.display()  # read_only
    # playwright.chromium.connect_over_cdp(browser.url)
    # Pass display.url to a noVNC client.

with Computer(local=True, template_id="browser-agent") as computer:
    browser = computer.browser()
    display = computer.display(mode="read_write")
```

## Local provisioning and capability contract

Add local support for the existing cloud option `template_id="browser-agent"`, resolving to the published `linux-desktop` image. Consume this SDK option before binding/forwarding the remaining `Celesto` constructor arguments. Do not change the meaning of `Computer(local=True)` or silently install graphical packages in a plain VM.

Extract graphical VM configuration preparation from `_build_browser_vm_config()` into a shared helper usable by both legacy factories and `Computer`. The new route still constructs exactly one `Celesto`, uses the normal persisted sandbox ID, and calls the existing lifecycle. It must not create a `BrowserSessionInfo` row just to borrow graphical code.

Define a small explicit local template option matrix before coding: support backend, data directory, memory, disk size, networking, mounts and SSH options where the existing graphical runtime supports them. Validate incompatible `config`, `image`, `os`, unknown templates and unsupported cloud template versions before image preparation. Translate SDK `memory`/`disk_size` deliberately, enforce the desktop minimum disk size, and reject rather than drop options. Preserve caller-selected SSH/command identity; browser services continue using their existing desktop user.

The SDK bundles a standard-library-only guest helper and executes it through the existing command transport. Its versioned capability response probes the actual installed graphical tools for browser CDP, writable display and view-only display. Future image builds also include this same helper; existing published desktop images do not require republishing to use the SDK connections. Capabilities are verified against the actual guest, including after `Computer.get(id, local=True)`; constructor options and image filenames are not sufficient proof. Probe descriptors before starting services or opening forwards. Images missing the required tools receive an actionable error, not a silently writable read-only connection.

For an explicit desktop template, prepare/probe graphical capabilities during its initial startup so image incompatibility follows the existing startup-cleanup contract. For attached or custom computers, a connection failure leaves the VM and its commands available. Reconnection never requires remembering which constructor was originally used.

## Provider flow

```text
browser() / display(mode)
  |
  +-- validate arguments and deleted/failed-handle guards
  +-- lazy lifecycle: create once OR use the attached VM
  |
  +-- cloud
  |     GET current state -> bounded polling of transitional states
  |     POST browser/display once
  |       backend: organization + capability + version + permission checks
  |     validate response -> encoded WebSocket URL + UTC expiry
  |
  +-- local
        guest capability descriptor -> running-state check
        ensure only missing graphical services, without restarting healthy ones
        bounded service probes -> loopback-only forwarding
        CDP discovery / mode-specific display URL -> expiry None
```

Keep connection data-plane traffic outside the Python SDK: clients connect to the cloud gateway or local forward directly. Add no per-viewer SDK relay, database table, heartbeat or background refresh thread.

## Cloud implementation

1. Add `_CloudComputer.browser()` and `.display(mode=...)` using the existing generated `sync_detailed` calls and request enum. Preserve `x-current-organization` on every call.
2. Use fresh GET state for attached handles. Poll only explicit transitional states (`creating`, `starting`, `restoring`, `pending`) within one monotonic connection-readiness deadline. Do not auto-start `stopped`/`restorable` computers or recreate missing ones. A proposed private connection budget is 30 seconds, separate from initial VM provisioning; cap each request/sleep to remaining time and preserve the client's original timeout afterward.
3. Issue the connection POST at most once per public call. Treat 401/403/404/409/422/501 as final for that call. Surface 429/503 and transport failures without replaying issuance. A state change between GET and POST fails clearly; the caller can request a new connection explicitly.
4. Keep backend capability/version checks authoritative. Do not reproduce its version allowlists or add a template-catalog fetch on every call. An initial unsupported template may only be discoverable after allocation; retain the computer for commands and explicit cleanup.
5. Normalize responses through one private helper: require nonempty token and valid gateway URL; accept `wss` and explicitly local `ws` (normalize `https`/local `http` if returned); reject userinfo, fragments, malformed hosts, and preexisting token parameters. Preserve valid gateway paths/query parameters and add the encoded token with URL utilities. Never forward the API key to the gateway.
6. Parse timezone-aware expiry; reject malformed, naive, missing or already-expired timestamps without echoing input. Verify returned display mode equals the requested mode; fail closed on mismatch. Do not return a writable connection for a read-only request.
7. Translate connection failures to short, safe `CelestoError`/`CloudAPIError` messages. Preserve stable status codes. For a 409 while the computer is running, explain capability/readiness uncertainty without guessing from arbitrary response text. Do not weaken global response-body redaction to expose server details.

No backend/OpenAPI mutation is expected. If verification reveals a missing protocol/error contract, fix backend source first, export the snapshot and regenerate together; never hand-edit generated code.

## Local browser and display implementation

Place reusable attachment helpers in a private module such as `_connections.py`, with functional helpers rather than a second computer ownership class. The shared guest helper is `images/guest_connections.py`. Let `Computer` pass its existing `Celesto` runtime. Refactor legacy browser code only where reuse requires it, keeping existing public properties and factories intact.

**Browser:** Ensure an existing healthy Chromium instance is reused. Probe the guest CDP service, create/reuse a loopback forward, read bounded `/json/version` data, and validate `webSocketDebuggerUrl`. Rewrite its authority to the known local forwarded address while preserving the verified WebSocket path; never return a guest-internal address or follow a guest-supplied external endpoint. Rediscover after a browser restart. Launch a missing browser once through an idempotent guest helper; do not retry an ambiguous launch blindly or execute browser actions during connection issuance.

**Display:** Keep independent writable and view-only VNC services on the same X display. SDK-owned guest endpoints are 5902/6082 for writable VNC/WebSocket and 5901/6081 for view-only VNC/WebSocket. Legacy 5900/6080 listeners remain intact. Use `x11vnc -viewonly` for the view-only service and keep file-transfer extensions disabled. Its WebSocket bridge targets only the view-only VNC service. Simultaneous read-only and writable callers must not toggle a shared global mode.

This reuses native enforcement: [upstream x11vnc documentation](https://github.com/LibVNC/x11vnc/blob/master/doc/OPTIONS.md?plain=1) specifies that `-viewonly` discards client input. noVNC's `viewOnly` flag can improve UI behavior but is not the enforcement boundary.

Bind new guest listeners to loopback and forward through `expose_local(..., guest_loopback=True)` where supported. Keep host listeners on loopback. Explicitly reject runtime/network combinations that cannot provide this route; do not weaken network policy. Existing legacy forwarding behavior remains compatible. Local URLs are intended for clients on the same machine; this is not a tenant authorization boundary against a user who can run commands in that VM.

Extend the guest helper with capability probing and non-destructive `ensure` behavior, guarded by a guest-side lock so separate Python handles cannot launch competing services. Check process health and expected ports; port occupancy alone is not proof of the right service. Start only missing components. Never use the current destructive `start_session` as a reconnect operation. Keep new PID files, stop behavior, readiness and image smoke assertions together.

Cache only validated local forwarding resources owned by the current handle, keyed by capability/mode; never cache a browser WebSocket path across discovery calls. Repeated calls must not allocate unbounded forwards. Partial connection setup rolls back newly opened forwards while preserving prior connections and the VM. `delete()`/`close()` use existing forward cleanup and retain retryability. Separate handles must not close one another's forwards.

## Failure and test plan

The matrix below is the acceptance contract. Local end-to-end coverage is in `tests/e2e/test_computer_connections.py`; cloud live connection checks are opt-in through `CELESTO_LIVE_CONNECTION_TEST=1`.

```text
SDK entry                     Provider / transport                  User result
invalid mode -------------> no provisioning ---------------------> ValueError
deleted/failed handle ----> existing lifecycle guard -------------> safe error
fresh computer -----------> create once, then connect -----------> same computer ID [E2E]
attached computer --------> no create/start ----------------------> fresh connection [E2E]
cloud transitional -------> bounded GET polling -----------------> ready or timeout
cloud POST failure -------> zero issuance retries ---------------> safe status/error
bad URL/token/expiry -----> reject before returning object ------> no secret leakage
local capability missing -> no launch/forward --------------------> actionable error
local healthy services ---> reuse; do not stop session ----------> existing tabs survive [E2E]
local startup/port failure -> rollback only new resources --------> VM remains usable
display read_only --------> guest/gateway rejects input ----------> screen changes only by writer [E2E]
refresh/reconnect --------> reauthorize / rediscover --------------> fresh usable URL [E2E]
delete -------------------> VM and owned forwards cleaned --------> no usable connection [E2E]
```

| Layer / files | Required assertions |
|---|---|
| `tests/test_computer_sdk.py` | Both provider routes, default/invalid modes, laziness, post-delete guards, persistent contexts, attach without create, one VM ID across commands/browser/display; local option validation and no dropped settings. |
| New connection type/helper tests | Immutable handwritten types, URL encoding with special-character tokens, timezone parsing, malformed/expired results, exact mode match, redacted repr/str/logs/exception chains, no API key in connection URLs. |
| `tests/test_cloud_computer.py` | Exact endpoint/body/header, refreshed credentials, 401/403/404/409/422/429/501/503, transport/decode failures, one POST maximum, fake-clock deadline, request timeout restoration, changing/stopped/deleted states. |
| New local attachment tests | Capability absence/version mismatch, no second VM/session row, correct mode-specific forward, safe CDP authority rewrite, bounded probes, repeated requests reuse resources, partial rollback, separate-handle cleanup. |
| `tests/images/test_images.py` and focused helper tests | View-only arguments and independent endpoints, manifest version, PID/stop cleanup, lock/idempotent ensure behavior; legacy browser startup remains valid. |
| `tests/e2e/test_browser.py` or new connections E2E | Browser action and command observe the same file/desktop; tabs survive repeated requests; read-only keyboard, pointer and clipboard attempts do not mutate the desktop even with client-side protections disabled; writable positive control succeeds; both modes coexist. |
| Backend/gateway contract suite | READ can watch; WRITE required for control/browser; organization isolation; unsupported image/host rejected; real token handshake and rejected expired token; verify actual RFB mode enforcement. |
| `tests/test_cloud_live.py` | Opt-in browser-agent issuance, actual CDP attach, display handshake, reconnect via a second handle, fresh credential after expiry, cleanup in finally. Test active-session expiry separately only if promised by gateway contract. |
| Installed wheel | Run connections smoke outside the checkout; test cloud endpoints and supported local runtime from installed package. |

Every failure has a required explicit error and test above. No silent fallback from read-only to writable, cloud to local, or unsupported template to newly allocated desktop is allowed. Connection failure after successful provisioning does not mark the whole computer permanently failed.

## Implementation tasks and PR boundaries

The implementation is delivered in one PR, covering the originally planned T1–T3 boundaries.

- [x] **T1: shared types and cloud connections.** Public types, generated issuance calls, normalization, facade/cloud tests, and documentation implemented.
- [x] **T2: local image support.** Bundled guest helper, capability probes, locking, and independent view-only endpoints implemented and smoked with existing desktop images. Future image builds include the helper; release pins remain unchanged.
- [x] **T3: attach locally to the same VM.** Explicit graphical template routing, shared configuration, forwarding reuse, and local contract/E2E tests implemented.
- [ ] **T4: parity and release acceptance.** Source and installed-wheel local QEMU tests passed, including keyboard/mouse/clipboard enforcement and reconnect preservation. Live cloud validation is pending credentials. The opt-in cloud smoke covers CDP and the RFB handshake; cloud mode enforcement and expired-credential rejection still need live acceptance. Image/package release validation is outside this PR.

Suggested verification commands during implementation:

```sh
uv run pytest tests/test_computer_sdk.py tests/test_cloud_computer.py tests/test_generated_cloud_client.py
uv run ruff check .
bash scripts/generate_cloud_client.sh
git diff --exit-code -- src/_celesto_cloud_api
```

Add new focused connection/image tests to the command set as they land. Use the existing opt-in E2E backend matrix for local smoke and cloud live-test flag/cleanup workflow. A mocked issuance response alone does not satisfy live connection acceptance.

## Performance and lifecycle constraints

Cloud connection methods require bounded control-plane requests, not a data relay. Avoid template catalog N+1 calls and background token polling. Local warm connections should use bounded health/discovery probes and existing forwards; they must not download images, restart desktops or create per-call services. Measure warm versus cold latency in smoke tests and verify process/forward counts stay bounded across repeated calls.

A second VNC process adds CPU/memory overhead when displaying the same desktop; measure simultaneous read-only/write viewers on the minimum supported desktop configuration. Start mode-specific services lazily if needed, retaining readiness/mode guarantees. Bound HTTP discovery response size (for example 64 KiB), socket timeouts and total readiness time; do not multiply the deadline by the number of probes.

## NOT in scope

- M1 file transfer, M3 published ports/terminals, M4 server-enforced computer expiry: separate milestones; M2 connection expiry is not resource expiry.
- TypeScript/OpenMuse migration, optional dependency splitting, CLI redesign or changing existing default images.
- Browser action wrappers, automatic Playwright ownership, hosted viewer UI, local multi-user authentication, or transparent action replay.
- Publishing a package or tagging a release. The bundled helper supports existing desktop images; future image releases must follow the repository's build, smoke, manifest, and SHA-pin checklist.

## Rollback and acceptance

The legacy graphical APIs remain usable throughout. The combined connection implementation can be reverted before release. Pair any backend/schema change with its generated snapshot. Do not downgrade an already-running guest or delete user computers during rollback; older unsupported images receive clear connection errors.

M2 acceptance: both methods return the same handwritten shapes across providers; commands and connections address the same computer; read-only access rejects input at the service boundary; repeat calls and reconnect preserve existing work; credentials stay out of diagnostic surfaces; readiness ends within a bound; old lifecycle/streaming tests pass; source and installed-wheel paths pass; docs accurately distinguish local untimed URLs from cloud short-lived credentials.

## GSTACK REVIEW REPORT

| Review | Runs | Status | Findings |
|---|---:|---|---|
| Scope | 1 | Full M2 approved by user (A) | Consolidated implementation PR; live cloud acceptance pending. |
| Architecture | 1 | Proposed implementation documented | Same-VM ownership, explicit graphical template, independent mode enforcement, truthful local expiry. |
| Code quality | 1 | Requirements documented | Reuse guest/forwarding helpers; prevent destructive reconnect and credential-bearing errors. |
| Tests | 1 | Focused tests and local E2E passed | New branch/failure matrix plus real CDP/RFB and installed-wheel verification. |
| Performance | 1 | Constraints documented | One issuance POST, bounded probes, bounded local forwards/processes, measure dual-VNC overhead. |
| Outside voice | 1 | Independent code review completed | No blocking findings; live cloud mode/expiry acceptance remains pending. |

VERDICT: Implementation prepared, with focused SDK/runtime regression tests and real local QEMU connection checks. Local CDP attachment, same-VM file access, concurrent display modes, keyboard/mouse/clipboard enforcement and reconnect preservation passed. Live cloud checks remain unrun because credentials are unavailable. No package or image release was published, and release SHA pins remain unchanged; the bundled helper supports existing desktop images. This is not release clearance.

NO UNRESOLVED DECISIONS

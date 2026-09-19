# TODOs

## Celesto Python SDK roadmap

| Order | Work item | Outcome | Status |
| --- | --- | --- | --- |
| 1 | Installed-wheel cloud end-to-end test | Build the `smolvm` wheel, install it in a clean environment, and exercise create, run, reconnect, and delete against Celesto Cloud. | Complete |
| 2 | Lifecycle guarantees | Confirm and document what ephemeral and persistent computers guarantee during normal exit, errors, network loss, and process termination. | Next |
| 3 | Streaming commands | Expose command output as it arrives without changing the simple `run()` result API. | Planned |
| 4 | Browser and display | Add the cloud browser and display capabilities behind the public `Computer` API. | Planned |
| 5 | Terminal sessions | Add interactive cloud terminal sessions. | Planned |
| 6 | File operations | Add cloud file upload, download, and filesystem operations. | Planned |
| 7 | TypeScript SDK | Bring the unified API to TypeScript after the Python API is established. | Later |
| 8 | Automated OpenAPI synchronization | Automate backend schema export and generated-client updates after the manual workflow becomes painful. | Deferred |
| 9 | Cloud-only dependency split | Consider a smaller cloud-only installation only if native local dependencies become a real user problem. The local-first package and `smolvm-core` dependency are acceptable today. | Deferred indefinitely |

The committed cloud OpenAPI snapshot and generated Python client are intentionally
updated manually for now.

## OpenMuse

### Automate expandable trace UI flows

**What:** Add a focused Playwright suite for collapsed, expanded, running, approval-paused, failed, cancelled, reconnecting, and mobile trace states.

**Why:** This implementation adds server and reducer coverage plus a manual browser pass. Dedicated visual interaction coverage should follow without expanding the first release.

**Context:** The trace UI lives beside each user message and uses nested native disclosure controls. Cover keyboard operation, focus stability, reduced motion, and bounded payload scrolling.

**Effort:** M

**Priority:** P2

**Depends on:** Expandable OpenMuse agent traces.

## Completed

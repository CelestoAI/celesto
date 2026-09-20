# Celesto interactive terminal

Celesto should let a Python program open the same interactive terminal whether
the computer runs locally or in Celesto Cloud. The public API should hide the
different transports and keep cloud connection tokens out of logs and object
representations.

Status: implemented and validated
Date: 2026-09-19

## Capability contract

```python
from celesto import Computer

with Computer() as computer:
    terminal = computer.terminal()
    terminal.attach()
```

`Computer.terminal()` returns a public `TerminalConnection`. Calling
`TerminalConnection.attach()` connects the process's current stdin and stdout,
switches an interactive TTY to raw mode, forwards resize events, and blocks until
the shell exits or the caller detaches.

Cloud terminals are durable across an attachment ending. Their ID can be saved
and supplied to a later call:

```python
terminal = computer.terminal()
terminal_id = terminal.terminal_id
terminal.attach()

# Later, while both the same cloud computer and terminal session still exist:
computer.terminal(terminal_id=terminal_id).attach()
```

`terminal_id` is `None` for local terminals because the current local fast-shell
transport does not expose durable session IDs. Passing `terminal_id` to a local
computer fails before the computer is provisioned. `attach()` returns `None` in
both environments; a terminal attachment is not a command execution result.

Ctrl+] detaches from a cloud terminal without asking the remote shell to exit.
Local terminals retain their existing transport behavior and end when the local
attachment ends. This capability difference is explicit rather than simulated.

## What already exists

- `Celesto.attach_shell()` and
  `RustHttpVsockChannel.attach_terminal()` already provide bounded local terminal
  I/O, raw-mode restoration, resize handling, and an exit frame. Reuse them.
- The committed OpenAPI client already includes
  `POST /v1/computers/{computer_id}/terminals` and its generated request and
  response models. Use it only for the control-plane request.
- The cloud backend already mints a short-lived token and supports a caller-
  supplied terminal ID for reattachment. No backend change is required.
- The retired SDK repository contains a working synchronous WebSocket bridge.
  Reuse its proven wire behavior, but do not copy its habit of sending a remote
  `close` message whenever the client detaches.
- `websockets` is already used by optional dashboard installs and is present in
  the lockfile. Promote it to a direct dependency because the base public SDK will
  import it only when a cloud terminal is attached.

## Architecture

```text
Computer.terminal(terminal_id=None)
                 |
          validate before allocation
                 |
        +--------+---------+
        |                  |
      local               cloud
        |                  |
 ensure/start VM     ensure/start computer
        |                  |
 TerminalConnection   POST /terminals exactly once
 attach callback       validate response + gateway URL
        |                  |
 Celesto.attach_shell  TerminalConnection
                           |
                       attach callback
                           |
                  bounded WebSocket bridge
```

`TerminalConnection` is handwritten public API. It contains only safe public
metadata (`terminal_id` and `expires_at`) plus a private attachment callback.
The cloud token and authenticated URL stay inside that callback and are excluded
from `repr`. Generated OpenAPI models never cross the public boundary.

The WebSocket bridge belongs in `celesto._terminal`, not in generated code or the
top-level facade. It validates that the backend returned `wss://`; `ws://` is
accepted only for loopback development. It preserves existing non-token query
parameters, replaces any existing `token` parameter, and bounds inbound messages
and queued frames using the `websockets` client controls. The library's sync
client supplies opening, closing, ping, and pong handling.

The control-plane POST is not replayed after a transport error because creating a
terminal session has an ambiguous outcome. The WebSocket itself does not
auto-reconnect. A caller reconnects explicitly by asking for fresh credentials
with the known `terminal_id`.

## Attachment state and cleanup

```text
created -> connecting -> attached -> remote shell exits -> returned
              |             |
              |             +-- Ctrl+] -> detach -> returned
              |             +-- stdin EOF -> stop input, keep receiving
              |             +-- abnormal close -> CelestoError
              +-- handshake failure -> CelestoError

always: restore TTY attributes, restore SIGWINCH handler, close WebSocket
```

Only the main thread may install `SIGWINCH`; attachment from another thread still
works without resize signals. A receiver thread owns WebSocket reads while the
calling thread owns stdin reads and WebSocket writes. At most one thread receives,
matching the `websockets` concurrency contract.

## Validation and user-facing failures

- `terminal_id` must match the backend's documented `term_...` format and length.
- Invalid IDs and local reattachment fail before provisioning or network calls.
- Missing stdin file descriptors produce a short error explaining that a real
  terminal or pipe is required.
- Invalid response fields, expiry timestamps, and gateway URLs produce a bounded
  `CelestoError` without including response bodies or tokens.
- Text frames are always treated as terminal output because shell output and
  gateway errors share the same wire representation in the current protocol.
- Abnormal WebSocket closure reports that the attachment ended unexpectedly and
  tells the caller to attach again. Normal closure and deliberate detach return.
- Terminal attributes and signal handlers are restored on every exit path.

## Test plan

Pytest is the repository's authoritative test framework. Unit tests cover the
transport deterministically with pipes and a fake WebSocket. The live cloud test
uses a child process with piped stdin and stdout to verify real gateway I/O without
requiring a human TTY.

```text
CODE PATHS                                      USER FLOWS
[+] Computer.terminal()                         [+] New local terminal
  +-- invalid ID -> ValueError, no allocation     +-- create -> attach -> restore TTY
  +-- local + ID -> ValueError, no allocation   [+] New cloud terminal [->E2E]
  +-- local -> safe connection                    +-- POST -> attach -> input/output
  +-- cloud -> POST exactly once                  +-- Ctrl+] -> detach, shell retained
      +-- valid response -> safe connection     [+] Cloud reattachment [->E2E]
      +-- bad response/URL -> CelestoError        +-- same ID -> fresh token -> attach

[+] TerminalConnection.attach()
  +-- initial resize + stdin/output forwarding
  +-- text and binary output
  +-- resize signal
  +-- stdin EOF keeps receiving / Ctrl+] cleanly detaches
  +-- normal remote close
  +-- abnormal close -> CelestoError
  +-- handshake failure -> CelestoError
  +-- every path restores TTY and signal state

COVERAGE TARGET: all branches unit-tested; one live gateway and shell I/O smoke
```

Specific tests:

- `tests/test_computer_sdk.py`: local lifecycle, safe public connection, attach
  delegation, and rejection before allocation.
- `tests/test_cloud_computer.py`: generated endpoint path/body/org header, new and
  reattached IDs, non-replay on transport failure, response validation, and no
  token in public `repr`.
- `tests/test_terminal.py`: authenticated URL construction, URL rejection, input,
  output, resize, detach, abnormal closure, and cleanup.
- `tests/test_cloud_live.py`: create and reauthorize a terminal session, attach
  through the real gateway, run a shell command, and verify its output without
  printing credentials.

## Failure modes

| Failure | Test | Handling | User result |
| --- | --- | --- | --- |
| Control-plane request times out after dispatch | Unit | No replay | Explicit ambiguous-outcome error |
| Backend returns an unsafe URL or malformed expiry | Unit | Reject before connect | Explicit version/response error |
| Token expires before WebSocket attach | Unit handshake failure | Close and restore local state | Explicit attach-again error |
| Gateway sends an oversized frame | Unit | `max_size` closes connection | Explicit unexpected-end error |
| Shell prints JSON shaped like a gateway error | Unit | Preserve it as terminal output | No false detach |
| Terminal is attached from a worker thread | Unit | Skip signal installation | I/O works; no resize signals |
| Receiver and stdin finish concurrently | Unit | Idempotent event and close | Clean return without leaked thread |
| User detaches cloud terminal | Unit | Close socket without remote close frame | Later reattachment remains possible |

There are no silent, untested failure modes in the planned public path.

## Implementation tasks

- [x] Add the public `TerminalConnection` and the private bounded WebSocket bridge.
- [x] Add cloud session creation through the generated endpoint with validation
  and secret-safe wrapping.
- [x] Add `Computer.terminal()` and route local and cloud providers through the
  same public return type.
- [x] Promote `websockets` to a direct dependency and update the lockfile.
- [x] Add unit and live control-plane tests, then run focused tests, the full
  non-E2E suite, Ruff, mypy, and a wheel-content/import smoke.
- [x] Document the public API and mark the terminal roadmap item complete.

Sequential implementation, no parallelization opportunity: the public type,
provider adapters, tests, and documentation all share the same Python SDK contract.

## NOT in scope

- Browser/display APIs: separate roadmap capability with different protocols.
- File operations: unrelated to terminal transport.
- TypeScript and OpenMuse: intentionally follow the established Python API later.
- Automatic reconnection: risks replaying input and hiding session state; callers
  reauthorize explicitly with `terminal_id`.
- Async terminal API: the current public `Computer` API is synchronous.
- A generic public raw-WebSocket descriptor: it would leak provider details and
  force local callers into a cloud-shaped abstraction.
- Backend or gateway changes: the required endpoint and protocol already exist.
- A new package or artifact: this ships in the existing `smolvm` distribution's
  `celesto` namespace and existing wheel workflow.

## Review findings

- Scope challenge: accepted as a focused Python SDK capability. Existing local,
  generated HTTP, and prior cloud terminal code cover most of the work.
- Architecture review: no open issue after keeping the token private, making cloud
  detach non-destructive, and rejecting automatic reconnect.
- Code-quality review: no open issue after isolating terminal I/O in one private
  module and keeping generated models private.
- Test review: the coverage map above requires every new branch plus a live
  control-plane smoke; no deferred gaps.
- Performance review: no database or CPU-heavy path. Explicit WebSocket message and
  queue bounds prevent unbounded buffering.
- TODO review: no new deferred item. This implements the existing terminal roadmap
  row; async and raw transport APIs are explicit non-goals rather than TODOs.
- Retrospective: recent cloud command streaming work established bounded parsing,
  no-replay behavior, public wrapper types, and installed-wheel validation; this
  plan applies the same boundaries.

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | — | Nested pass skipped inside Codex |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | CLEAR | 0 issues, 0 critical gaps |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | — | Not applicable to the Python terminal transport |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

**VERDICT:** ENG CLEARED — ready to implement.

NO UNRESOLVED DECISIONS

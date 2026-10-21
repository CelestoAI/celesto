# Sandbox credential injection: build interfaces

Contract between the parallel workstreams that build
[sandbox-credential-injection.md](sandbox-credential-injection.md). The
decision log wins over this file; if they disagree, stop and report.

After #677 removed presets, W2's preset parts and all of W5 were dropped
(D-20, D-22). The rows below are marked; the plan module stays for user
secrets.

Shared Python types live in `src/celesto/credentials/types.py` (committed with
this file). Change them only by agreement; add fields with defaults.

## Workstreams and file ownership

| WS | Owns | Decisions |
|---|---|---|
| W1 proxy | `celesto-core/src/credential_proxy/**`, `celesto-core/Cargo.toml`, `celesto-core/python/celesto_core/credential_proxy.py`, registration in `celesto-core/src/python.rs` | D-05 (lock 2), D-08, D-14 (CA), D-16 (panic isolation), D-18 (log), D-19 (header rules) |
| W2 plan (presets removed) | `src/celesto/credentials/{plan,store,migrate}.py` | D-09, D-20, D-21 |
| W3 runtime | `src/celesto/runtime/_credential_proxy.py` (launcher), `src/celesto/credentials/runtime.py`, `src/celesto/credentials/guest.py`, backend forwards (`runtime/qemu_args.py`, `runtime/qemu.py`, `runtime/_libkrun_launcher.py`, `host/network.py`), lifecycle in `vm.py`/`facade.py` start/stop, `sandbox info/list` status, `sandbox logs --credentials` | D-04, D-05 (lock 1, lifecycle), D-07, D-14 (guest install), D-15 (control socket), D-16 |
| W4 user secrets | `src/celesto/credentials/{user_secrets,detect}.py`, `sandbox secret set/remove/list`, `env set` refusal, SDK `secrets=`/`not_secret=`, TS SDK, `server/app.py` exec env check | D-11, D-12, D-15 (CLI), D-18 (`secret list`) |
| W5 logins (removed) | none | D-22 |
| W6 SSH | `src/celesto/credentials/ssh.py`, `sandbox ssh-key add/remove/list`, git `insteadOf` in guest | D-13 |

Shared files touched by several streams (`cli/commands/app.py`, `facade.py`,
`types.py`, `cli/_sqlite.py`, storage protocol): keep edits small and
additive so the merge stays mechanical.

## W1 → everyone: `celesto_core.credential_proxy`

```python
class CredentialProxy:
    def __init__(self, *, listen: str, log_path: str) -> None:
        ...
        # listen: "unix:/abs/path.sock" (required support) or "tcp:127.0.0.1:0"

    def start(self) -> dict:
        ...
        # -> {"address": str, "ca_cert_pem": str}; generates a fresh CA in memory

    def set_bindings(self, bindings: list[dict]) -> None:
        ...
        # replaces all; dict = Binding fields minus `source` (see types.py)

    def set_local_routes(self, routes: list[dict]) -> None:
        ...
        # dict = LocalRoute fields

    def set_resolver(self, fn: Callable[[str], str | None]) -> None:
        ...
        # called with Binding.name at injection time; None = do not inject

    def set_local_handler(
        self,
        handler_id: str,
        fn: Callable[
            [str, str, list[tuple[str, str]], bytes],  # method, path, headers, body
            tuple[int, list[tuple[str, str]], bytes],
        ],
    ) -> None: ...
    def stats(self) -> dict: ...  # {"connections": int, "last_used": {name: iso8601}}
    def stop(self) -> None: ...
```

Behavior:

- The guest connects as if to the real host on port 443 (TLS). Read SNI. If
  SNI is a host of some binding or local route, terminate TLS with a leaf
  minted from the in-memory CA; otherwise close the connection.
- Require HTTP `Host` (or `:authority`) to equal SNI; otherwise 421, logged.
- For each binding whose `hosts` contains the host, for each `HeaderRule`:
  if the header carries the exact placeholder in that form, replace it with
  `resolver(name)`. `bearer`: `Bearer <ph>`; `raw`: `<ph>`;
  `basic_password`: Basic, decode, password == `<ph>`, re-encode.
  Never touch body or query. Never overwrite a header that lacks the
  placeholder. Resolver `None` leaves the placeholder (upstream rejects).
- A placeholder of any binding seen on a host not bound to it: forward
  unchanged and log a `refuse` event.
- Local routes: call the handler; never forward upstream.
- Upstream: resolve and connect from the host with standard roots; stream
  responses (SSE) without buffering; support WebSocket Upgrade (inject on the
  Upgrade request, then pipe bytes); offer ALPN `h2` and `http/1.1`.
- Log JSON lines to `log_path`: `{"ts","event":"inject|refuse|local|error", "name","host","method","path","status"}`. Never log values or placeholders.
- A panic in one connection must not kill the process.
- Must build and run on macOS and Linux.

## W3 → W2/W4/W5/W6: `celesto.credentials.runtime`

```python
def attach(vm, plan: CredentialPlan) -> ProxyHandle:
    ...
    # starts the per-VM launcher (python -m celesto.runtime._credential_proxy),
    # sets up the backend forward, installs CA + /etc/hosts block + managed env
    # placeholders + plan.guest_files in the guest. Raises CredentialsUnsupported
    # on bridge mode (caller prints the D-07 message).


def detach(sandbox_id: str) -> None: ...
def control(sandbox_id: str, op: str, **kw) -> dict:
    ...
    # ops: "status", "set_binding"(binding: dict, real_value: str),
    #      "remove_binding"(name: str)


def status(sandbox_id: str) -> ProxyStatus: ...
```

- Launcher reads a `LaunchSpec` JSON on stdin (never argv/env):
  `{sandbox_id, listen, log_path, control_socket, vm_pid, bindings, local_routes, real_values}`; prints one JSON line
  `{"address", "ca_cert_pem"}` on stdout; serves the control socket
  (Unix, 0600); exits when `vm_pid` exits. It calls
  `celesto.credentials.ssh.serve(spec)` (W6) if that module exposes it.
- QEMU slirp forward: guest `10.0.2.100:443` → the proxy's Unix socket
  (e.g. `guestfwd=tcp:10.0.2.100:443-cmd:<relay to unix socket>`). Do not
  listen on host TCP loopback: slirp guests reach it via `10.0.2.2`.
- Guest `/etc/hosts` managed block maps every bound and local-route host to
  the proxy address (IPv4 and IPv6 or no IPv6 route).

## W2: `celesto.credentials.plan`

```python
def build_plan(sandbox_id: str, state, env=None) -> CredentialPlan: ...
```

Built from `user_secrets.plan_for(sandbox_id)` (W4) only (D-20). Each
secret keeps its own stored placeholder; real values are re-read every call.
`credentials.store` keeps only the credential-protection version, which
gates the one-time cleanup in `credentials.migrate` (D-21).

## W4: `celesto.credentials.user_secrets` / `detect`

```python
def plan_for(sandbox_id: str, state) -> tuple[list[Binding], dict[str, str], list[str]]:
    ...
    # bindings, guest_env, missing-warnings; real values via resolve()


def looks_like_secret(name: str, value: str) -> bool: ...
```

## W5: removed

Subscription logins are out of scope (D-22); `credentials/logins.py` and the
launcher's login hook are gone.

## W6: `celesto.credentials.ssh`

```python
def guest_git_config() -> str: ...  # insteadOf block for the guest
def serve(spec: dict) -> None: ...  # filtered agent for allowed keys
```

## Rules for every stream

- Follow `CLAUDE.md`/`AGENTS.md`: E2E-first tests with an artifact; isolated
  tests only with a written failure-mode list first; user-facing errors per
  the Errors and warnings rules.
- Commit on your own branch; each message ends with `Decisions: D-xx, ...`.
  No `Co-Authored-By` lines. Do not push.
- Never put a real secret value in argv, env of child processes, logs, the
  state DB, or the guest.
- VMs you boot for tests: name them `w<N>-…` and delete them when done.

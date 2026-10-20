# Sandbox credential injection

Status: building
Acceptance target: local stack on the user's Mac — QEMU slirp and libkrun
(`uv run celesto codex start`, `uv run celesto claude-code start`). Linux
backends (Firecracker, QEMU TAP, bridge) are deferred until a Linux host is
available; their acceptance items are marked not run.

## Context

Celesto presets copy credentials into the guest: an allowlist of API-key env
vars per preset (`presets/_install.py:56`) written to a world-readable
`/etc/profile.d/celesto_env.sh`, login files (`~/.codex/auth.json`,
`~/.claude/.credentials.json` from the Keychain), GitHub tokens
(`~/.git-credentials`, `~/.config/gh`), and the whole `~/.ssh` directory
including private keys (`presets/_git.py:37`). User env (`sandbox env set`,
SDK `env_vars`, TS `exec` env) also lands in plaintext. A prompt-injected agent
can read and exfiltrate all of it, which defeats the point of a sandbox.

Most sandbox providers now keep real secrets in a proxy outside the sandbox
and give the guest placeholders. See
[sandbox-credential-injection-research.md](sandbox-credential-injection-research.md).

Non-goals: outbound allowlists, cloud computers (D-06), macOS and Windows
guests, AWS credentials (D-02), stopping an agent from *using* a credential
against its bound host (D-01).

## Decisions

### D-01: Real secret values never enter the sandbox

- Why: A compromised agent must not be able to steal a credential. The guest
  holds only a placeholder; a host-side proxy swaps in the real value only on
  requests to the secret's bound destination host.
- Rejected: Allowlist-only env copying — the secret is still readable inside
  the guest once passed. Egress allowlisting as part of this feature — separate
  decision; brings its own UX cost (package installs, browsing).
- Non-goal: Preventing the agent from *using* a credential against its bound
  host, and preventing exfiltration of non-secret data such as files.
- Implementation: Enforced by D-04, D-05, D-11–D-14; no single code site.
- Tests: E2E secret-scan test: start each preset with known sentinel real
  values on the host, then search the whole guest (env of every process,
  `/etc`, `/root`, `/home`, `/tmp`, process argv) for each real value; expect
  zero hits. Artifact: scan report JSON.
- Acceptance: A-08

### D-02: Protect API keys, subscription logins, GitHub HTTPS tokens, and SSH keys

- Scope: everything the presets copy into the guest today
  (`src/celesto/presets/*.py`, `presets/_git.py:37`).
  - API keys in env vars (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`,
    `OPENROUTER_API_KEY`, `GOOGLE_API_KEY`, `GEMINI_API_KEY`, `HF_TOKEN`):
    placeholder swapped in a request header (hosts in D-19).
  - Subscription logins (`~/.codex/auth.json`, `~/.claude/.credentials.json`
    or the Keychain item, opencode/pi auth files): placeholder tokens; the host
    owns refresh (D-10).
  - GitHub over HTTPS (`~/.git-credentials`, `~/.config/gh`): placeholder
    swapped for GitHub hosts only.
  - SSH keys: stop copying private keys from `~/.ssh`; D-13 replaces them.
  - OpenClaw gateway token: not copied; see D-19.
  - AWS keys: removed from the opencode preset (`presets/opencode.py:33-36`).
    Under D-11/D-12 they cannot be passed into a sandbox at all; opencode on
    Bedrock is unsupported until AWS signing support exists.
- Rejected: AWS SigV4 re-signing at the proxy, or host-minted STS
  credentials — each is a project of its own, used only by opencode on Bedrock.
  Shipping API keys first and logins later — most Codex and Claude Code users
  sign in with a subscription and would stay exposed.
- Implementation: Each `Preset` (`presets/_types.py:151`) gains a credential
  spec (name, source, bound hosts, injection form) replacing raw
  `host_env_vars` copying and credential entries in its file-copy lists;
  `apply_preset` (`presets/_install.py:83`) writes placeholders instead of
  values; `GIT_HOST_CONFIGS` drops `~/.ssh` private keys,
  `~/.git-credentials`, and `~/.config/gh/hosts.yml` tokens (configs without
  secrets still copy).
- Tests: The D-01 secret-scan E2E runs for codex, claude-code, opencode, pi,
  hermes, and openclaw.
- Acceptance: A-01, A-02, A-08

### D-03: Ship as one release

- Why: The "secrets never enter the sandbox" promise holds on the day it ships.
- Rejected: Two releases (keys/GitHub/SSH, then logins) — would advertise
  protection most users don't yet have.
- Implementation: One Celesto release, preceded by the `celesto-core` release
  that carries the proxy (D-08) and an image release if guest changes need it.

### D-04: Route only secret hosts to the proxy, via guest `/etc/hosts`

- Why: Every guest process follows `/etc/hosts` however it was started (login
  shell, raw exec, SDK exec, browser). Non-secret traffic is untouched, so a
  proxy failure breaks only the secret hosts. Bypassing the redirect leaks
  nothing: the request carries only the placeholder and fails auth. The proxy
  learns the destination from TLS SNI, requires the HTTP `Host` to match it,
  and resolves the real address on the host itself.
- Per-backend plumbing: guest port 443 on the proxy address must reach this
  VM's proxy — QEMU slirp `guestfwd` (`runtime/qemu_args.py:248`), an nftables
  DNAT rule scoped to the VM's TAP on Firecracker / QEMU TAP, a gvproxy
  forward on libkrun.
- IPv6: `/etc/hosts` gets an entry for both families (or the guest has no
  IPv6 route), so an AAAA lookup cannot skip the redirect.
- Rejected: `HTTPS_PROXY` env vars — processes started without the login
  profile (raw/SDK exec, `guest-agent/src/exec.rs:52`) skip it, and all other
  traffic would depend on the proxy. Capturing all port-443 traffic — every
  connection depends on the proxy, and QEMU slirp cannot do it without
  turning off normal internet.
- Limit: exact host names only; wildcard hosts would need a guest DNS server.
- Implementation: A managed block in guest `/etc/hosts` written by the guest
  agent (new route beside `/env/managed`, `guest-agent/src/handler.rs:57`) and
  the SSH fallback; per-backend forward in `runtime/qemu_args.py`,
  `host/network.py` (nftables), and `runtime/_libkrun_launcher.py` (gvproxy).
- Tests: E2E per backend: `curl https://api.openai.com/v1/models` with the
  placeholder from a raw exec (no login shell) succeeds; the same from a
  process that ignores `/etc/hosts` (resolve real IP, `--resolve`) returns
  401 and the real key never leaves the host. `curl https://pypi.org` works
  with the proxy stopped.
- Acceptance: A-03

### D-05: One proxy process per VM

- Why: Each proxy holds only its own VM's secrets, so one sandbox can never
  use another's key through it, and a crash, flood, or memory-disclosure bug
  affects one VM. Lifecycle matches gvproxy on libkrun: starts and stops with
  the VM.
- Two locks against cross-VM use:
  1. Network path: each VM's forward reaches only its own proxy (per-TAP
     nftables rule; per-VM QEMU or gvproxy forward). Proxy listeners bind
     where other guests cannot reach them (e.g. a Unix socket or a loopback
     port not reachable through slirp's host alias).
  1. Placeholder as capability: each sandbox gets random placeholders, and the
     proxy injects only on an exact match — never overwrites a header blindly.
- Placeholders are not secret on their own; they are stored with the sandbox
  in the host state DB so guest files stay valid across restarts.
- Rejected: One shared proxy per host — misattribution means one sandbox uses
  another's key, one process holds every secret, one crash affects all.
- Cloud direction (not built here, see D-06): the same model fits cloud pool
  hosts (≤ ~32 VMs per 64 GiB host, ≤ ~300 MB of proxies). Cloud placement
  reserves no per-VM memory overhead today (backend `pool_capacity.py`); the
  cloud design should add a fixed reserve covering QEMU and proxy.
- Implementation: Proxy launch and teardown hooked into `vm.start()` / stop
  in `vm.py` for every supported backend; per-VM state (proxy PID, socket,
  placeholders) in the state DB (`cli/_sqlite.py`).
- Tests: E2E: two sandboxes on one host, A with a real key and B without;
  B connects to A's proxy endpoint and sends A's placeholder; expect no
  injection and a refusal logged. Isolated Rust tests (see D-08).
- Acceptance: none — covered by the two-sandbox E2E test

### D-06: Local only; cloud integration is designed later

- Why: Keeps this release to the Celesto repo. Cloud needs its own design in
  the backend repo: an API to attach secrets to a computer, encrypting the
  vault by default (`encrypt=False` today), host delivery that avoids the
  stateful-broker failure that caused a three-week git outage, moving the
  GitHub git-credential broker (which hands the raw token to the guest)
  behind the proxy, a cloud image change, and a fleet rollout.
- Rejected: Shipping a cloud-ready library API now — deferred with the rest of
  the cloud design. Shipping Celesto and backend together — one release
  across two repos, an API change, an image change, and a fleet rollout.

### D-07: Support every NAT backend; fail closed on bridge mode

- Supported: QEMU slirp (macOS default), Firecracker (Linux default), QEMU
  TAP, libkrun with gvproxy on macOS. Each gets a per-VM forward from the
  guest proxy address on port 443 to its own proxy (D-04, D-05).
- Bridge mode (`NetworkSettings.mode="bridge"`, `types.py:573`) has no
  Celesto NAT to hook into. The sandbox still starts, but credentials are
  not delivered, and the user sees a message with a recovery command.
- Why: Covers both platform defaults and every NAT mode. Falling back to
  copying real values would make D-01 meaningless.
- Rejected: Copying real secrets on unsupported backends with a warning.
- Implementation: Backend capability check before credential setup in the
  preset start path (`cli/main.py:1886`, `:2046`) and `Celesto` facade.
- Tests: E2E: `celesto codex start --network bridge` (Linux) starts, prints
  the message, and the D-01 scan finds no real values.
- Acceptance: A-03, A-04

### D-08: Write the proxy in Rust inside `celesto-core`, run as its own process per VM

- Why: It parses untrusted guest traffic and holds real secrets, so it should
  sit on proven libraries (hyper, rustls, rcgen) rather than hand-written
  HTTP parsing. Mature streaming, WebSocket, and HTTP/2 support. ~5–10 MB per
  VM. `celesto-core` already ships Rust with tokio as a PyO3 wheel.
- Launch: a per-VM child process (`python -m celesto.runtime.<module>`, the
  same pattern as `runtime/_libkrun_launcher.py`) that runs the Rust proxy.
- Rejected: Python asyncio + `ssl` — hand-written HTTP/1.1 parsing on an
  attack surface, heavier per VM.
- Release: requires a `celesto-core` release before the Celesto release.
- Implementation: New `celesto-core/src/credential_proxy/` module exposed via
  PyO3; launcher `src/celesto/runtime/_credential_proxy.py`.
- Tests: Isolated Rust tests, justified by failure modes the E2E tests cannot
  reach cheaply. Failure modes: (1) inject for a host not bound to the secret;
  (2) inject when the request lacks the exact placeholder; (3) inject into
  body or query; (4) SNI and `Host` disagree (domain fronting); (5) Basic auth
  decode/re-encode wrong or applied to the wrong header; (6) placeholder split
  across headers or repeated; (7) WebSocket Upgrade not injected; (8) SSE
  buffered instead of streamed; (9) real value written to the log; (10) panic
  in one connection kills the process.
- Acceptance: covered by A-01–A-03

### D-09: Re-read real secrets from their source on every sandbox start; store nothing

- Sources: env vars of the command that starts the sandbox, `~/.codex/auth.json`,
  the macOS Keychain item Claude Code uses, `~/.claude/.credentials.json`,
  opencode/pi auth files, `~/.git-credentials`, `~/.config/gh`, and the
  host SSH agent.
- Why: No new place for secrets to leak from; rotated keys take effect on the
  next start; logins stay consistent with the host's own login.
- A credential missing at start is not injected, and the start prints a
  warning naming the variable, the sandbox, and the recovery command, e.g.
  `OPENAI_API_KEY isn't set in this terminal, so Codex in my-codex can't use it. Set it, then run 'celesto sandbox stop my-codex' and 'celesto sandbox start my-codex'.`
- Rejected: Snapshotting into the Keychain or a 0600 file at creation — an
  extra long-lived copy (plaintext on Linux), stale after rotation, and it
  forks the login from the host's.
- Implementation: Credential resolution runs at every start (preset start,
  `celesto sandbox start`, SDK `start()`), reusing the readers in
  `presets/_install.py` (env, files, Keychain at `:468`), and hands values to
  the proxy over its private channel only. `VMConfig.env_vars` no longer
  persists secret values in SQLite (`cli/_sqlite.py:261`).
- Tests: E2E: start with key K1, stop, change host env to K2, start; upstream
  stub sees K2. Start without the env var; the warning text matches and no
  injection happens.
- Acceptance: none — covered by E2E tests

### D-10: The proxy owns login refresh and writes new tokens back to the host's login

- Applies to: Codex ChatGPT login (`~/.codex/auth.json`, refresh at
  `auth.openai.com/oauth/token`) and Claude Pro/Max (macOS Keychain item or
  `~/.claude/.credentials.json`, refresh at `platform.claude.com/v1/oauth/token`).
- How: before refreshing, re-read the host source; if the host CLI already
  refreshed, use those tokens. Otherwise refresh upstream and write the new
  tokens back atomically, so the host CLI stays logged in. Both services
  rotate refresh tokens; a reused token fails (`refresh_token_reused`) or
  wipes the login.
- Guest side: placeholder tokens are shaped like the real ones — Codex
  `id_token`/`access_token` are unsigned JWTs with the same claims (email,
  plan, account ID) and a far-future `exp`; Claude tokens keep their
  `sk-ant-oat01-` / `sk-ant-ort01-` prefixes with a far-future `expiresAt`.
  A guest refresh call is answered by the proxy with the same placeholders
  and never forwarded upstream.
- Why: Long-running agents keep working, and the host CLI is never logged out.
- Rejected: Read-only, never refresh — agents stop when the token expires
  unless the user runs the CLI on the host. A separate sandbox-only login —
  extra login step and a second stored login (conflicts with D-09).
- Risk: writing the Keychain item may prompt the user once; confirm in
  acceptance.
- Implementation: Placeholder builders per login type in Python; refresh
  logic and host write-back in the proxy (file write with rename; Keychain
  via `security add-generic-password -U`).
- Tests: E2E with real logins on the acceptance machine (A-08). Isolated test
  for the refresh race: host CLI refreshes between the proxy's read and
  refresh — the proxy must use the host's new token, not refresh again.
- Acceptance: A-05

### D-11: No secret of any kind enters the sandbox; user secrets are host-bound

- Principle: every secret a user gives Celesto — preset credentials (D-02) or
  their own — stays on the host. The guest only ever sees placeholders.
- User secrets: a first-class, host-bound secret.
  - CLI: `celesto sandbox secret set <sandbox> STRIPE_KEY --host api.stripe.com`.
    The value comes from the host env var of the same name or a prompt,
    never from the command line.
  - Python SDK: `secrets={"STRIPE_KEY": Secret(host="api.stripe.com")}`;
    TS SDK equivalent.
  - The proxy injects the real value into request headers for that host only.
  - Per D-09, a secret is defined by its source (an env var name), not a
    stored value, and is re-read on every start.
- Consequence: a secret that cannot be injected into an HTTPS header (for
  example a database password over the Postgres protocol, or AWS SigV4) cannot
  be used inside the sandbox.
- Rejected: Presets only, with a docs note that `env set` values are visible —
  leaves users' own secrets exposed.
- Implementation: `celesto sandbox secret set|remove|list` beside
  `sandbox env` (`cli/commands/app.py:1549`); `Secret` type and `secrets`
  field on `VMConfig` (`types.py:711`); TS SDK option in `ts/src/types.ts`.
- Tests: E2E: `secret set` with a stub upstream at a bound test host;
  the guest sees a placeholder and the stub receives the real value.
- Acceptance: none — covered by E2E tests

### D-12: Refuse secret-looking values on the plain env paths

- Paths: `celesto sandbox env set`, SDK `VMConfig.env_vars` and
  `Celesto.browser/desktop(env_vars=…)`, TS SDK `exec(cmd, {env})`.
- Detection: names matching `*_KEY`, `*_TOKEN`, `*_SECRET`, `*PASSWORD*`,
  `*CREDENTIAL*`; values shaped like known secrets (`sk-`, `ghp_`,
  `github_pat_`, `xox…`, `AKIA…`, JWTs).
- Error, e.g.: `OPENAI_API_KEY looks like a secret, so Celesto won't place it inside the sandbox. Run 'celesto sandbox secret set my-sbx OPENAI_API_KEY --host api.openai.com' instead.`
- Escape hatch for false positives: CLI `--not-secret NAME`; SDK
  `not_secret=["NAME"]`.
- Why: Enforces D-11 where people make the mistake; the error teaches the
  right command. Detection is best-effort, not a guarantee.
- Rejected: Warn only — the value still enters the guest. No detection.
- Implementation: One shared detector in `src/celesto/` used by the CLI,
  facade (`facade.py:2174`), and server exec path (`server/app.py:77`).
- Tests: E2E via CLI and SDK: secret-looking name and value are refused with
  the exact message; `--not-secret` passes; nothing reached the guest.
- Acceptance: none — covered by E2E tests

### D-13: GitHub SSH URLs go over HTTPS; other SSH uses a filtered agent with chosen keys

- GitHub: the guest's global git config rewrites `git@github.com:` and
  `ssh://git@github.com/` to `https://github.com/` (`url.<base>.insteadOf`).
  Repos are untouched. Push and pull then use the HTTPS token injection (D-02).
- Other SSH: Celesto runs a per-sandbox filter in front of the host's
  `SSH_AUTH_SOCK` (ssh-agent, 1Password, etc.). It exposes only keys the user
  allowed and only signing — no listing of other keys, add, remove, or lock.
  Unlock (passphrase, Keychain, 1Password) stays on the host.
  - Allow a key: `celesto sandbox ssh-key add my-sbx ~/.ssh/id_work.pub`.
  - Default: no keys allowed.
- Why: The common case (push to GitHub) needs no setup and no SSH key; the
  sandbox can never sign with a key the user didn't choose, such as a
  production server key.
- Rejected: Forwarding the whole host agent — a prompt-injected agent could
  sign into anything the user can reach.
- Implementation: Agent filter in the per-VM proxy process; guest socket via
  vsock relay where available, SSH remote forwarding otherwise; guest
  `SSH_AUTH_SOCK` set for all exec paths. Allowed key fingerprints stored with
  the sandbox (public keys only).
- Tests: E2E: in a guest, `git clone git@github.com:<private test repo>`
  succeeds over HTTPS; `ssh-add -l` lists only the allowed key;
  signing with a non-allowed key fails.
- Acceptance: A-06

### D-14: A fresh per-sandbox CA on every start; private key only in proxy memory

- At each start the proxy generates a new CA. Before any user process runs,
  Celesto installs its certificate into the guest trust store
  (`/usr/local/share/ca-certificates/` + `update-ca-certificates`; images
  already ship `ca-certificates`, `images/builder.py:793`) and sets
  `NODE_EXTRA_CA_CERTS` and `SSL_CERT_FILE` to the full system bundle
  (`SSL_CERT_FILE` replaces Codex's store, so it must be the bundle, not the
  CA alone).
- The proxy mints leaf certificates only for bound hosts.
- Why: The key never touches disk and dies with the run; matches D-09.
- Rejected: One persisted CA per sandbox — an any-site impersonation key on
  disk for the sandbox's life. Name-constrained CA — little extra protection
  when the key never leaves memory, and adding a host to a running sandbox
  would need a new CA that running processes don't reload.
- Implementation: CA generation in the Rust proxy; certificate returned to
  the launcher and installed by the guest agent (or SSH fallback) during
  start, before preset launch.
- Tests: E2E: after a restart the guest's installed CA differs and no CA
  private key exists on host disk or in the guest; Codex (REST and WebSocket)
  and Claude Code connect through the proxy without TLS errors.
- Acceptance: A-01, A-02

### D-15: Secret changes apply live to a running sandbox

- `celesto sandbox secret set|remove` (and the SDK equivalent) update the
  running proxy over a local control channel, then the guest `/etc/hosts`
  and placeholder env file.
- Remove is an immediate kill switch: the next request with that placeholder
  gets no real value.
- Add: the proxy is ready at once; processes started afterwards see the new
  variable. The success message says already-open shells must be reopened.
- Why: Instant revocation, and adding a key mid-task is a common flow.
- Rejected: Next start only — no fast revocation short of stopping the
  sandbox.
- Implementation: Control channel on a host-only Unix socket owned by the
  user; CLI and facade call it.
- Tests: E2E: while a guest loop calls a stub host, `secret remove`; the next
  request carries only the placeholder.
- Acceptance: none — covered by E2E tests

### D-16: Contain proxy crashes, fail closed, and report clearly

- Panics are isolated to the connection that caused them.
- If the proxy process dies, secret hosts refuse connections; nothing leaks
  and other traffic is unaffected (D-04).
- The proxy watches the VM process and exits when it exits, so no orphaned
  proxy holds secrets.
- `celesto sandbox info` and `celesto sandbox list` show: `Credential protection stopped for my-sbx. Run 'celesto sandbox stop my-sbx' and 'celesto sandbox start my-sbx' to restore it.`
- Rejected: Auto-restart with the same CA — a second long-lived process holds
  the key. Auto-restart with a new CA — running clients keep failing TLS.
  Revisit only if crashes appear in practice.
- Implementation: Proxy health from PID + control socket in `sandbox info` /
  `list`; parent-death watch in the launcher.
- Tests: E2E: kill the proxy; secret host fails, `pypi.org` works, `info`
  shows the message (human and JSON). Kill the VM; the proxy exits.
- Acceptance: none — covered by E2E tests

### D-17: Clean up pre-release sandboxes automatically on their first start

- Celesto knows what it copied (each preset's env and file lists, plus
  `GIT_HOST_CONFIGS`). On the first start after upgrade it replaces each real
  env value and login file with placeholders, deletes copied private keys and
  token files (`/root/.ssh` keys, `/root/.git-credentials`, `/root/.config/gh`),
  and turns on the proxy.
- One-time message: `Celesto removed the real keys from old-codex and now protects them. If an agent may have copied them elsewhere in the sandbox, rotate them or recreate the sandbox.`
- Why: Protects existing users without destroying their work; honest about
  copies it cannot find.
- Rejected: Refusing to start old sandboxes — loses their state. Leaving them
  with a warning — real keys stay exposed.
- Implementation: A credential-protection version on each sandbox in the
  state DB; migration step in the start path.
- Tests: E2E: create a sandbox with the previous release's preset flow, start
  with the new release; D-01 scan passes and the message prints once.
- Acceptance: A-07

### D-18: Show what is protected, never the values

- Start summary: preset starts print each protected credential and its hosts,
  plus credentials that were not set.
- `celesto sandbox secret list <sandbox> [--json]`: name, hosts, source (env
  var or file), status (active / missing / proxy stopped), last used. Never
  values or placeholders.
- Proxy log: one line per injection (time, secret name, host, method, path,
  status) and per refusal (e.g. placeholder sent to a non-bound host). Shown
  by `celesto sandbox logs <sandbox> --credentials` (`cli/commands/app.py:783`).
- Invariant: no real value ever appears in output or logs; a test scans
  logs and CLI output for the real values.
- Why: Builds trust, answers "is it set up?", and shows what the agent did
  with a key it can still use (D-01 non-goal).
- Implementation: Start summary in the preset start output; `secret list`
  reads proxy status over the control socket; proxy log file in the
  sandbox's state dir.
- Tests: E2E output checks for summary, `secret list --json`, and log lines;
  the D-01 scan also runs over CLI output and logs.
- Acceptance: none — covered by E2E tests

### D-19: Built-in host bindings for preset credentials; inject into headers only

| Credential | Bound hosts | Injected as |
|---|---|---|
| `OPENAI_API_KEY` | `api.openai.com` | `Authorization: Bearer` |
| `ANTHROPIC_API_KEY` | `api.anthropic.com` | `x-api-key` |
| `OPENROUTER_API_KEY` | `openrouter.ai` | `Authorization: Bearer` |
| `GOOGLE_API_KEY`, `GEMINI_API_KEY` | `generativelanguage.googleapis.com` | `x-goog-api-key` |
| `HF_TOKEN` | `huggingface.co` | `Authorization: Bearer` |
| Codex ChatGPT login | `chatgpt.com`; `auth.openai.com` answered by the proxy (D-10) | `Authorization: Bearer` |
| Claude Pro/Max login | `api.anthropic.com`; `platform.claude.com` answered by the proxy | `Authorization: Bearer` |
| GitHub token | `github.com`, `api.github.com` | git `Authorization: Basic` (`x-access-token:<token>`); gh `Authorization: Bearer` |
| opencode / pi auth files | per provider entry, using the rows above | as above |

- Headers only. Basic auth is decoded, swapped, and re-encoded. Never the
  request body or URL query string (an echoing host could reflect the key).
  Known gap: clients sending a Google key as `?key=` fail; official SDKs use
  the header.
- OpenClaw: `OPENCLAW_GATEWAY_TOKEN` / `PASSWORD` authenticate clients to
  OpenClaw's own gateway, which runs in the sandbox. They are not copied;
  Celesto generates a fresh per-sandbox token. Verify OpenClaw's usage in the
  build before relying on this.
- Claude connectors (`mcp-proxy.anthropic.com`) are not bound until their
  credential is confirmed.
- Implementation: The table lives in the preset credential specs (D-02);
  Claude Code's custom-API-key approval is pre-seeded in `~/.claude.json`.
- Tests: Covered by the per-preset E2E runs and the Rust tests in D-08.
- Acceptance: A-01, A-02

## Open questions

- Q-01 (deferred by user): Linux host for Firecracker / QEMU TAP / bridge
  acceptance. Use the Mac for now; A-03's Linux half and A-04 stay not run.

## Acceptance plan

Only what the E2E tests cannot prove: real CLIs with real logins, real
GitHub, Linux backends, and upgrading from the previous release.

### A-01 (D-02, D-08, D-14, D-19): Codex works with an API key and a ChatGPT login

- Steps: `uv run celesto codex start`, once with `OPENAI_API_KEY` and once
  with a ChatGPT login; ask Codex a question that streams a reply.
- Expect: Replies stream over REST and WebSocket; guest `env` and
  `/root/.codex/auth.json` hold placeholders only.
- Result: pending

### A-02 (D-02, D-08, D-14, D-19): Claude Code works with an API key and a Pro/Max login

- Steps: `uv run celesto claude-code start`, once with `ANTHROPIC_API_KEY` and
  once with the Keychain login; run a prompt.
- Expect: Reply streams; no approval prompt for the key; guest holds
  placeholders only.
- Result: pending

### A-03 (D-04, D-07, D-08): Routing works on every supported backend

- Steps: On QEMU slirp and libkrun (macOS), Firecracker and QEMU TAP (Linux):
  raw exec `curl` to a bound host with the placeholder; `curl https://pypi.org`.
- Expect: Bound host authorized; pypi unaffected.
- Result: pending

### A-04 (D-07): Bridge mode fails closed

- Steps: `celesto codex start --network bridge` on Linux.
- Expect: Starts, prints the recovery message, guest scan finds nothing.
- Result: pending

### A-05 (D-10): Login refresh keeps both host and sandbox logged in

- Steps: Bring the real access token near expiry; use Codex in the sandbox
  and on the host; repeat for Claude Code with the Keychain login.
- Expect: Both keep working; host login file and Keychain updated; record
  whether macOS showed a Keychain prompt.
- Result: pending

### A-06 (D-13): Git over an SSH URL works against real GitHub; only allowed keys sign

- Steps: Clone and push a private repo via `git@github.com:`; `ssh-key add`
  one key; `ssh-add -l` in the guest.
- Expect: Clone and push succeed over HTTPS; only the allowed key is listed.
- Result: pending

### A-07 (D-17): Old sandboxes are cleaned on first start after upgrade

- Steps: Create a codex sandbox with the previous release (`uv tool install celesto==<previous>`); upgrade; start it.
- Expect: Guest scan passes; the one-time message prints once.
- Result: pending

### A-08 (D-01, D-02): No real value anywhere after real sessions

- Steps: After A-01, A-02, and A-06, run the guest-wide scan for the real
  values used.
- Expect: Zero hits; scan report saved.
- Result: pending

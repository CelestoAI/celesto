# How sandbox providers keep credentials out of sandboxes

Research for [sandbox-credential-injection.md](sandbox-credential-injection.md),
as of October 2026. Items marked *unverified* lack a primary source.

## Summary

Most providers now keep the real secret in a proxy outside the sandbox. The
sandbox holds a placeholder, or no credential at all, and the proxy attaches
the real value only on requests to the secret's allowed hosts. For HTTPS this
means TLS interception with a certificate authority (CA) generated per sandbox
and installed in the guest's trust store. Vercel, Modal, and Cloudflare
intercept traffic transparently. Anthropic's sandbox-runtime and Fly's
tokenizer use an explicit proxy.

## Comparison

| Provider | Secret in sandbox? | Mechanism | Host binding | Egress control | Source |
|---|---|---|---|---|---|
| Fly.io tokenizer (OSS) | No — the sandbox holds an encrypted blob it cannot open | Explicit HTTP proxy; `Proxy-Tokenizer` header; upgrades to HTTPS upstream; processors for header injection, HMAC, SigV4, JWT, OAuth client-credentials, GitHub App | `allowed_hosts` / pattern sealed inside the secret | Rejects requests without a sealed secret unless `OPEN_PROXY` | github.com/superfly/tokenizer |
| Fly Sprites | No (Connectors) | Gateway URL: the sandbox calls `api.sprites.dev/v1/gateway/<connector>/…` and the gateway adds auth | Per connector, with path allow/block | DNS allowlist; raw IPs blocked unless resolved from an allowed name; private IPs blocked | docs.fly.io/sprites |
| E2B (private beta) | No (`Secret.fill` reference) | Egress proxy rewrites headers on HTTPS only | Per hostname rule | `allowOut`/`denyOut` are separate from injection; an unresolved secret drops the header and still sends the request | docs.e2b.dev/secrets/inject |
| Daytona | Placeholder `dtn_secret_…` in env | Proxy swaps the placeholder in HTTPS headers; scrubs echoed real values from responses | Per-secret host allowlist; **no allowlist means every host** | CIDR plus domain firewall | daytona.io/docs/en/secrets |
| Modal | No (`$NAME` templates) | Transparent redirect of port 443, SNI routing, per-sandbox CA at `/etc/modal/sandbox-egress-ca.crt`, sets `SSL_CERT_FILE` and `NODE_EXTRA_CA_CERTS` | Exact or `*.` domain | Cannot be combined with allowlists; port 443 and HTTP/1.1 only | modal.com/docs/guide/sandbox-secret-injection |
| Vercel Sandbox | No | SNI firewall; terminates TLS only for domains with transform rules, using a per-sandbox CA | Domain, plus path/method/header matchers | Allow-all, deny-all, or domain/CIDR lists; documents that domain fronting is possible | vercel.com/docs/vercel-sandbox/concepts/firewall |
| Cloudflare Sandbox | No | Transparent (TPROXY); "outbound Workers" set headers; `interceptHttps` creates a per-instance CA and sets CA env vars for Node, curl, Python, and Git | `outboundByHost` | `allowedHosts`/`deniedHosts`; ports 80/443 only | developers.cloudflare.com/sandbox/guides/outbound-traffic |
| Runloop | Gateway token only | Base-URL reverse proxy (`$NAME_URL`); gateway swaps the token for the real key; token bound to one devbox | One endpoint per gateway | Hostname network policies | docs.runloop.ai/docs/devboxes/agent-gateways |
| Blaxel (preview) | No (`{{SECRET:name}}`) | Proxy resolves placeholders in headers or JSON body | Per routing-rule destinations | Domain filtering; unresolved placeholders forwarded as literal text | docs.blaxel.ai/Sandboxes/Proxy-secrets-injection |
| Docker Sandboxes | Sentinel value | Host proxy overwrites the auth header; built-in service-to-domain map; SSH agent forwarding for git | Per service domain | Install-time vs runtime allowlists. CVE-2026-101998 (fixed 0.47.0): fail-open response masking leaked OAuth tokens | docs.docker.com/ai/sandboxes/security/credentials |
| Anthropic sandbox-runtime | Optional sentinel (`mode: mask`) | Explicit HTTP + SOCKS5 proxy, reachable only through a Unix socket so there is no other route out; experimental TLS termination; `ssh` wrapped via `GIT_SSH_COMMAND` | `injectHosts` | Deny by default; blocks loopback, link-local, and metadata IPs | github.com/anthropic-experimental/sandbox-runtime |
| Claude Code on the web | No for git and network secrets | GitHub proxy swaps a scoped credential for the real token and blocks tag pushes, branch deletion, GraphQL, and unattached repos | Per-secret host list | None / Trusted / Full / Custom | code.claude.com/docs/en/cloud-environments |
| OpenAI Codex cloud | Only during setup scripts | Time separation: secrets are removed and internet is off by default before the agent runs | n/a | Allowlist presets; optional GET/HEAD/OPTIONS only | learn.chatgpt.com/docs/environments/cloud-environment |
| GitHub Copilot agent | MCP gets `COPILOT_MCP_*` env vars | Firewall covers only Bash-tool processes, not MCP or setup | n/a | Allowlist | docs.github.com (customize the agent firewall) |
| Deno Sandbox | Placeholder | Outbound proxy substitutes only for approved hosts | `secrets: {value, hosts}` | `allowNet` | docs.deno.com/sandbox/security |
| Northflank, Morph | *Unverified* — no injection feature found in primary docs | | | | |

Open-source building blocks: Envoy `credential_injector` filter, Stripe
smokescreen (CONNECT ACL, no injection), iron-proxy (MITM + token swap,
default deny), OneCLI, Infisical Agent Vault, coder/httpjail, mitmproxy.

## Patterns and pitfalls

1. **Bind every secret to hosts.** Daytona injects into every host when a
   secret has no allowlist. Injection rules do not restrict egress on their
   own (E2B, Vercel).
1. **HTTPS injection needs a per-sandbox CA in the guest trust store.**
   Terminate TLS only for hosts that carry a secret; pass the rest through.
   Set `SSL_CERT_FILE`, `NODE_EXTRA_CA_CERTS`, `REQUESTS_CA_BUNDLE`, and git's
   CA. JVM and some Go/Rust binaries ship their own trust store; pinned
   clients need an exclusion. Never inject over plain HTTP.
1. **Inject into headers, not anywhere in the request.** Swapping anywhere in
   the request lets an allowed host that echoes input reflect the real key
   back. Response scrubbing must fail closed (Docker CVE-2026-101998).
1. **Capture traffic at the network layer, not via `HTTP_PROXY`.** Agents
   unset proxy variables, and ssh, the JVM, and Bun ignore them. Use nftables
   or TPROXY, or remove every other route out.
1. **Identify the destination robustly.** After terminating TLS, require the
   Host header to match SNI. Decide whether traffic with no SNI, QUIC, or
   non-443 ports is denied or passed through uninjected.
1. **Git needs special handling.** Swap a session token for the real token on
   HTTPS, and optionally enforce policy such as no tag pushes. For SSH, use
   agent forwarding or a ProxyCommand, or require HTTPS remotes.
1. **Alternatives without interception:** base-URL gateways (Runloop, Fly
   Connectors) need no CA but require clients that accept a base URL.
   Time-phased secrets (Codex) suit setup-only credentials.
1. **Fail closed.** E2B sends the request without the header when a secret is
   unresolved; Blaxel forwards the literal placeholder.

## Codex and Claude Code compatibility

Checked against openai/codex at 9032fc7 (2026-10-19), the Claude Code 2.1.303
native binary, and code.claude.com/docs/en/network-config. Not yet tested end
to end. Neither CLI pins certificates.

| | Codex CLI | Claude Code |
|---|---|---|
| Trusts a custom CA | Yes. System store via `rustls-native-certs`; `SSL_CERT_FILE` / `CODEX_CA_CERTIFICATE` **replace** the store, so point them at the full bundle (`/etc/ssl/certs/ca-certificates.crt`). Issue openai/codex#46489 reports the WebSocket path rejecting an `SSL_CERT_FILE`-only CA; installing into the system store covers both. | Yes. Bun binary reads bundled + OS store; honors `NODE_EXTRA_CA_CERTS`. Set both. |
| Local token parsing | Decodes `id_token` and `access_token` JWTs without verifying signatures (`email`, plan, account ID, `exp`). Placeholders must be well-formed JWTs with the same claims and a far-future `exp`. | Checks prefixes (`sk-ant-oat`, `sk-ant-api03-`). Placeholders must keep the prefix; set `expiresAt` far in the future. Pre-approve a custom `ANTHROPIC_API_KEY` in `~/.claude.json`. |
| Refresh | `POST auth.openai.com/oauth/token`; triggered by `exp` within 5 min, `last_refresh` older than 8 days, or a 401. `invalid_grant` logs out. | `POST platform.claude.com/v1/oauth/token`; triggered by `expiresAt` within 5 min or a 401. `invalid_grant` wipes tokens. |
| Credential header | `Authorization: Bearer` (+ `ChatGPT-Account-ID`) to `api.openai.com` or `chatgpt.com/backend-api/codex` | `x-api-key` (API key) or `Authorization: Bearer` (OAuth) to `api.anthropic.com` |
| Transport needs | WebSocket by default (`wss://chatgpt.com/backend-api/codex/responses`): inject on the Upgrade request. HTTP/2 via ALPN. | Long-lived SSE; do not buffer. Gzipped request bodies. |
| Fallback | `openai_base_url`, custom `model_providers` with `base_url` | `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN` |

Only the host may refresh: OpenAI rejects a reused refresh token
(`refresh_token_reused`). Codex ships its own credential broker that uses
prefix-preserving "shaped dummy" keys
(`codex-rs/network-proxy/src/credential_broker`), a useful model for
placeholder shape.

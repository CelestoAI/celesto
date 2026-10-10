# Submitting Celesto to sandbox infrastructure benchmarks

Measure Celesto’s create / first-command / workload latency against peers such as E2B, Daytona, and Modal. The public board is **ComputeSDK**.

Assumed Celesto surface for gap analysis: exec, file upload/download, snapshots, published ports, env vars, host directory mounts, local VM by default, optional cloud, Linux. ComputeSDK’s daily job calls a **remote** API from Namespace GitHub runners — a laptop-only Celesto cannot appear on that board.

## Summary

| Platform | What they measure | What to ship | Listing path |
| --- | --- | --- | --- |
| **ComputeSDK Benchmarks** | Burst TTI + DAX (sandbox infra only) | `@computesdk/celesto` + PR into `computesdk/benchmarks` | PR like [sandbox0 #239](https://github.com/computesdk/benchmarks/pull/239); vault API key for daily CI |

Live board: [computesdk.com/benchmarks/sandboxes](https://www.computesdk.com/benchmarks/sandboxes). Repo: [computesdk/benchmarks](https://github.com/computesdk/benchmarks). Methodology: [METHODOLOGY.md](https://raw.githubusercontent.com/computesdk/benchmarks/master/METHODOLOGY.md).

## What you submit

A **sandbox provider** under the ComputeSDK interface, then a PR that wires it into the daily benchmark matrix. There is no separate application form. Sponsors cannot buy a score; results are committed as JSON and the methodology is public ([README](https://raw.githubusercontent.com/computesdk/benchmarks/master/README.md)).

## What they measure

- **Burst Time to Interactive (TTI):** wall-clock from `compute.sandbox.create()` to the first successful `runCommand('node -v')`, for **100 concurrent** sandboxes. Composite score = timing score × success rate against a fixed 10s ceiling. Failures are not retried. Teardown is not timed. Sequential/staggered TTI suites are retired; historic JSON remains.
- **DAX:** clone → install → typecheck inside a fresh sandbox (real developer workload). Lower is better.

Daily automation runs on Namespace GitHub Actions (~00:00 UTC). As of late September 2026 the board listed on the order of ~27 burst-TTI providers and ~20 DAX providers.

## Official interface

Build with [`@computesdk/provider` `defineProvider`](https://github.com/computesdk/computesdk/blob/main/packages/provider/README.md). Required for TTI:

- `sandbox.create` → `{ sandbox, sandboxId }`
- `sandbox.runCommand` → `{ stdout, stderr, exitCode }`
- `sandbox.destroy`
- Also typically: `getById`, `list`, `getInfo`, `getUrl`

DAX needs filesystem helpers (`readFile` / `writeFile` / `mkdir` / …) and outbound network so the install/typecheck workload can run. The probe assumes a **Node** runtime (`node -v`).

## Listing path (from merged PRs)

Mirror [feat: add sandbox0 (#239)](https://github.com/computesdk/benchmarks/pull/239) / Beam-style one-block adds:

1. Publish `@computesdk/celesto` (or `celesto` wrapped via `defineProvider`).
2. Add a factory in `benchmarks/sandbox/providers.ts` with `requiredEnvVars` (e.g. `CELESTO_API_KEY`).
3. Document the key in `.env.example`; regenerate `provider-vars.json` via their `gen-provider-vars.ts` script; add `bench:celesto` in `package.json`.
4. Maintainers seed the Namespace vault; runs without the key skip with a clear missing-credential note.

## Celesto gaps

- **Remote cloud API** the Namespace runner can hit (local-only computers cannot rank).
- Survive **100 simultaneous creates** with a high success rate (composite scoring punishes flaky launches harder than slow ones).
- Image/template with **Node** (and git/network for DAX).
- Optional later: snapshot/fork suite if ComputeSDK’s snapshot benchmarks matter for product claims.

## Recommended next step

1. Ship a cloud create/exec/destroy surface + `@computesdk/celesto`.
2. Smoke-test `pnpm exec tsx … --provider celesto --mode burst --concurrency 10` against ComputeSDK’s runner.
3. Open the benchmarks PR and arrange vault credentials.
4. Keep Celesto’s own `scripts/benchmarks/` for local/regression numbers; they are not a substitute for the public board.

## Open questions

- Whether Celesto cloud quotas / warm pools can absorb ComputeSDK’s 100-sandbox burst without tanking success rate.
- Whether ComputeSDK will accept a provider that boots full VMs (vs container/microVM peers) without methodology objections — dispute path is a GitHub issue ([METHODOLOGY.md](https://raw.githubusercontent.com/computesdk/benchmarks/master/METHODOLOGY.md)).

## Primary sources

- https://www.computesdk.com/benchmarks/sandboxes/
- https://github.com/computesdk/benchmarks
- https://raw.githubusercontent.com/computesdk/benchmarks/master/README.md
- https://raw.githubusercontent.com/computesdk/benchmarks/master/METHODOLOGY.md
- https://github.com/computesdk/computesdk/blob/main/packages/provider/README.md
- https://github.com/computesdk/benchmarks/pull/239

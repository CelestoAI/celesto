# Celesto CI from the terminal

Status: accepting. PR 2 (CLI) is a draft on claude/celesto-ci-cli and merges after backend #1069 deploys; A-02, A-04 and A-05 run against production then. PR 1 (backend) is open at https://github.com/CelestoAI/backend/pull/1069; A-01 and A-03 not run
Acceptance target: PR 1 on the backend local stack (`scripts/run_all.sh` in a backend worktree); PR 2 read-only against production (`celesto auth login` with Celesto's own default API key, done by the user)

## Context

Customers who run their GitHub Actions jobs on Celesto (labels such as
`celesto-standard`) can only see those jobs in the dashboard. Blacksmith ships a
CLI that lets people and their coding agents list jobs, read logs, browse
machine sizes, manage caches, read usage and run tests on a remote box. We want
Celesto CI customers to have the same from `celesto`.

Facts from the code (verified 2026-11-03):

- The backend already serves jobs and logs to the dashboard:
  `GET /v1/integrations/github/actions/jobs/page`, `/jobs/groups`,
  `/jobs/summary`, `/jobs/{job_id}`, `/jobs/{job_id}/steps` and
  `/jobs/{job_id}/steps/{number}/log`
  (`backend/src/celesto_api/v1/integrations/github_actions_ci.py:327-470`).
- A step log is the last 5,000 lines GitHub wrote for that step, read live from
  GitHub (`backend/src/celesto_cloud_core/services/github_actions_logs.py:144-151`).
  Celesto stores no logs, so nothing can be searched across jobs.
- Those routes accept the dashboard's default API key. Named (scoped) keys are
  refused on every route outside `/v1/computers`
  (`backend/src/celesto_cloud_core/core/security.py:478-547,589-592`).
- An API key carries its organization, so no organization header is needed
  (`backend/src/celesto_api/dependencies.py:116-118`).
- Machine sizes and their vCPU, RAM, disk and hourly price live in
  `backend/src/celesto_cloud_core/services/sandbox_sizes.py:22-29`; CI labels map
  to them in `github_actions_ci_sizes.py:6-29`. No endpoint returns them.
- The CLI's generated client lacks `/jobs/page`, `/jobs/groups`, `/jobs/summary`,
  `/jobs/{id}/steps` and the step-log route
  (`src/_celesto_cloud_api/api/git_hub_actions_on_celesto/`). It is regenerated
  from `openapi/cloud.json` (`docs/python-cloud.md:302-308`).
- CLI commands default to human output and take `--json`
  (`src/celesto/cli/commands/app.py`, `src/celesto/cli/output.py`).

Non-goals (D-01): cache list/delete, usage and cost, Testbox, per-job CPU and
memory, sticky disks, cross-job log search.

## Decisions

### D-01: Ship only commands over data the backend already has: jobs, logs, machine sizes

- Why: these need at most one small backend route; the rest need new storage
  or data collection, and Testbox alone outweighs the whole MVP.
- Rejected: one feature for all Blacksmith parity — too large for one review
  and blocks the cheap wins on the slow ones.
- Implementation: commands under D-02; follow-up features get their own
  decision logs.
- Tests: n/a (scope decision).
- Acceptance: n/a.

### D-02: One new top-level group, `celesto ci`, with `jobs list`, `jobs show <job-id>`, `logs <job-id>` and `runners list`

- Why: one top-level name for the whole CI area; `logs` mirrors
  `celesto sandbox logs` and is the most-read command. Signed off by the user as
  the CLAUDE.md top-level discussion (2026-11-03).
- Rejected: `celesto ci jobs logs` (strict noun-verb, more typing);
  per-noun top-level commands (`celesto jobs`, clashes with sandboxes).
- Implementation: a `ci` click group in `src/celesto/cli/commands/app.py` with
  `jobs` and `runners` subgroups and a `logs` command; handlers in a new
  `src/celesto/cli/ci.py`. Add `ci` to the CLI design list in AGENTS.md
  (CLAUDE.md is a symlink to it).
- Tests: CLI e2e tests for each command (see slice plan).
- Acceptance: A-01..A-04 (to be drafted).

### D-03: Only the default API key works; the CLI rewrites the named-key refusal into a clear recovery message

- Why: keeps backend permissions unchanged in this feature while telling the
  user exactly what to run.
- Rejected: passing the backend's generic message through (no recovery
  command); adding a `ci:read` scope now (backend, dashboard and security
  review — first follow-up after this ships).
- Implementation: in `src/celesto/cli/ci.py`, a 403 whose `error_code` is
  `api_key_endpoint_not_allowed` becomes: "This API key can't read CI jobs. Run
  'celesto auth login' with your dashboard's default API key." Same text in
  human output and in the JSON `error` payload.
- Tests: CLI e2e test with a named key gets the message and a non-zero exit.
- Acceptance: A-05 (to be drafted).

### D-04: `jobs list` reads `/jobs/page`; the backend gains `failed` and `passed` status filters

- Why: "which of my jobs failed?" is the main question; today failures hide
  inside `completed` (`backend/.../github_actions_status.py:25`).
- Rejected: only the existing tabs (cannot list failures); filtering in the
  CLI (slow, uneven pages).
- Implementation:
  - Backend: `CIJobTab` gains `"failed"` and `"passed"`. Both are finished
    jobs (`native_status == "completed"`). `passed` = result `success` or
    `neutral`; `failed` = any other result except `skipped`, `cancelled`,
    `stale`, `completed` — the same split as `_bucket`
    (`github_actions_status.py:45-57`), expressed once and shared by `_bucket`
    and the SQL filter in `crud/github_actions_ci.py:807` so they cannot drift.
    Counts include the two new tabs.
  - CLI: `celesto ci jobs list [--repo OWNER/REPO] [--workflow NAME] [--status in-progress|needs-action|completed|failed|passed] [--search TEXT] [--limit N]`. `--limit` default 20, max 100, read as
    one page of that size.
- Tests: backend API test seeding passed, failed, cancelled, skipped and
  running jobs, asserting each tab's rows and counts; CLI e2e test for flag
  mapping.
- Acceptance: A-01 (to be drafted).

### D-05: `logs <job-id>` prints every step in order; `--step N` prints one

- Why: one command answers "what happened in this job"; agents can `grep` the
  output. No backend change.
- Rejected: failed steps only by default (a passed job prints nothing); a new
  whole-log backend route (more backend work, rethinks the 5,000-line cap).
- Implementation: `src/celesto/cli/ci.py` calls `/jobs/{id}/steps`, then
  `/jobs/{id}/steps/{n}/log` per step, printing `── Step <n>: <name> (<conclusion or status>) ──` before each step's lines. A step whose log is
  `truncated` gets a line saying only the last 5,000 lines are shown. `--json`
  returns `{"job_id", "steps": [{number, name, status, conclusion, lines, truncated}]}`. `--step N` with an unknown N exits non-zero with: "Job <id>
  has no step <N>. Run 'celesto ci logs <id>' to see all steps."
- Tests: CLI e2e test against a backend stub with a multi-step job (all
  steps, `--step`, unknown step, truncated step).
- Acceptance: A-02 (to be drafted).

### D-06: New backend route `GET /v1/integrations/github/actions/runners` returns the documented sizes; no price

- Why: one source of truth, so the CLI never shows stale specs. Price is left
  out because CI billing may not match the sandbox hourly rates.
- Rejected: a copy of the table in the CLI (goes stale).
- Implementation: route in `backend/src/celesto_api/v1/integrations/github_actions_ci.py`,
  same auth dependencies as `/jobs` (`activated_only`). Response:
  `{"runners": [{"label": "celesto-micro", "size": "micro", "vcpus": 1, "ram_mb": 2048, "disk_size_mb": 20480}, ...]}`, one entry per
  `CI_SIZE_LABELS` key (`github_actions_ci_sizes.py:6-13`) in that order,
  specs from `SANDBOX_SIZES_BY_ID`. Legacy labels are not listed.
  CLI: `celesto ci runners list` prints LABEL, VCPU, RAM, DISK.
- Tests: backend API test asserting the six labels and their specs match
  `SANDBOX_SIZES`; CLI e2e test for the table and `--json`.
- Acceptance: A-03 (to be drafted).

### D-07: Human output by default, `--json` for the standard envelope

- Why: every other `celesto` command works this way; agents already pass
  `--json`.
- Rejected: Blacksmith's JSON-by-default (makes `celesto ci` the odd one out).
- Implementation: every `celesto ci` command takes the existing `json_option`
  and emits through `emit_json` (`src/celesto/cli/output.py`) with command names
  `ci.jobs.list`, `ci.jobs.show`, `ci.logs`, `ci.runners.list`.
- Tests: covered by each command's e2e test (human and `--json`).
- Acceptance: covered by A-01..A-03.

### D-08 (superseded by D-13): Two PRs: backend first and deployed, then the CLI PR with a regenerated client

- Why: customers never get a CLI that calls routes production lacks.
- Rejected: releasing both together off the local stack (a CLI release ahead
  of the backend deploy breaks for customers).
- Implementation: PR 1 in `celesto.ai/backend` (D-04 filters, D-06 route).
  After it deploys, export the schema into `openapi/cloud.json`, regenerate
  `src/_celesto_cloud_api` with the pinned generator
  (`docs/python-cloud.md:302-308`), and commit both in PR 2 here.
- Tests: the regenerated client is exercised by the CLI e2e tests.
- Acceptance: A-04 (to be drafted) runs PR 2 against production after PR 1
  deploys.

### D-09: `logs` on an unfinished job prints what GitHub has, then a note; no follow mode

- Why: GitHub often serves no log until the job finishes
  (`backend/.../github_actions_logs.py:148`), so a follow mode would mostly wait.
- Rejected: `--follow` polling.
- Implementation: `logs` first reads `/jobs/{id}`; if the job is not finished,
  it prints the steps it gets and then, on stderr: "Job <id> is still running,
  so its log may be incomplete. Run 'celesto ci logs <id>' again when it
  finishes." Exit 0. With `--json`, the same text goes in `data.warnings`
  (the JSON envelope has no warnings field).
- Tests: CLI e2e test with a running job stub (human and `--json`).
- Acceptance: A-02 covers a finished job; running-job behaviour is covered by
  the test.

### D-10: Accept PR 1 on the local stack with seeded jobs; accept PR 2 read-only against production

- Why: filters and the runners route need no GitHub; `logs` can only be proven
  against real GitHub logs.
- Rejected: local stack only (never reads a real GitHub log).
- Implementation: seed script for A-01/A-03 inserts finished (success,
  failure, cancelled, skipped) and running jobs into the slot database. PR 2
  runs only GET commands in production.
- Tests: n/a.
- Acceptance: A-01..A-05.

### D-11: The jobs page counts finished, failed and passed jobs in one query

- Why: D-04 made every jobs-page load (polled every 5-10 s) run 3 COUNTs
  over the full filter set instead of 1 (review finding, ruled by the user
  2026-11-03).
- Rejected: keeping three COUNTs; counting only the active tab (the page
  shows every tab's count).
- Implementation: `GitHubActionsCRUD.completed_counts(filters)` in
  `backend/src/celesto_cloud_core/crud/github_actions_ci.py` returns
  `{"completed", "failed", "passed"}` from one `SELECT count(*), sum(CASE...), sum(CASE...)`; `page_jobs` uses it. The failed/passed conditions stay shared
  with `job_page`.
- Tests: a test counting finished-job COUNT statements per page load (one);
  the existing count tests keep the numbers right.
- Acceptance: A-01.

### D-12: The CI jobs-tab and runners tests run in GitHub CI on Postgres

- Why: CI runs a fixed list of files, so the new tests never ran there and
  never on Postgres (review finding, ruled by the user 2026-11-03).
- Rejected: leaving them local-only (`make verify-db`).
- Implementation: a step in the Postgres job of
  `backend/.github/workflows/tests.yml` runs
  `tests/e2e/test_ci_jobs_result_tabs.py tests/e2e/test_ci_runners_route.py -q --require-postgres`.
- Tests: the step itself; run locally against Postgres before pushing.
- Acceptance: the PR's CI run shows the step passing.

### D-13: Build the CLI PR now against the backend PR's schema; it opens as a draft and merges only after backend #1069 deploys

- Why: the user asked for the CLI PR alongside the backend PR (2026-11-03).
  D-08's reason still holds: no CLI release may call routes production lacks.
- Rejected: waiting for the deploy before writing the CLI (D-08).
- Implementation: export `/openapi.json` from the PR 1 branch's running
  backend (slot 14, :9900) into `openapi/cloud.json`, regenerate
  `src/_celesto_cloud_api`, build slices 3-9. Open PR 2 as a draft that names
  CelestoAI/backend#1069. Before merging, re-export the schema from the
  deployed backend and confirm the generated client has no diff.
- Tests: CLI tests as in the slice plan.
- Acceptance: A-02, A-04, A-05 run against production after #1069 deploys.

### D-14: Every `celesto ci` error says what happened and the exact recovery, and each has a test

- Why: review found two misleading messages (a GitHub 404 read as "job not
  found", a GitHub outage blamed on the login) and several untested ones
  (ruled by the user 2026-11-04).
- Rejected: one generic HTTP message for everything.
- Implementation: in `src/celesto/cli/ci.py`, same text in human output and
  the JSON `error`:
  - not logged in or unreadable login (`ValueError` opening the connection; a
    stored login with non-text fields is checked up front and raises it), `not_logged_in`: "Your Celesto login is missing or invalid.
    Run 'celesto auth login'."
  - 401, `unauthorized`: "Your Celesto API key was refused. Run 'celesto auth
    login'."
  - 403 named key: D-03.
  - 404 on job details, `ci_job_not_found`: "CI job <id> was not found. Run
    'celesto ci jobs list' to see your jobs."
  - 404 on steps or a step log, `ci_log_unavailable`: "GitHub no longer has the
    log for job <id>. Open \<github_job_url> to check it."
  - 502, `github_unavailable`: "GitHub is unavailable right now. Retry in a
    minute."
  - transport failure, `cloud_transport_error`: "Could not reach Celesto
    (<error type>). Check your connection and retry."
  - unreadable body, `cloud_invalid_response`: "Celesto returned an invalid
    response. Retry, or run 'celesto update' if it keeps happening."
  - any other status, `http_<status>`: "Celesto CI returned HTTP <status>.
    Retry, then check 'celesto auth status'."
  - `--search` over 200 characters, `--repo`/`--workflow` over 255: click
    usage error (exit 2) naming the flag and its limit, before any request.
- Tests: one CLI test per message through the HTTP stub (or a closed port for
  the transport failure).
- Acceptance: A-04 covers the happy path; errors are covered by tests.

### D-15: `celesto ci` records no local-usage telemetry

- Why: telemetry features count local computer use; CI commands are cloud
  reads, like `auth` (ruled by the user 2026-11-04).
- Rejected: counting them as `setup`.
- Implementation: `ci` joins the nouns that return early in `_before_command`
  (`src/celesto/cli/commands/app.py`); the update notice still shows.
- Tests: n/a (no behaviour visible to the user).
- Acceptance: n/a.

### D-16: When `jobs list` hits `--limit 100` and more jobs exist, the hint suggests narrowing

- Why: suggesting `--limit 100` when already at 100 is a dead end (ruled by
  the user 2026-11-04).
- Implementation: below 100: "Showing <n> of <total> jobs. Run 'celesto ci
  jobs list --limit 100' to see more." At 100: "Showing 100 of <total> jobs.
  Narrow the list with --status, --repo or --search."
- Tests: CLI test for both hints.
- Acceptance: n/a.

### D-17: A backend 502 for lost GitHub App access gets its own message

- Why: the backend sends 502 both when GitHub is down and when Celesto's
  GitHub App lost access; "Retry in a minute" never fixes the second (review
  finding, ruled by the user 2026-11-04).
- Rejected: one 502 message (D-14 as first written).
- Implementation: in `_api_error` (`src/celesto/cli/ci.py`), a 502 whose
  `detail` is exactly "GitHub access is unavailable. Check the App
  installation." (`backend/.../github_actions_logs.py:174`) becomes
  `github_access_denied`: "Celesto's GitHub App can't read this repository.
  Check its installation in your GitHub organization's settings." Every other
  502 keeps D-14's `github_unavailable`. Only that exact text is matched;
  other server text is never printed.
- Tests: CLI test for both 502 bodies.
- Acceptance: n/a.

### D-18: Only the backend's own GitHub-outage 502 says GitHub is down; other 502s get the generic message

- Why: a 502 can come from a Celesto gateway while GitHub is fine; D-14's
  "GitHub is unavailable" would then mislead (CodeRabbit review on #702,
  2026-11-04, under the user's Auto-fix authorization).
- Supersedes: D-14's 502 line.
- Implementation: `_api_error` returns `github_unavailable` only for a 502
  whose `detail` is exactly "GitHub is unavailable. Try again."
  (`backend/.../github_actions_logs.py:175,178`); D-17's access text keeps
  `github_access_denied`; any other 502 is `http_502`.
- Tests: CLI tests for all three 502 bodies.
- Acceptance: n/a.

## Open questions

(none)

## Slice plan

Test seam for PR 2: `CliRunner` invoking `build_cli()`, going through the real
generated client to a local HTTP stub that serves backend-shaped JSON (the
style of `tests/cli/test_computer_providers.py`, but stubbing HTTP, not
handlers). The live check is `tests/test_ci_live.py`, skipped unless
`CELESTO_CI_LIVE=1`, which writes its output to `artifacts/ci-cli-live/`.

PR 1, backend (`celesto.ai/backend`):

1. `/jobs/page?tab=failed|passed` returns the right rows and counts — seam:
   backend API test over seeded jobs — D-04
1. `GET /integrations/github/actions/runners` returns the six labels and specs —
   seam: backend API test — D-06

PR 2, CLI (this repo, after PR 1 deploys):
3\. Tracer: regenerated client plus `celesto ci runners list` (human and
`--json`), `ci` group registered, CLAUDE.md CLI list updated — seam:
CliRunner + HTTP stub — D-02, D-06, D-07, D-08
4\. `celesto ci jobs list` with all filters and `--limit` paging — seam:
CliRunner + HTTP stub asserting query parameters — D-04, D-07
5\. `celesto ci jobs show <id>`, including the not-found message — seam:
CliRunner + HTTP stub — D-02, D-07
6\. `celesto ci logs <id>` (all steps, `--step`, unknown step, truncated) —
seam: CliRunner + HTTP stub — D-05, D-07
7\. Running-job note — seam: CliRunner + HTTP stub — D-09
8\. Named-key refusal message — seam: CliRunner + HTTP stub returning the
backend's 403 body — D-03
9\. Live check `tests/test_ci_live.py` — D-10

## Acceptance plan

### A-01 (D-04): Failed and passed filters on the running backend

- Steps: on the backend worktree's local stack, seed one job per result, then
  `GET /v1/integrations/github/actions/jobs/page?tab=failed` and `tab=passed`
  with a default key.
- Expect: `failed` lists only the failure job, `passed` only success and
  neutral; counts match; cancelled, skipped and running jobs appear in neither.
- Result: pending

### A-02 (D-05, D-09): Logs of a real failed job in production

- Steps: `celesto ci jobs list --status failed --limit 5 --json`, then
  `celesto ci logs <first id>` and `celesto ci logs <first id> --step <failed step>`.
- Expect: every step printed in order with headers; the failed step's lines
  match GitHub's log for that step; exit 0.
- Result: pending

### A-03 (D-06): Runner sizes from the running backend

- Steps: local stack `GET .../actions/runners`; after deploy,
  `celesto ci runners list` in production.
- Expect: six labels, specs equal to `sandbox_sizes.py:22-29`, no price.
- Result: pending

### A-04 (D-02, D-04, D-07, D-08): Released CLI against deployed backend

- Steps: in production, `celesto ci jobs list`, `--status failed`,
  `--repo <a Celesto repo>`, `celesto ci jobs show <id>`, each with and without
  `--json`.
- Expect: readable tables; valid JSON envelopes; filters narrow the rows.
- Result: pending

### A-05 (D-03): Named key gets the recovery message

- Steps: user logs in with a named key (computers-only), runs
  `celesto ci jobs list` and `--json`; then logs back in with the default key.
- Expect: "This API key can't read CI jobs. Run 'celesto auth login' with your
  dashboard's default API key." in both outputs; non-zero exit.
- Result: pending

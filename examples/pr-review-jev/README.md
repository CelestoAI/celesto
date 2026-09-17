# Review Lab

Paste a public GitHub pull request and watch an agent prepare its test environment, run checks, and compare two reviewers. Choose local Celesto OSS or Celesto Cloud from the same page.

## Run

Requires Python 3.12+, uv, model credentials, and one sandbox backend. For Jev through Vercel, also install Node.js 22+ and run `npm install` in this directory. Copy `.env.example` to `.env` and supply `OPENAI_API_KEY` and `AI_GATEWAY_API_KEY`. The application never sends these keys into repository sandboxes.

Jev defaults to Vercel Gateway when `AI_GATEWAY_API_KEY` is present. No separate TypeSafe key is needed. The fixed Node helper uses AI SDK 7's evaluation API, which is separate from Gateway's Chat Completions API. To use TypeSafe directly instead, set `JEV_PROVIDER=typesafe` and `TYPESAFE_API_KEY`. Gateway Choice confidence is preserved when provided in provider metadata; missing confidence is not invented. Reported evaluator wall time includes Node startup; `sdk_seconds` isolates the SDK request.

When both LLM keys exist, direct OpenAI is selected. Set `LLM_PROVIDER=gateway` to use Vercel AI Gateway. Both default to GPT-5.6 Luna, using each provider's model ID format. Override `INVESTIGATOR_MODEL`, `EVALUATOR_MODEL`, and `WRITER_MODEL` to compare another model. Providers never silently fall back during a review. For another compatible endpoint, set `LLM_PROVIDER=custom`, `LLM_BASE_URL`, `LLM_API_KEY`, and explicit model IDs.

Local, from this example directory in the Celesto source checkout:

```sh
uv run --env-file .env python app.py
```

The demo resolves SmolVM from the parent Celesto checkout automatically. Run `uv run smolvm doctor` first to check the local virtualization setup.

The 16 GB review disks also need `e2fsprogs`. On macOS, install it with `brew install e2fsprogs`; the demo discovers its Homebrew tools without changing your shell configuration. On Debian/Ubuntu, use `sudo apt-get install e2fsprogs`.

Cloud, with the Celesto SDK installed:

```sh
uv run --extra cloud --env-file .env python app.py
```

Set `CELESTO_API_KEY` and, if necessary, `CELESTO_TEMPLATE`. The default template is `coding-agent`. Open http://127.0.0.1:4328 and select the installed backend. Reports record the provider and configured models, as well as model IDs returned by inference calls.

## What happens

1. Fetch public PR metadata and pin the base and head commits.
2. A discovery sandbox and investigator LLM inspect repository manifests and CI to produce an installation/test recipe.
3. Two fresh sandboxes run that recipe against base and head. Installation failures remain distinct from test failures.
4. The investigator examines the diff and gathers evidence for at most six candidate findings.
5. Both evaluators receive the same evidence and three questions per candidate: introduced by the PR, supported by evidence, and actionable. Jev receives all questions in one call. The LLM receives the same rubric in one call.
6. The same writer model summarizes each lane's results. Uncertain candidates remain marked as needing evidence; this version does not automatically reinvestigate them.
7. Sandboxes are deleted and a JSON report is saved under `artifacts/`. Cleanup errors remain visible.

Evaluator calls run concurrently. The UI separates shared preparation, evaluator latency, and writer latency. Usage and exact returned model names are in the report. It does not claim accuracy, calculate unconfigured dollar prices, or treat probability concentration as proof of correctness. A run with zero candidate findings does not perform a speed comparison.

## Limits

This is a local, single-run demo. It supports public PRs with at most 30 changed files and 3,000 changed lines. Logs are bounded and report truncation. The setup agent gets six commands, the investigator ten, and each command gets 180 seconds. Cancellation waits for an in-flight operation before cleanup. A process crash can leave resources requiring manual cleanup.

Repository and generated commands execute inside disposable sandboxes with internet access and no shared host workspace. Only run repositories you are comfortable executing under that provider's network policy. Reports contain source and test logs. The server listens on loopback and checks browser origins and request tokens; it is not a hosted multi-user service.

The rubric comparison is implemented. CUA browser journeys, labeled benchmark datasets, repeated-trial statistics, and automatic investigation of uncertain findings are follow-up work. A failing PR test with a passing baseline is evidence to investigate, not automatic proof of a regression.

## Verify offline

```sh
uv run python -m unittest discover -s tests -v
```

Tests use fake sandboxes and model responses. They do not create cloud resources or make paid API calls. TypeSafe integration follows the [System One API](https://docs.typesafe.ai/api) and [Choice primitive](https://docs.typesafe.ai/primitives/choice).

# Run GitHub Actions jobs on Celesto Cloud

Install this small controller on a Celesto Cloud computer, then point a job in your private GitHub repository at `runs-on: [self-hosted, celesto-cloud]`. The controller finds queued jobs, creates one disposable Celesto computer per job, and deletes that computer when GitHub finishes. Your laptop can stay off. GitHub Actions keeps the usual job status and logs.

This first version handles one private repository and one queued `celesto-cloud` job at a time. If two jobs queue, it waits until you cancel one; this keeps the disposable runner attached to the job the controller will monitor. Add a workflow concurrency group if repeat pushes are likely. It polls GitHub every 20 seconds, so it needs no public webhook or inbound port. The controller computer itself stays on and is billed while running. Job computers are billed for their runtime. Docker-based actions and service containers are not supported unless the job image has Docker installed.

## Failure cases to prove

The live acceptance must check: a job that is queued without a runner; a GitHub API error; a Celesto creation error; a runner download or registration error; controller restart while a job computer exists; a completed, failed, or cancelled job; an uncertain computer deletion; two queued jobs; and a job computer that exceeds its time limit. The first pilot may report manual intervention for ambiguous creation or whole-controller loss, but must not claim those cases are automatically resolved.

## Setup

1. Use a private test repository and a Celesto organization with enough balance for the always-on controller and short-lived jobs. Install a GitHub App on only that repository with repository **Actions: read** and **Administration: write**. Download its private key and note the App and installation IDs. For a quick private pilot, a token with repository admin access may be set as `GITHUB_TOKEN` instead of the App settings.
2. Create one persistent Celesto Cloud computer with the `coding-agent` template for the controller, preferably with an external volume. It does not need a published port. Open its terminal, clone the Celesto repository at the commit containing this example, and run `uv sync`. Job computers use the same template because the default `scratch` template lacks Git and Python.
3. Copy `.env.example` to `/root/celesto-ci/controller.env`, fill in the values, and set file mode `0600`. Put the GitHub App PEM at `/root/celesto-ci/github-app.pem` with the same permissions. Set `CELESTO_CONTROLLER_COMPUTER_ID` to the persistent computer's ID. Do not commit credentials or the SQLite database.
4. Run `uv run python controller.py --once` to verify GitHub access. Run `sh start.sh` to launch a detached process that restarts the controller after a crash. Read `/root/celesto-ci/controller.log` for job lifecycle messages. Celesto's `coding-agent` image does not have systemd; if you restart the whole controller computer, run `sh start.sh` again from its terminal.
5. Change one simple job in the test repository:

   ```yaml
   runs-on: [self-hosted, celesto-cloud]
   timeout-minutes: 120
   ```

The controller needs outbound HTTPS to GitHub and the Celesto API. The job computer needs outbound HTTPS to GitHub Actions and action download hosts. Do not route untrusted fork pull requests to this pilot runner.

The GitHub token, App key, and runner registration token are sensitive. Enter controller secrets through its terminal or another private secret channel. Celesto's command API can retain command text, so do not use `computer.run()` to write long-lived secrets. The registration token is short lived but currently crosses the command API during runner setup; use this pilot only with a repository you control until that handoff is hardened.

## Acceptance receipt

After pushing a commit with the changed job, record the GitHub run and job URLs, job conclusion, controller computer ID, disposable job computer ID, create/delete timestamps, and final Celesto computer state in a JSON receipt. Exclude all tokens, private keys, command payloads, and private source. The run is complete only when GitHub shows the job result and Celesto shows that its job computer was deleted. Repeat once after restarting the controller process during a queued or running job.

## Recovery and rollback

The SQLite ledger makes the controller retry cleanup after a process restart. If creation returns an ambiguous error or the whole controller computer is lost, list computers in the pilot Celesto organization and manually delete any job computers left behind. No automated sweep deletes an unrecognized computer because it might belong to someone else.

To stop the pilot, revert the job to `ubuntu-latest`, stop the controller, delete all remaining job computers, then delete the controller computer. Revoke the GitHub App installation or pilot token after the demo.

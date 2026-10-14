# Legacy report fetcher computer-use demo

This demo shows an agent using a browser to get reports from an old web app and hand those reports to a normal data pipeline.

The workflow runs in a Celesto browser session, a browser in its own isolated computer. The fake Acme portal starts inside that computer, the agent uses the browser, the files are checked inside the computer, and the final reports are copied back to your machine for the pipeline.

## What it demonstrates

- An agent can use a legacy web app when there is no API.
- Celesto gives the agent an isolated computer with a live browser you can watch.
- The workflow does not trust the agent saying “done”; it checks that the files exist.
- A shell inside the computer can list and recover report files when browser downloads are unreliable.
- The harness copies verified files from the computer to your machine before running the pipeline.

## Run it

This demo needs two Python packages on your machine: `openai` for the computer-use model and `playwright` to connect to the browser over CDP.

```bash
export OPENAI_API_KEY=...
uv run --with openai --with playwright examples/cua/legacy_report_fetcher/run_demo.py --mode live
```

Open the printed live URL to watch the browser.

For a quieter run without the live browser view:

```bash
uv run --with openai --with playwright examples/cua/legacy_report_fetcher/run_demo.py --mode headless
```

Optional flags:

```bash
--report-date 2026-05-07   # defaults to yesterday
--max-steps 24             # max computer-use turns
--boot-timeout 180         # seconds to wait for the computer to boot
```

## What you should see

The script prints progress as it moves through the workflow:

```txt
Starting Celesto browser session...
Starting Acme legacy portal inside the browser session...
Starting OpenAI computer-use browser task...
Listing browser session downloads and copying reports to your machine...
Running the existing-pipeline import on the handoff folder on your machine...
```

A successful run ends with pipeline output like:

```txt
Found manifest.json for acme_legacy_reports
Imported orders_2026-05-07.csv: 3 rows into orders
Imported inventory_2026-05-07.csv: 3 rows into inventory
Stored normalized data in .../artifacts/warehouse/acme.sqlite
Run complete.
```

## Output

Generated files appear under:

```txt
examples/cua/legacy_report_fetcher/artifacts/
  inbox/acme/<report-date>/
    orders_<report-date>.csv
    inventory_<report-date>.csv
    manifest.json
  warehouse/
    acme.sqlite
  screenshots/
    01-portal-login.png
    02-after-downloads.png
```

Browser session logs and video are collected in the Celesto browser artifacts directory printed by the script.

## Fake portal credentials

```txt
username: ops@acme.test
password: demo-password
```

## How it works

```txt
Folder on your machine, shared with the computer
└── /workspace/legacy_report_fetcher
    ├── portal/      # fake Acme Legacy Reports Portal
    ├── ops/         # helper scripts that run inside the computer
    ├── pipeline/    # existing-pipeline stand-in
    └── artifacts/   # handoff output on your machine
```

The browser opens the portal at:

```txt
http://127.0.0.1:8000
```

That server runs inside the Celesto computer, not on your machine.

The important reliability step is after the agent finishes. The harness lists the download folder inside the computer, recovers files if needed, copies the verified CSVs to your machine, writes `manifest.json`, and then runs the pipeline.

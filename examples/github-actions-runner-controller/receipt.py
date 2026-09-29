"""Save an independently checkable receipt for one live GitHub Actions job."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx

from controller import Config, Github, JobStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify a GitHub job and its Celesto computer cleanup")
    parser.add_argument("job_id", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    config = Config.from_env()
    github = Github(config)
    store = JobStore(config.state_db)
    try:
        rows = [row for row in store.rows("deleted") if row["job_id"] == args.job_id]
        if len(rows) != 1 or not rows[0]["computer_id"]:
            raise SystemExit("The ledger does not show a deleted computer for this job.")
        row = rows[0]
        job = github.job(args.job_id)
        if job["status"] != "completed":
            raise SystemExit("GitHub has not completed this job.")
        response = httpx.get(
            f"{config.celesto_base_url}/v1/computers/{row['computer_id']}",
            headers={
                "Authorization": f"Bearer {config.celesto_key}",
                "x-current-organization": config.celesto_organization_id,
            },
            timeout=20,
        )
        if response.status_code != 404:
            raise SystemExit(
                f"Celesto still returns computer {row['computer_id']}: HTTP {response.status_code}"
            )
        receipt = {
            "verified_at": datetime.now(UTC).isoformat(),
            "repository": config.repository,
            "github_job_id": args.job_id,
            "github_run_id": row["run_id"],
            "github_job_url": job["html_url"],
            "github_status": job["status"],
            "github_conclusion": job["conclusion"],
            "controller_computer_id": config.controller_computer_id,
            "job_computer_id": row["computer_id"],
            "celesto_get_status": 404,
            "computer_deleted": True,
        }
        output = args.output or Path("artifacts") / f"ci-job-{args.job_id}.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(receipt, indent=2) + "\n")
        print(output)
    finally:
        store.close()
        github.close()


if __name__ == "__main__":
    main()

"""Single-repository GitHub Actions runner controller hosted on Celesto Cloud."""

from __future__ import annotations

import argparse
import logging
import os
import shlex
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import jwt
from celesto import CloudComputer, VMNotFoundError

LOG = logging.getLogger("celesto_ci")
RUNNER_LABEL = "celesto-cloud"
POLL_SECONDS = 20
MAX_JOB_AGE = timedelta(hours=2)


def now() -> datetime:
    return datetime.now(UTC)


def timestamp() -> str:
    return now().isoformat()


@dataclass(frozen=True)
class Config:
    repository: str
    celesto_key: str = field(repr=False)
    celesto_organization_id: str
    celesto_base_url: str
    controller_computer_id: str
    state_db: Path
    github_token: str | None = field(repr=False)
    github_app_id: str | None
    github_installation_id: str | None
    github_private_key_file: Path | None

    @classmethod
    def from_env(cls) -> Config:
        repository = os.environ.get("GITHUB_REPOSITORY", "").strip()
        if repository.count("/") != 1 or not all(repository.split("/")):
            raise ValueError("Set GITHUB_REPOSITORY to OWNER/REPO.")
        celesto_key = os.environ.get("CELESTO_API_KEY", "").strip()
        if not celesto_key:
            raise ValueError("Set CELESTO_API_KEY for the controller's Celesto account.")
        organization_id = os.environ.get("CELESTO_ORGANIZATION_ID", "").strip()
        if not organization_id:
            raise ValueError("Set CELESTO_ORGANIZATION_ID for the controller and job computers.")
        github_token = os.environ.get("GITHUB_TOKEN", "").strip() or None
        app_id = os.environ.get("GITHUB_APP_ID", "").strip() or None
        installation_id = os.environ.get("GITHUB_INSTALLATION_ID", "").strip() or None
        key_path = os.environ.get("GITHUB_APP_PRIVATE_KEY_FILE", "").strip()
        if not github_token and not (app_id and installation_id and key_path):
            raise ValueError(
                "Set GITHUB_TOKEN, or set the GitHub App ID, installation ID, and private key file."
            )
        if key_path and not Path(key_path).is_file() and not github_token:
            raise ValueError("GITHUB_APP_PRIVATE_KEY_FILE does not exist.")
        return cls(
            repository=repository,
            celesto_key=celesto_key,
            celesto_organization_id=organization_id,
            celesto_base_url=os.environ.get("CELESTO_BASE_URL", "https://api.celesto.ai").rstrip("/"),
            controller_computer_id=os.environ.get("CELESTO_CONTROLLER_COMPUTER_ID", "").strip(),
            state_db=Path(os.environ.get("CELESTO_CI_STATE_DB", "./jobs.sqlite3")),
            github_token=github_token,
            github_app_id=app_id,
            github_installation_id=installation_id,
            github_private_key_file=Path(key_path) if key_path else None,
        )


class Github:
    def __init__(self, config: Config):
        self.config = config
        self.client = httpx.Client(base_url="https://api.github.com", timeout=20)
        self._installation_token: str | None = None
        self._installation_expires = now()

    def close(self) -> None:
        self.client.close()

    def _token(self) -> str:
        if self.config.github_token:
            return self.config.github_token
        if self._installation_token and now() < self._installation_expires - timedelta(minutes=2):
            return self._installation_token
        assert self.config.github_app_id and self.config.github_installation_id
        assert self.config.github_private_key_file
        current = int(time.time())
        app_jwt = jwt.encode(
            {"iat": current - 60, "exp": current + 540, "iss": self.config.github_app_id},
            self.config.github_private_key_file.read_text(),
            algorithm="RS256",
        )
        response = self.client.post(
            f"/app/installations/{self.config.github_installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {app_jwt}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        response.raise_for_status()
        payload = response.json()
        self._installation_token = payload["token"]
        self._installation_expires = datetime.fromisoformat(payload["expires_at"])
        return self._installation_token

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self.client.request(
            method,
            path,
            headers={
                "Authorization": f"Bearer {self._token()}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            **kwargs,
        )
        response.raise_for_status()
        return response.json() if response.content else None

    def path(self, suffix: str) -> str:
        return f"/repos/{self.config.repository}{suffix}"

    def queued_jobs(self) -> list[dict[str, Any]]:
        runs = self.request("GET", self.path("/actions/runs"), params={"per_page": 30})["workflow_runs"]
        queued: list[dict[str, Any]] = []
        for run in runs:
            if run["status"] == "completed":
                continue
            jobs = self.request(
                "GET", self.path(f"/actions/runs/{run['id']}/jobs"), params={"per_page": 100}
            )["jobs"]
            for job in jobs:
                if job["status"] == "queued" and RUNNER_LABEL in job.get("labels", []):
                    queued.append(job)
        return queued

    def job(self, job_id: int) -> dict[str, Any]:
        return self.request("GET", self.path(f"/actions/jobs/{job_id}"))

    def runner_download_url(self) -> str:
        builds = self.request("GET", self.path("/actions/runners/downloads"))
        for build in builds:
            if build.get("os") == "linux" and build.get("architecture") == "x64":
                url = str(build["download_url"])
                parsed = urlparse(url)
                if parsed.scheme != "https" or parsed.hostname != "github.com":
                    raise ValueError("GitHub returned an unexpected runner download URL.")
                return url
        raise RuntimeError("GitHub did not offer a Linux x64 runner build.")

    def registration_token(self) -> str:
        return self.request("POST", self.path("/actions/runners/registration-token"))["token"]

    def remove_stale_runner(self, runner_name: str) -> None:
        result = self.request("GET", self.path("/actions/runners"), params={"per_page": 100})
        for runner in result["runners"]:
            if runner["name"] == runner_name:
                self.request("DELETE", self.path(f"/actions/runners/{runner['id']}"))


class JobStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(mode=0o600, exist_ok=True)
        os.chmod(path, 0o600)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id INTEGER PRIMARY KEY,
                run_id INTEGER NOT NULL,
                html_url TEXT NOT NULL,
                state TEXT NOT NULL,
                github_status TEXT NOT NULL,
                conclusion TEXT,
                computer_id TEXT,
                runner_name TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def record_queued(self, job: dict[str, Any]) -> None:
        job_id = int(job["id"])
        self.connection.execute(
            """INSERT OR IGNORE INTO jobs
            (job_id, run_id, html_url, state, github_status, runner_name, created_at, updated_at)
            VALUES (?, ?, ?, 'pending', 'queued', ?, ?, ?)""",
            (job_id, int(job["run_id"]), job["html_url"], f"celesto-{job_id}", timestamp(), timestamp()),
        )
        self.connection.commit()

    def rows(self, *states: str) -> list[sqlite3.Row]:
        placeholders = ",".join("?" for _ in states)
        return list(
            self.connection.execute(
                f"SELECT * FROM jobs WHERE state IN ({placeholders}) ORDER BY created_at, job_id", states
            )
        )

    def known_computer_ids(self) -> set[str]:
        return {
            row[0]
            for row in self.connection.execute(
                "SELECT DISTINCT computer_id FROM jobs WHERE computer_id IS NOT NULL"
            )
        }

    def update(self, job_id: int, **fields: Any) -> None:
        allowed = {"state", "github_status", "conclusion", "computer_id", "attempts", "error"}
        if not fields or not set(fields) <= allowed:
            raise ValueError("Invalid job update.")
        fields["updated_at"] = timestamp()
        assignments = ", ".join(f"{key} = ?" for key in fields)
        self.connection.execute(f"UPDATE jobs SET {assignments} WHERE job_id = ?", (*fields.values(), job_id))
        self.connection.commit()


def computer(config: Config, computer_id: str | None = None) -> CloudComputer:
    options = {
        "api_key": config.celesto_key,
        "organization_id": config.celesto_organization_id,
        "base_url": config.celesto_base_url,
    }
    if computer_id:
        return CloudComputer.get(computer_id, **options)
    return CloudComputer(
        lifetime="persistent",
        template_id="coding-agent",
        startup_timeout=180,
        cleanup_timeout=180,
        **options,
    )


def run_checked(
    target: CloudComputer, command: str, *, timeout: int = 300, secret: str | None = None
) -> None:
    result = target.run(command, timeout=timeout)
    if result.exit_code != 0:
        detail = (result.stderr or result.stdout)[-500:]
        if secret:
            detail = detail.replace(secret, "[redacted]")
        raise RuntimeError(f"Runner setup command failed ({result.exit_code}): {detail}")


def provision(config: Config, github: Github, store: JobStore, row: sqlite3.Row) -> None:
    job_id = row["job_id"]
    target = computer(config)
    store.update(job_id, state="provisioning", attempts=row["attempts"] + 1, error=None)
    try:
        target.start()
        if not target.id:
            raise RuntimeError("Celesto did not return a computer ID.")
        store.update(job_id, computer_id=target.id)
        LOG.info("Created job computer %s for GitHub job %s", target.id, job_id)
        download_url = github.runner_download_url()
        run_checked(
            target,
            "set -eu; mkdir -p /tmp/celesto-actions-runner; cd /tmp/celesto-actions-runner; "
            f"curl -fL --retry 2 {shlex.quote(download_url)} -o runner.tar.gz; "
            "tar -xzf runner.tar.gz; rm runner.tar.gz",
        )
        run_checked(
            target,
            "set -eu; export DEBIAN_FRONTEND=noninteractive; "
            "apt-get update -qq; apt-get install -y -qq libicu74",
            timeout=300,
        )
        registration_token = github.registration_token()
        run_checked(
            target,
            "set -eu; cd /tmp/celesto-actions-runner; "
            "RUNNER_ALLOW_RUNASROOT=1 ./config.sh --unattended --ephemeral "
            f"--url {shlex.quote('https://github.com/' + config.repository)} "
            f"--token {shlex.quote(registration_token)} "
            f"--name {shlex.quote(row['runner_name'])} --labels {RUNNER_LABEL}",
            secret=registration_token,
        )
        run_checked(
            target,
            "set -eu; cd /tmp/celesto-actions-runner; "
            "setsid env RUNNER_ALLOW_RUNASROOT=1 ./run.sh "
            ">/tmp/celesto-actions-runner.log 2>&1 </dev/null & "
            "sleep 2; kill -0 $!",
            timeout=30,
        )
        store.update(job_id, state="online")
        LOG.info("Runner %s is online for job %s", row["runner_name"], job_id)
    except Exception as error:
        LOG.exception("Provisioning failed for GitHub job %s", job_id)
        if target.id:
            store.update(job_id, computer_id=target.id, state="deleting", error=str(error)[:500])
            if cleanup(config, github, store, job_id, target.id, row["runner_name"]):
                if row["attempts"] + 1 < 3:
                    store.update(job_id, state="pending", computer_id=None, error=str(error)[:500])
                else:
                    store.update(job_id, state="failed", error=str(error)[:500])
        else:
            store.update(job_id, state="failed", error=str(error)[:500])


def cleanup(
    config: Config, github: Github, store: JobStore, job_id: int, computer_id: str, runner_name: str
) -> bool:
    store.update(job_id, state="deleting")
    try:
        computer(config, computer_id).delete()
    except VMNotFoundError:
        pass
    except Exception as error:
        LOG.exception("Could not delete Celesto computer %s; will retry", computer_id)
        store.update(job_id, error=str(error)[:500])
        return False
    try:
        github.remove_stale_runner(runner_name)
    except (httpx.HTTPError, KeyError, ValueError) as error:
        LOG.warning("Computer deleted but runner cleanup failed for %s: %s", runner_name, error)
        store.update(job_id, error=str(error)[:500])
        return False
    store.update(job_id, state="deleted", error=None)
    LOG.info("Deleted job computer %s for GitHub job %s", computer_id, job_id)
    return True


def reconcile(config: Config, github: Github, store: JobStore) -> None:
    for row in store.rows("online", "provisioning", "deleting"):
        job_id = row["job_id"]
        computer_id = row["computer_id"]
        if row["state"] == "deleting":
            if computer_id:
                cleanup(config, github, store, job_id, computer_id, row["runner_name"])
            continue
        age = now() - datetime.fromisoformat(row["created_at"])
        if age > MAX_JOB_AGE:
            LOG.warning("Job %s exceeded the two-hour computer limit", job_id)
            if computer_id:
                cleanup(config, github, store, job_id, computer_id, row["runner_name"])
            else:
                store.update(job_id, state="failed", error="Computer creation exceeded the two-hour limit.")
            continue
        if row["state"] == "provisioning" and now() - datetime.fromisoformat(row["updated_at"]) > timedelta(
            minutes=5
        ):
            if computer_id:
                try:
                    if github.job(job_id)["status"] == "in_progress":
                        store.update(job_id, state="online", github_status="in_progress")
                        continue
                except httpx.HTTPError:
                    LOG.warning("Could not verify interrupted runner %s; will retry next check", job_id)
                    continue
                if cleanup(config, github, store, job_id, computer_id, row["runner_name"]):
                    if row["attempts"] < 3:
                        store.update(
                            job_id,
                            state="pending",
                            computer_id=None,
                            error="Retrying after an interrupted setup.",
                        )
                    else:
                        store.update(
                            job_id, state="failed", error="Runner setup was interrupted three times."
                        )
            else:
                store.update(
                    job_id,
                    state="failed",
                    error="Provisioning interrupted before computer ID was saved; inspect Celesto computers.",
                )
            continue
        if not computer_id:
            continue
        try:
            job = github.job(job_id)
        except Exception:
            LOG.exception("Could not read GitHub job %s; leaving computer running until next check", job_id)
            continue
        status = job["status"]
        store.update(job_id, github_status=status, conclusion=job.get("conclusion"))
        if status == "completed":
            cleanup(config, github, store, job_id, computer_id, row["runner_name"])


def audit_unknown_computers(config: Config, store: JobStore) -> None:
    """Report ambiguous creates for manual cleanup; never delete an unknown computer."""
    if not config.controller_computer_id:
        LOG.warning("Set CELESTO_CONTROLLER_COMPUTER_ID to audit unknown pilot computers")
        return
    response = httpx.get(
        f"{config.celesto_base_url}/v1/computers",
        headers={
            "Authorization": f"Bearer {config.celesto_key}",
            "x-current-organization": config.celesto_organization_id,
        },
        params={"limit": 200},
        timeout=20,
    )
    response.raise_for_status()
    known = store.known_computer_ids() | {config.controller_computer_id}
    for item in response.json()["computers"]:
        if item["id"] not in known and item["status"] in {"creating", "starting", "running"}:
            LOG.warning(
                "Unknown active Celesto computer %s; inspect and delete manually if it belongs to CI",
                item["id"],
            )


def tick(config: Config, github: Github, store: JobStore) -> None:
    reconcile(config, github, store)
    queued = github.queued_jobs()
    for job in queued:
        store.record_queued(job)
    if len(queued) > 1:
        LOG.warning(
            "Found %s queued Celesto jobs. This pilot starts no runner until only one remains; "
            "cancel extra runs or add workflow concurrency.",
            len(queued),
        )
        return
    active = store.rows("provisioning", "online", "deleting")
    if active:
        return
    pending = store.rows("pending")
    if pending:
        row = pending[0]
        latest = github.job(row["job_id"])
        if latest["status"] == "queued":
            provision(config, github, store, row)
        elif latest["status"] == "completed":
            store.update(
                row["job_id"], state="deleted", github_status="completed", conclusion=latest.get("conclusion")
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run GitHub Actions jobs on Celesto Cloud")
    parser.add_argument("--once", action="store_true", help="Check GitHub and the job ledger once, then exit")
    arguments = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = Config.from_env()
    github = Github(config)
    store = JobStore(config.state_db)
    LOG.info("Watching %s for queued jobs with %s", config.repository, RUNNER_LABEL)
    try:
        checks = 0
        while True:
            try:
                tick(config, github, store)
                if checks % 30 == 0:
                    audit_unknown_computers(config, store)
            except Exception:
                LOG.exception("Controller check failed; retrying")
                if arguments.once:
                    raise
            if arguments.once:
                return
            checks += 1
            time.sleep(POLL_SECONDS)
    finally:
        store.close()
        github.close()


if __name__ == "__main__":
    main()

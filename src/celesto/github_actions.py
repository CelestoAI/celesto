"""Commands for starting an ephemeral GitHub Actions runner on a Celesto computer."""

import re
import shlex
from urllib.parse import urlparse

RUNNER_LABEL = "celesto-cloud"
RUNNER_DIR = "/tmp/celesto-actions-runner"


def install_runner_command(download_url: str) -> str:
    """Download GitHub's current Linux runner and its Ubuntu 24.04 ICU dependency."""
    parsed = urlparse(download_url)
    if parsed.scheme != "https" or parsed.hostname != "github.com":
        raise ValueError("Runner download must come from github.com over HTTPS")
    return (
        f"set -eu; mkdir -p {RUNNER_DIR}; cd {RUNNER_DIR}; "
        f"curl -fL --proto-redir =https --retry 2 {shlex.quote(download_url)} -o runner.tar.gz; "
        "tar -xzf runner.tar.gz; rm runner.tar.gz; "
        "export DEBIAN_FRONTEND=noninteractive; "
        "apt-get update -qq; apt-get install -y -qq libicu74"
    )


def configure_runner_command(repository: str, token: str, runner_name: str) -> str:
    """Register one job VM with its repository as an ephemeral runner."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Repository must be OWNER/REPO")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", runner_name):
        raise ValueError("Runner name must contain only GitHub runner name characters")
    if not token:
        raise ValueError("Runner registration token is required")
    return (
        f"set -eu; cd {RUNNER_DIR}; "
        "RUNNER_ALLOW_RUNASROOT=1 ./config.sh --unattended --ephemeral "
        f"--url {shlex.quote('https://github.com/' + repository)} "
        f"--token {shlex.quote(token)} "
        f"--name {shlex.quote(runner_name)} --labels {RUNNER_LABEL}"
    )


def start_runner_command() -> str:
    """Run the configured runner after the Celesto command request exits."""
    return (
        f"set -eu; cd {RUNNER_DIR}; "
        "setsid env RUNNER_ALLOW_RUNASROOT=1 ./run.sh "
        ">/tmp/celesto-actions-runner.log 2>&1 </dev/null & "
        "sleep 2; kill -0 $!"
    )

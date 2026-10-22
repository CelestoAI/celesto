# Copyright 2026 Celesto AI
# Licensed under the Apache License, Version 2.0
"""D-13 end to end: GitHub SSH URLs go over HTTPS; only allowed keys sign.

Boots one Ubuntu computer through the CLI inventory, allows one of two
throwaway keys with the real ``celesto computer ssh-key add`` command, runs
the filtered agent with :func:`celesto.credentials.ssh.serve`, and checks
from inside the guest. The user's own SSH agent and keys are never used.

Writes a JSON result file to ``$CELESTO_E2E_ARTIFACTS`` (or the test's
tmp dir) so the run can be inspected and repeated.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from _util import BOOT_TIMEOUT

from celesto.cli.service import CLIService
from celesto.credentials import ssh as cssh
from tests.credentials._agent_lab import Lab, _clean_env, make_lab

pytestmark = pytest.mark.e2e

SANDBOX = "w6-ssh-e2e"


def _artifact_dir(tmp_path: Path) -> Path:
    target = Path(os.environ.get("CELESTO_E2E_ARTIFACTS", tmp_path))
    target.mkdir(parents=True, exist_ok=True)
    return target


@pytest.fixture
def agent_lab() -> Iterator[Lab]:
    with make_lab() as started:
        yield started


def test_filtered_agent_and_github_https_rewrite(agent_lab: Lab, tmp_path: Path) -> None:
    lab = agent_lab
    service = CLIService()
    results: dict[str, object] = {"sandbox": SANDBOX, "checks": {}}
    checks: dict[str, object] = results["checks"]  # type: ignore[assignment]
    agent_service: cssh.SshAgentService | None = None
    # Create through the real CLI, with the user's SSH agent out of reach.
    create_env = {k: v for k, v in os.environ.items() if k != "SSH_AUTH_SOCK"}
    create_env["CELESTO_DATA_DIR"] = str(service.data_dir)
    created = subprocess.run(
        [sys.executable, "-c", "from celesto.cli.main import main; raise SystemExit(main())"]
        + ["computer", "create", "-n", SANDBOX, "--os", "ubuntu", "--json"],
        env=create_env,
        capture_output=True,
        text=True,
        timeout=BOOT_TIMEOUT + 600,
    )
    assert created.returncode == 0, created.stdout + created.stderr
    vm = service.vm_from_id(SANDBOX, comm_channel="ssh")
    try:
        # Allow exactly one key, through the real CLI.
        cli_env = _clean_env(
            HOME=str(lab.home),
            SSH_AUTH_SOCK=str(lab.agent_sock),
            CELESTO_DATA_DIR=str(service.data_dir),
            CELESTO_DISABLE_VERSION_CHECK="1",
            CELESTO_NO_TELEMETRY="1",
        )
        added = subprocess.run(
            [sys.executable, "-c", "from celesto.cli.main import main; raise SystemExit(main())"]
            + ["computer", "ssh-key", "add", SANDBOX, f"{lab.allowed_key}.pub", "--json"],
            env=cli_env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        checks["ssh_key_add"] = json.loads(added.stdout)
        assert added.returncode == 0, added.stdout + added.stderr

        # Guest wiring (what the start flow installs) and the per-VM agent.
        setup = vm.run(cssh.guest_setup_script(), shell="raw")
        assert setup.exit_code == 0, setup.stderr
        vm.set_env_vars(cssh.guest_env())
        agent_service = cssh.serve(
            {
                "sandbox_id": SANDBOX,
                "ssh": {
                    "host_agent_socket": str(lab.agent_sock),
                    "data_dir": str(service.data_dir),
                },
            }
        )
        assert agent_service.forward.ready.wait(60), "agent forward never became ready"

        def guest(command: str, shell: str = "login") -> dict[str, object]:
            result = vm.run(command, timeout=120, shell=shell)  # type: ignore[arg-type]
            return {
                "command": command,
                "shell": shell,
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        listed = guest("ssh-add -l")
        checks["ssh_add_list"] = listed
        assert listed["exit_code"] == 0
        assert lab.allowed_fp in str(listed["stdout"])
        assert lab.other_fp not in str(listed["stdout"])

        # Raw exec does not source the login profile; ssh still finds the agent.
        raw_env = guest('echo "SSH_AUTH_SOCK=${SSH_AUTH_SOCK:-}"; ssh -G example.com', "raw")
        checks["raw_exec_ssh_config"] = raw_env
        assert f"identityagent {cssh.GUEST_AGENT_SOCKET}" in str(raw_env["stdout"]).lower()

        # Sign with the allowed key works; the other key and agent changes fail.
        for name, key in (("allowed", lab.allowed_key), ("other", lab.other_key)):
            pub = shlex.quote(lab.pub(key).strip())
            checks[f"sign_{name}"] = guest(
                f"cd /tmp && printf %s {pub} > w6-{name}.pub && echo hi > w6-data && "
                f"rm -f w6-data.sig && ssh-keygen -Y sign -n file -f w6-{name}.pub w6-data"
            )
        assert checks["sign_allowed"]["exit_code"] == 0  # type: ignore[index]
        assert checks["sign_other"]["exit_code"] != 0  # type: ignore[index]
        checks["remove_all"] = guest("ssh-add -D")
        assert checks["remove_all"]["exit_code"] != 0  # type: ignore[index]
        host_keys = lab.fingerprints(lab.agent_sock)
        checks["host_agent_after"] = host_keys
        assert lab.allowed_fp in host_keys and lab.other_fp in host_keys

        # GitHub SSH URLs go over HTTPS, without any SSH key.
        rewrite = guest("git config --global --get-regexp url")
        checks["git_url_rewrite"] = rewrite
        for prefix in cssh.GITHUB_SSH_PREFIXES:
            assert f"url.https://github.com/.insteadof {prefix}" in str(rewrite["stdout"])
        ls_remote = guest(
            "GIT_SSH_COMMAND=false git ls-remote git@github.com:octocat/Hello-World.git HEAD"
        )
        checks["git_ls_remote"] = ls_remote
        assert ls_remote["exit_code"] == 0, ls_remote
        assert "HEAD" in str(ls_remote["stdout"])
        checks["git_ls_remote_raw"] = guest(
            "GIT_SSH_COMMAND=false git ls-remote ssh://git@github.com/octocat/Hello-World.git HEAD",
            "raw",
        )

        # Live allow-list change: removing the key hides it without a restart.
        removed = subprocess.run(
            [sys.executable, "-c", "from celesto.cli.main import main; raise SystemExit(main())"]
            + ["computer", "ssh-key", "remove", SANDBOX, lab.allowed_fp, "--json"],
            env=cli_env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert removed.returncode == 0
        after = guest("ssh-add -l")
        checks["ssh_add_list_after_remove"] = after
        assert lab.allowed_fp not in str(after["stdout"])

        # No private key material anywhere in the guest.
        # The first body line is a header shared by every unencrypted key;
        # the remaining lines hold this key's material.
        secret_lines = lab.allowed_key.read_text().splitlines()[2:-1]
        patterns = " ".join(f"-e {shlex.quote(line)}" for line in secret_lines)
        scan = guest(
            f"grep -rIlF {patterns} /root /etc /run /tmp /home 2>/dev/null; true",
            "raw",
        )
        checks["private_key_scan"] = {"exit_code": scan["exit_code"], "hits": scan["stdout"]}
        assert str(scan["stdout"]).strip() == ""
        results["ok"] = True
    finally:
        results.setdefault("ok", False)
        results["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        artifact = _artifact_dir(tmp_path) / "w6-ssh-e2e.json"
        artifact.write_text(json.dumps(results, indent=2, default=str))
        print(f"artifact: {artifact}")
        if agent_service is not None:
            agent_service.stop()
        vm.delete()

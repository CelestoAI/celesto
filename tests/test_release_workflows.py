import tomllib
from pathlib import Path

_WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"


def test_package_release_accepts_standard_and_namespaced_version_tags() -> None:
    workflow = (_WORKFLOWS / "publish.yml").read_text(encoding="utf-8")

    assert '- "v*.*.*"' in workflow
    assert '- "celesto-v*.*.*"' in workflow
    assert 'expected_tags = (f"v{version}", f"celesto-v{version}")' in workflow
    assert "if tag not in expected_tags:" in workflow


def test_dashboard_release_accepts_standard_and_namespaced_version_tags() -> None:
    workflow = (_WORKFLOWS / "publish-dashboard-ui.yml").read_text(encoding="utf-8")

    assert '- "v*.*.*"' in workflow
    assert '- "celesto-v*.*.*"' in workflow


def test_celesto_dependency_tracks_the_core_release_version() -> None:
    repository = _WORKFLOWS.parents[1]
    project = tomllib.loads((repository / "pyproject.toml").read_text(encoding="utf-8"))
    core_project = tomllib.loads(
        (repository / "celesto-core" / "Cargo.toml").read_text(encoding="utf-8")
    )

    core_dependency = next(
        dependency
        for dependency in project["project"]["dependencies"]
        if dependency.startswith("celesto-core")
    )
    assert core_dependency == f"celesto-core~={core_project['package']['version']}"


def test_installer_smoke_reports_create_error(tmp_path: Path) -> None:
    import os
    import subprocess
    import textwrap

    workflow = (_WORKFLOWS / "install-script-e2e.yml").read_text()
    step_start = "      - name: Create and exercise a sandbox\n        run: |\n"
    step_end = "\n      - name: Show sandbox logs after failure"
    script = textwrap.dedent(workflow.split(step_start, 1)[1].split(step_end, 1)[0])
    script = script.replace("${{ matrix.backend }}", "firecracker")
    cli = tmp_path / "celesto"
    cli.write_text(
        '#!/bin/sh\nprintf \'{"ok":false,"error":{"message":"image unavailable"}}\\n\'\nexit 1\n'
    )
    cli.chmod(0o755)

    result = subprocess.run(
        ["bash", "-e", "-c", script],
        env={
            **os.environ,
            "CELESTO_BIN": str(cli),
            "RUNNER_TEMP": str(tmp_path),
            "SANDBOX_NAME": "install-script-smoke",
        },
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "image unavailable" in result.stdout

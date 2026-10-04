import re
import tomllib
from pathlib import Path

_WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"

_SETUP_PYTHON = "actions/setup-python"
_BLOCK_SCALAR = re.compile(r"[|>][+-]?\d*")
_EXPRESSION = re.compile(r"\$\{\{.*\}\}")
_VERSION_SPEC = re.compile(r"[0-9A-Za-z.*|<>=!~, -]+")


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _python_version_values(workflow: str) -> list[str]:
    """Every `python-version` passed to an `actions/setup-python` step.

    A block scalar (`|`, `>`, `|-`) resolves to several lines joined by
    newlines, so its lines are returned as one newline-separated string.
    """
    lines = workflow.splitlines()
    values: list[str] = []

    index = 0
    while index < len(lines):
        line = lines[index]
        if _SETUP_PYTHON not in line or "uses:" not in line:
            index += 1
            continue

        step_indent = _indent(line)
        index += 1
        while index < len(lines):
            current = lines[index]
            stripped = current.strip()
            if stripped and _indent(current) <= step_indent:
                break
            if stripped.startswith("python-version:"):
                raw = current.split("python-version:", 1)[1].strip()
                if _BLOCK_SCALAR.fullmatch(raw):
                    block: list[str] = []
                    index += 1
                    while index < len(lines) and (
                        not lines[index].strip() or _indent(lines[index]) > step_indent
                    ):
                        block.append(lines[index].strip())
                        index += 1
                    values.append("\n".join(part for part in block if part))
                    continue
                values.append(raw.strip("\"'"))
            index += 1

    return values


def test_setup_python_never_receives_a_list_of_versions() -> None:
    workflows = sorted(_WORKFLOWS.glob("*.y*ml"))
    assert workflows, "no workflows found to inspect"

    inspected = 0
    offenders: list[str] = []
    for workflow in workflows:
        for value in _python_version_values(workflow.read_text(encoding="utf-8")):
            inspected += 1
            name = f"{workflow.name}: python-version {value!r}"
            if "\n" in value:
                offenders.append(f"{name} is a list, not a single version or range")
            elif not _EXPRESSION.fullmatch(value) and not _VERSION_SPEC.fullmatch(value):
                offenders.append(f"{name} is not a version, range, or expression")

    assert inspected, "no actions/setup-python step found; the check below is vacuous"
    assert offenders == []


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

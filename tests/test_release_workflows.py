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

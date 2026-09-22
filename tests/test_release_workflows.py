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

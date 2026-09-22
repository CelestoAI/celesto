from pathlib import Path

_WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"


def test_package_release_uses_standard_version_tag() -> None:
    workflow = (_WORKFLOWS / "publish.yml").read_text(encoding="utf-8")

    assert '- "v*.*.*"' in workflow
    assert 'expected_tag = f"v{version}"' in workflow
    assert "celesto-v" not in workflow


def test_dashboard_release_uses_standard_version_tag() -> None:
    workflow = (_WORKFLOWS / "publish-dashboard-ui.yml").read_text(encoding="utf-8")

    assert '- "v*.*.*"' in workflow
    assert "celesto-v" not in workflow

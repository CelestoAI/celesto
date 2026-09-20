"""Guards for the clean-machine public installer smoke test."""

from pathlib import Path

_WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "install-script-e2e.yml"


def test_install_script_workflow_uses_only_the_public_installer() -> None:
    workflow = _WORKFLOW.read_text()

    assert "curl -fsSL https://celesto.ai/install.sh | bash" in workflow
    assert "actions/checkout" not in workflow
    assert "pip install" not in workflow
    assert "uv pip install" not in workflow
    assert "uv sync" not in workflow
    assert "install -e" not in workflow


def test_install_script_workflow_exercises_cli_lifecycle() -> None:
    workflow = _WORKFLOW.read_text()

    assert "os: ubuntu-latest\n            backend: firecracker" in workflow
    assert "os: macos-15-intel\n            backend: qemu" in workflow
    assert "runs-on: ${{ matrix.os }}" in workflow
    assert '--backend "${{ matrix.backend }}"' in workflow

    for command in (
        "sandbox create",
        "sandbox list",
        "sandbox exec",
        "sandbox stop",
        "sandbox delete",
    ):
        assert command in workflow

    assert "--start --json -- uname -s" in workflow
    assert "if: always()" in workflow

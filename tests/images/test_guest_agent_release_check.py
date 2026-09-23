"""Checks for the standalone binaries required by installed Celesto packages."""

import importlib.util
from pathlib import Path
from types import ModuleType


def _load_checker() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "scripts/ci/check_guest_agent_release.py"
    spec = importlib.util.spec_from_file_location("check_guest_agent_release", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_checker_requires_celesto_assets_with_pinned_digests() -> None:
    checker = _load_checker()
    pins = checker._constant(
        checker.ROOT / "src/celesto/images/builder.py", "_GUEST_AGENT_RELEASE_SHA256"
    )
    assets = [
        {"name": f"celesto-guest-agent-linux-{arch}", "digest": f"sha256:{sha}"}
        for arch, sha in pins.items()
    ]

    assert checker.check(assets) == []
    assert len(checker.check(assets[:1])) == 1
    assert len(checker.check([assets[0], {**assets[1], "digest": "sha256:wrong"}])) == 1
    assert (
        len(
            checker.check(
                [{**asset, "name": asset["name"].replace("celesto", "smolvm")} for asset in assets]
            )
        )
        == 2
    )

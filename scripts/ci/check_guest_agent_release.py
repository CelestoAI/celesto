"""Verify that the pinned image release contains the guest agents used by wheels."""

import argparse
import ast
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _constant(path: Path, name: str) -> Any:
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            return ast.literal_eval(node.value)
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
            and node.value is not None
        ):
            return ast.literal_eval(node.value)
    raise ValueError(f"Could not find {name} in {path}")


def check(assets: list[dict[str, str]]) -> list[str]:
    builder = ROOT / "src/celesto/images/builder.py"
    published = ROOT / "src/celesto/images/published.py"
    tag = _constant(published, "IMAGES_RELEASE_TAG")
    pins = _constant(builder, "_GUEST_AGENT_RELEASE_SHA256")
    by_name = {asset["name"]: asset for asset in assets}
    errors = []
    for arch, expected_sha in pins.items():
        name = f"celesto-guest-agent-linux-{arch}"
        asset = by_name.get(name)
        if asset is None:
            errors.append(f"{tag} is missing {name}")
        elif asset.get("digest") != f"sha256:{expected_sha}":
            errors.append(f"{tag} has an unexpected SHA-256 for {name}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets-json", type=Path, help="Read release metadata from a file")
    args = parser.parse_args()
    tag = _constant(ROOT / "src/celesto/images/published.py", "IMAGES_RELEASE_TAG")
    if args.assets_json:
        payload = json.loads(args.assets_json.read_text())
    else:
        result = subprocess.run(
            ["gh", "release", "view", tag, "--repo", "CelestoAI/celesto", "--json", "assets"],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
    errors = check(payload["assets"])
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print(f"Guest-agent release assets and SHA-256 pins match {tag}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

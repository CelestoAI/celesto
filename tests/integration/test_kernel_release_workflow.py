"""Exercise the release upload shell against an isolated GitHub CLI fixture."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


@pytest.mark.parametrize("draft,force", [(False, True), (True, True), (False, False)])
def test_kernel_upload_preserves_published_release(
    tmp_path: Path, draft: bool, force: bool
) -> None:
    root = Path(__file__).resolve().parents[2]
    workflow = yaml.safe_load((root / ".github/workflows/build-microvm-kernel.yml").read_text())
    step = next(step for step in workflow["jobs"]["build"]["steps"] if step.get("id") == "upload")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    released = tmp_path / "released"
    released.mkdir()
    output = tmp_path / "kernel-out"
    output.mkdir()
    names = ["vmlinux-arm64." + fmt for fmt in ("elf", "image", "config")]
    for name in names:
        (released / name).write_bytes(b"published-kernel")
        (output / name).write_bytes(b"candidate-kernel")
    cli = fake_bin / "gh"
    cli.write_text(
        f"#!{sys.executable}\n"
        + r"""
import json, os, shutil, sys
from pathlib import Path
args = sys.argv[1:]
with Path(os.environ["CLI_LOG"]).open("a") as log:
    log.write(json.dumps(args) + "\n")
if args[:2] == ["release", "view"]:
    if "isDraft" in args:
        print(os.environ["RELEASE_DRAFT"])
    elif "assets" in args:
        print("\n".join(p.name for p in Path(os.environ["RELEASED"]).iterdir()))
elif args[:2] == ["release", "upload"]:
    source = Path(args[-1])
    shutil.copyfile(source, Path(os.environ["RELEASED"]) / source.name)
else:
    sys.exit("Unexpected GitHub CLI operation: " + repr(args))
"""
    )
    cli.chmod(0o755)
    env = {
        "PATH": str(fake_bin) + os.pathsep + os.defpath,
        "TAG": "existing-release",
        "ARCH": "arm64",
        "ASSET": "vmlinux-arm64",
        "GITHUB_REPOSITORY": "example/sdk",
        "GITHUB_OUTPUT": str(tmp_path / "outputs"),
        "FORCE_OVERWRITE": str(force).lower(),
        "RELEASE_DRAFT": str(draft).lower(),
        "RELEASED": str(released),
        "CLI_LOG": str(tmp_path / "cli.jsonl"),
        "ELF_SHA": "new",
        "IMAGE_SHA": "new",
        "PINNED_ELF_SHA": "old",
        "PINNED_IMAGE_SHA": "old",
    }
    result = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", step["run"]],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    calls = [json.loads(line) for line in (tmp_path / "cli.jsonl").read_text().splitlines()]
    if force and not draft:
        assert result.returncode != 0, "Published release must reject forced replacement"
        assert not any(call[:2] == ["release", "upload"] for call in calls)
    else:
        assert result.returncode == 0, result.stderr
    expected = b"candidate-kernel" if draft and force else b"published-kernel"
    assert [(released / name).read_bytes() for name in names] == [expected] * len(names)

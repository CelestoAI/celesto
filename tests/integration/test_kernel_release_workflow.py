"""Exercise the release upload shell against an isolated GitHub CLI fixture."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


@pytest.mark.parametrize(
    "draft,force,corrupt",
    [
        (False, True, False),
        (True, True, False),
        (True, False, False),
        (False, False, False),
        (False, False, True),
    ],
)
def test_kernel_upload_preserves_published_release(
    tmp_path: Path, draft: bool, force: bool, corrupt: bool
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
        (released / name).write_bytes(b"tampered" if corrupt else b"published-kernel")
        (output / name).write_bytes(b"candidate-kernel")
    cli = fake_bin / "gh"
    cli.write_text(
        f"#!{sys.executable}\n"
        + r"""
import hashlib, json, os, shutil, sys
from pathlib import Path
args = sys.argv[1:]
with Path(os.environ["CLI_LOG"]).open("a") as log:
    log.write(json.dumps(args) + "\n")
if args[:2] == ["release", "view"]:
    if "isDraft" in args:
        print(os.environ["RELEASE_DRAFT"])
    elif "assets" in args:
        for asset in Path(os.environ["RELEASED"]).iterdir():
            print(asset.name + "\tsha256:" + hashlib.sha256(asset.read_bytes()).hexdigest())
elif args[0] == "api":
    if os.environ["RELEASE_DRAFT"] == "true":
        sys.exit("gh: Not Found (HTTP 404)")
    for asset in Path(os.environ["RELEASED"]).iterdir():
        print(asset.name + "\tsha256:" + hashlib.sha256(asset.read_bytes()).hexdigest())
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
        "PROFILE": "sandbox",
        "ASSET": "vmlinux-arm64",
        "GITHUB_REPOSITORY": "example/sdk",
        "GITHUB_OUTPUT": str(tmp_path / "outputs"),
        "FORCE_OVERWRITE": str(force).lower(),
        "RELEASE_DRAFT": str(draft).lower(),
        "RELEASED": str(released),
        "CLI_LOG": str(tmp_path / "cli.jsonl"),
        "ELF_SHA": "new",
        "IMAGE_SHA": "new",
        "PINNED_ELF_SHA": hashlib.sha256(b"published-kernel").hexdigest(),
        "PINNED_IMAGE_SHA": hashlib.sha256(b"published-kernel").hexdigest(),
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
    if (force and not draft) or corrupt:
        assert result.returncode != 0, (
            "Published release must reject replacement or a corrupt pinned asset"
        )
        assert not any(call[:2] == ["release", "upload"] for call in calls)
    else:
        assert result.returncode == 0, result.stderr
    if not draft and not force and not corrupt:
        assert "Bump ARM_KERNELS_RELEASE_TAG" in result.stdout
    expected = (
        b"candidate-kernel"
        if draft and force
        else (b"tampered" if corrupt else b"published-kernel")
    )
    assert [(released / name).read_bytes() for name in names] == [expected] * len(names)


@pytest.mark.parametrize(
    "event,input_tag,release_state,force,outcome",
    [
        ("push", "", "published", False, "skip"),
        ("push", "candidate", "draft", False, "skip"),
        ("unknown", "candidate", "draft", False, "skip"),
        ("workflow_dispatch", "", "published", False, "skip"),
        ("workflow_dispatch", "candidate", "published", False, "reject"),
        ("workflow_dispatch", "candidate", "published", True, "reject"),
        ("workflow_dispatch", "candidate", "draft", False, "upload"),
        ("workflow_dispatch", "candidate", "missing", False, "upload"),
    ],
)
def test_android_kernel_publication_requires_explicit_draft(
    tmp_path: Path,
    event: str,
    input_tag: str,
    release_state: str,
    force: bool,
    outcome: str,
) -> None:
    root = Path(__file__).resolve().parents[2]
    workflow = yaml.safe_load((root / ".github/workflows/build-microvm-kernel.yml").read_text())
    step = next(step for step in workflow["jobs"]["build"]["steps"] if step.get("id") == "upload")
    assert step["env"]["EVENT_NAME"] == "${{ github.event_name }}"
    assert step["env"]["INPUT_TAG"] == "${{ inputs.release_tag }}"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    released = tmp_path / "released"
    released.mkdir()
    output = tmp_path / "kernel-out"
    output.mkdir()
    names = ["vmlinux-github-ci-android-amd64." + fmt for fmt in ("elf", "image", "config")]
    for name in names:
        (output / name).write_bytes(b"unqualified-android-candidate")
    # Reproduce the real failure: an existing published release has ordinary
    # assets, but none of the Android filenames exist yet.
    (released / "vmlinux-amd64.image").write_bytes(b"ordinary-published-kernel")
    state = tmp_path / "release-state"
    state.write_text(release_state)
    cli = fake_bin / "gh"
    cli.write_text(
        f"#!{sys.executable}\n"
        + r"""
import hashlib, json, os, shutil, sys
from pathlib import Path
args = sys.argv[1:]
with Path(os.environ["CLI_LOG"]).open("a") as log:
    log.write(json.dumps(args) + "\n")
state = Path(os.environ["RELEASE_STATE"])
if args[:2] == ["release", "view"]:
    if state.read_text() == "missing":
        sys.exit("gh: release not found")
    if "isDraft" in args:
        print(str(state.read_text() == "draft").lower())
    elif "assets" in args:
        for asset in Path(os.environ["RELEASED"]).iterdir():
            print(asset.name + "\tsha256:" + hashlib.sha256(asset.read_bytes()).hexdigest())
elif args[:2] == ["release", "create"]:
    if "--draft" not in args:
        sys.exit("Refusing non-draft creation")
    state.write_text("draft")
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
        "TAG": input_tag or "existing-published-release",
        "ARCH": "amd64",
        "PROFILE": "github-ci-android",
        "EVENT_NAME": event,
        "INPUT_TAG": input_tag,
        "ASSET": "vmlinux-github-ci-android-amd64",
        "GITHUB_REPOSITORY": "example/sdk",
        "GITHUB_OUTPUT": str(tmp_path / "outputs"),
        "FORCE_OVERWRITE": str(force).lower(),
        "RELEASE_STATE": str(state),
        "RELEASED": str(released),
        "CLI_LOG": str(tmp_path / "cli.jsonl"),
        "ELF_SHA": "new",
        "IMAGE_SHA": "new",
        "PINNED_ELF_SHA": "",
        "PINNED_IMAGE_SHA": "",
    }
    result = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", step["run"]],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    calls = (
        [json.loads(line) for line in (tmp_path / "cli.jsonl").read_text().splitlines()]
        if (tmp_path / "cli.jsonl").exists()
        else []
    )
    uploads = [call for call in calls if call[:2] == ["release", "upload"]]
    assert (released / "vmlinux-amd64.image").read_bytes() == b"ordinary-published-kernel"
    if outcome == "skip":
        assert result.returncode == 0, result.stderr
        assert calls == [], "Automatic or implicit Android publication must not reach GitHub"
        assert "publication_skipped=true" in (tmp_path / "outputs").read_text()
    elif outcome == "reject":
        assert result.returncode != 0, "Even missing Android assets require a draft target"
        assert uploads == []
    else:
        assert result.returncode == 0, result.stderr
        draft_check = next(i for i, call in enumerate(calls) if "isDraft" in call)
        assert all(calls.index(call) > draft_check for call in uploads)
        assert [Path(call[-1]).name for call in uploads] == names
        assert state.read_text() == "draft"
    if outcome != "upload":
        assert sorted(path.name for path in released.iterdir()) == ["vmlinux-amd64.image"]


def test_negative_control_cannot_reuse_old_console(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    kernels = tmp_path / "kernels"
    kernels.mkdir()
    (kernels / "vmlinux-github-ci-amd64.image").write_bytes(b"candidate")
    guest = tmp_path / "guest"
    guest.mkdir()
    proof = tmp_path / "proof"
    run = proof / "run"
    run.mkdir(parents=True)
    (run / "sandbox-write.console.log").write_text("Sandbox kernel unexpectedly supports XFS\n")
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    for name, status in [("truncate", 0), ("mkfs.ext4", 1)]:
        command = fake_bin / name
        command.write_text(f"#!/bin/sh\nexit {status}\n")
        command.chmod(0o755)
    result = subprocess.run(
        [
            "bash",
            str(root / "kernel/microvm/smoke/reject-ci-as-sandbox.sh"),
            "amd64",
            str(kernels),
            str(guest),
            str(proof),
        ],
        env={"PATH": str(fake_bin) + os.pathsep + os.defpath},
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode != 0, "A pre-boot failure must not reuse a previous rejection log"
    assert not (proof / "negative-control.json").exists()

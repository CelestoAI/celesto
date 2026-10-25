#!/usr/bin/env python3
"""Build and serve an unreleased Ubuntu candidate for the ordinary Linux E2E job."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Literal

from celesto.images import published

REPO = Path(__file__).resolve().parents[2]
ARTIFACT = "ubuntu-amd64-rootfs.ext4.zst"
Backend = Literal["qemu", "firecracker"]


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run(*command: str | Path) -> None:
    subprocess.run(command, cwd=REPO, check=True)


def prepare(backend: Backend, directory: Path) -> None:
    artifacts = directory / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=False)
    base_entry = published.lookup("ubuntu", "amd64", backend)
    # This uses the selected release catalog's SHA pins and keeps the verified
    # base separate from both the build output and the normal E2E image cache.
    base = published.ensure_published_image(
        "ubuntu", "amd64", backend, cache_dir=directory / "base-cache"
    )
    run(
        "cargo",
        "build",
        "--locked",
        "--release",
        "--target",
        "x86_64-unknown-linux-musl",
        "-p",
        "celesto-guest-agent",
    )
    agent = REPO / "target/x86_64-unknown-linux-musl/release/celesto-guest-agent"
    init = REPO / "scripts/ci/preset-init.sh"
    build = directory / "build"
    # The release build script copies the verified base before mounting it.
    run(
        "sudo",
        "env",
        "ARCH=amd64",
        "OS=ubuntu",
        f"CELESTO_GUEST_AGENT_BINARY={agent}",
        "bash",
        REPO / "scripts/ci/build-preset.sh",
        "ubuntu",
        base.rootfs_path,
        build,
    )
    rootfs = build / "ubuntu-amd64-rootfs.ext4"
    run("sudo", "chown", f"{os.getuid()}:{os.getgid()}", rootfs)
    # Verify bytes from the finished image, after the builder has unmounted it.
    with tempfile.TemporaryDirectory(prefix="celesto-e2e-verify-") as mount:
        run("sudo", "mount", "-o", "loop,ro,noload", rootfs, mount)
        try:
            run("sudo", "cmp", init, Path(mount) / "init")
            run("sudo", "cmp", agent, Path(mount) / "usr/local/bin/celesto-guest-agent")
            run("sudo", "test", "-x", Path(mount) / "init")
            run("sudo", "test", "-x", Path(mount) / "usr/local/bin/celesto-guest-agent")
        finally:
            run("sudo", "umount", mount)
    candidate = artifacts / ARTIFACT
    run("zstd", "-3", "-T0", "-o", candidate, rootfs)
    candidate_sha = digest(candidate)
    (artifacts / "SHA256SUMS").write_text(f"{candidate_sha}  {ARTIFACT}\n")
    provenance = {
        "kind": "unreleased-ci-candidate",
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
        ).strip(),
        "backend": backend,
        "base_image": base_entry.model_dump(),
        "init_sha256": digest(init),
        "guest_agent_sha256": digest(agent),
        "candidate_rootfs_sha256": candidate_sha,
        "candidate_bytes": candidate.stat().st_size,
    }
    (artifacts / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps(provenance, indent=2), flush=True)


def serve(backend: Backend, directory: Path) -> None:
    artifacts = directory / "artifacts"
    provenance = json.loads((artifacts / "provenance.json").read_text())
    if provenance["kind"] != "unreleased-ci-candidate" or provenance["backend"] != backend:
        raise ValueError("Candidate provenance does not match this E2E job")
    candidate_sha = digest(artifacts / ARTIFACT)
    if candidate_sha != provenance["candidate_rootfs_sha256"]:
        raise ValueError("Candidate artifact no longer matches its recorded SHA-256")
    base = published.PublishedImage.model_validate(provenance["base_image"])
    if (base.preset, base.arch, base.vmm, base.os) != ("ubuntu", "amd64", backend, "ubuntu"):
        raise ValueError("Candidate base does not match this E2E job")
    handler = partial(SimpleHTTPRequestHandler, directory=str(artifacts))
    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        url = f"http://127.0.0.1:{server.server_port}/{ARTIFACT}"
        candidate = base.model_copy(update={"rootfs_url": url, "rootfs_sha256": candidate_sha})
        # Only this disposable CI checkout changes. A fresh pytest/CLI process
        # still downloads, checks, decompresses and caches through production code.
        catalog = REPO / "src/celesto/images/published.py"
        key = ("ubuntu", "amd64", backend, "ubuntu")
        with catalog.open("a") as stream:
            stream.write(
                "\n# Unreleased current-source E2E candidate; CI checkout only.\n"
                f"MANIFEST[{key!r}] = PublishedImage(**{candidate.model_dump()!r})\n"
            )
        (directory / "ready").write_text(url + "\n")
        print(f"Serving unreleased E2E candidate: {url}", flush=True)
        server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "serve"))
    parser.add_argument("backend", choices=("qemu", "firecracker"))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    backend: Backend = "qemu" if args.backend == "qemu" else "firecracker"
    directory = args.directory.resolve()
    if args.action == "prepare":
        prepare(backend, directory)
    else:
        serve(backend, directory)


if __name__ == "__main__":
    main()

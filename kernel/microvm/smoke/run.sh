#!/usr/bin/env bash
# Boot both workload profiles twice, exercising real filesystems and Docker.
# Usage: run.sh <amd64|arm64> <kernel-artifact-dir> <exported-guest-root> <proof-dir>
# Requires QEMU, mkfs.ext4 and mkfs.xfs on a Linux build host.
set -euo pipefail
mkdir -p "$4"
proof="$(realpath "$4")"
rm -f "$proof/receipt.json"
version="$(tr -d '[:space:]' < "$(dirname "$0")/../linux.version")"
case "$version" in *.*.*) ;; *) version="$version.0" ;; esac
arch="$1"; kernels="$(realpath "$2")"; guest="$(realpath "$3")"
case "$arch" in
    amd64) qemu=qemu-system-x86_64; machine=q35; console=ttyS0 ;;
    arm64) qemu=qemu-system-aarch64; machine=virt; console=ttyAMA0 ;;
    *) echo "Unsupported architecture: $arch" >&2; exit 2 ;;
esac
for profile in sandbox github-ci; do
    asset="vmlinux-$arch.image"
    if [ "$profile" = github-ci ]; then asset="vmlinux-github-ci-$arch.image"; fi
    truncate -s 2G "$proof/$profile-rootfs.ext4"
    mkfs.ext4 -F -d "$guest" "$proof/$profile-rootfs.ext4" > "$proof/$profile.rootfs-format.log" 2>&1
    truncate -s 1G "$proof/$profile.ext4"
    mkfs.ext4 -F "$proof/$profile.ext4" > "$proof/$profile.ext4-format.log" 2>&1
    truncate -s 512M "$proof/$profile.xfs"
    mkfs.xfs -f -m reflink=1 "$proof/$profile.xfs" > "$proof/$profile.xfs-format.log" 2>&1
    for phase in write read; do
        timeout 360 "$qemu" -machine "$machine,accel=tcg" -cpu max -m 3072 -smp 2 \
            -nographic -no-reboot -kernel "$kernels/$asset" \
            -append "console=$console panic=1 root=/dev/vda rw init=/init celesto_profile=$profile celesto_phase=$phase celesto_expected_kernel=$version" \
            -drive "file=$proof/$profile-rootfs.ext4,format=raw,if=virtio" \
            -drive "file=$proof/$profile.ext4,format=raw,if=virtio" \
            -drive "file=$proof/$profile.xfs,format=raw,if=virtio" \
            -netdev user,id=net0 -device virtio-net-pci,netdev=net0 \
            2>&1 | tee "$proof/$profile-$phase.console.log"
        grep -q "^KERNEL_SMOKE_PASS profile=$profile phase=$phase kernel=$version" "$proof/$profile-$phase.console.log"
        if grep -q KERNEL_SMOKE_FAIL "$proof/$profile-$phase.console.log"; then
            echo "Guest reported a kernel smoke failure" >&2
            exit 1
        fi
    done
done
python3 - "$arch" "$kernels" "$proof" "$version" <<'PY'
import hashlib, json, sys
from pathlib import Path
arch, kernels, proof = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
receipt = {"architecture": arch, "kernel_version": sys.argv[4], "profiles": {}}
for profile in ("sandbox", "github-ci"):
    asset = kernels / f"vmlinux-{'github-ci-' if profile == 'github-ci' else ''}{arch}.image"
    receipt["profiles"][profile] = {
        "sha256": hashlib.sha256(asset.read_bytes()).hexdigest(), "bytes": asset.stat().st_size,
        "checks": ["namespaces", "ext4-restart", "docker-overlay-storage", "docker-cgroups", "docker-bridge-dns"]
                  + (["xfs-mount-reflink"] if profile == "github-ci" else ["xfs-absent"]),
        "console_logs": [f"{profile}-{phase}.console.log" for phase in ("write", "read")],
    }
(proof / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
PY

#!/usr/bin/env bash
# Negative qualification control: the CI kernel must fail sandbox admission.
# Takes the same four arguments as run.sh. Uses its own disposable proof tree.
set -euo pipefail
mkdir -p "$4"
proof="$(realpath "$4")"
rm -f "$proof/negative-control.json"
arch="$1"; kernels="$(realpath "$2")"; guest="$(realpath "$3")"
mkdir -p "$proof/replaced-kernels" "$proof/run"
cp "$kernels/vmlinux-github-ci-$arch.image" "$proof/replaced-kernels/vmlinux-$arch.image"
cp "$kernels/vmlinux-github-ci-$arch.image" "$proof/replaced-kernels/vmlinux-github-ci-$arch.image"
# A previous success must not survive qualification of the wrong candidate.
printf '{"stale":true}\n' > "$proof/run/receipt.json"
if bash "$(dirname "$0")/run.sh" "$arch" "$proof/replaced-kernels" "$guest" "$proof/run"; then
    echo "Negative control failed: an XFS-enabled kernel passed sandbox qualification" >&2
    exit 1
fi
grep -q 'Sandbox kernel unexpectedly supports XFS' "$proof/run/sandbox-write.console.log"
test ! -e "$proof/run/receipt.json"
printf '{"architecture":"%s","wrong_profile_rejected":true,"stale_receipt_removed":true}\n' "$arch" > "$proof/negative-control.json"

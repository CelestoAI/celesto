# Prepare the Android CI kernel

Build a separate Linux runner kernel that can host an accelerated Android
emulator. This SDK change reuses ordinary CI configuration and does not require
the separate QEMU confinement or bounded-console features. Building or merging
the kernel support does not enable production Android jobs.

## What the kernel inherits

The build merges the same pinned Linux source and configuration in this order:

```text
Linux defaults → common → architecture → github-ci → github-ci-android
```

The ordinary CI profile supplies XFS and transparent huge page (THP) support.
Android adds built-in Intel and AMD KVM and changes THP's default from `always` to
`madvise`, allowing programs to request larger pages selectively. The child
explicitly disables the inherited `always` choice. The build verifies the final
value of each setting using this same order.

The Android-only Linux 7.3 source patch enables read-only executable kernel
allocations with strict kernel permissions even though loadable modules are
disabled. Strict memory permissions and CPU mitigations remain enabled. Review
the patch when upgrading Linux. This kernel-local repair has no dependency on
the separate host-confinement helper.

The profile targets x86_64 with both vendor drivers built in. The existing Linux
QEMU launch uses `-cpu host`, so no SDK runtime change is needed to expose the
matching host's CPU features. Acceleration still requires nested virtualization
on that host. Building AMD support does not qualify AMD hardware; other Android
system images and smaller-machine recommendations also need their own validation.

## Check the SDK independently

Follow [contributor setup](../../CONTRIBUTING.md#development-setup), then run:

```bash
uv run pytest tests/runtime/test_kernel_config.py \
  tests/integration/test_kernel_profile_inheritance.py \
  tests/integration/test_kernel_release_workflow.py \
  tests/images/test_published_images.py
uv run ruff check .
uv run ruff format --check .
```

The shell integration fixture checks profile composition, not real Linux or
hardware behavior. Existing ordinary runtime, SSH, networking and lifecycle
checks must also pass. Verify an installed wheel without the extracted console,
launch or TAP modules, and retain the shared AppArmor option already used by the
backend. No new privileged helper or security capability is needed for ordinary
SDK use.

## Build an isolated candidate

On Linux, with the documented kernel build tools installed:

```bash
set -euo pipefail
output_dir=$(mktemp -d /tmp/celesto-android-kernel.XXXXXXXX)
CELESTO_KERNEL_PROFILE=github-ci-android CELESTO_ARCH_OVERRIDE=amd64 \
  OUT_DIR="$output_dir" bash kernel/microvm/build.sh
sha256sum "$output_dir"/vmlinux-github-ci-android-amd64.{elf,image,config}
```

Preserve the exact SDK commit, Linux source checksum, configuration, source patch,
artifact hashes and build log. The build emits ELF, boot-image and resolved
configuration files. Review the resolved configuration and test the exact
artifact for nested acceleration, actual memory mappings and kernel memory
permissions. A configuration check or successful compilation is not that proof.

Qualify the exact new artifact separately on Intel and AMD hardware. On AMD,
record the host's `kvm_amd` nested setting, the runner VM's `AuthenticAMD` vendor
and `svm` CPU flag, usable `/dev/kvm`, nested vCPU execution, emulator acceleration
and fresh-AVD instrumentation. Repeat the existing Intel checks with the same
artifact to catch regressions. Intel boot evidence does not validate AMD's KVM
driver. Keep production admission closed until the required evidence is reviewed.

Existing explicit kernel-path support permits isolated candidate testing before
publication. Real hardware testing and infrastructure changes require separate
authorization. Do not replace the ordinary CI kernel to try an Android candidate.

## Publication and release boundaries

`ANDROID_CI_KERNELS` in the [kernel catalog](../../src/celesto/images/published.py)
stays empty until verified release receipts provide real URLs and SHA-256 hashes.
Selecting an unpublished Android kernel fails clearly; ordinary SDK profiles keep
their existing kernel entries and never become an Android fallback.

The [kernel workflow](../../.github/workflows/build-microvm-kernel.yml) builds
Android candidates but skips their release upload on push or an implicit dispatch.
An Android upload requires an explicit dispatch with a reviewed draft release tag.
The dispatch covers the complete kernel matrix, including ordinary profiles; use
a new draft and verify every resulting asset. Do not overwrite published assets
or use a global kernel-tag override to populate the Android catalog.

After authorized artifact review, pin Android entries only, publish the reviewed
SDK package through the normal release process, and update backend dependency
pins together. A merged SDK branch, draft kernel upload and installed backend
release are separate milestones. The backend's current signed runtime bundle
must consume the matching SDK version; do not manually replace its environment.

For image preparation and the remaining hardware, runtime-download and qualification
work, see [backend PR #1310](https://github.com/CelestoAI/backend/pull/1310).
Production admission remains closed during this separation. The pre-existing SDK
asynchronous-start cancellation finding is separate and is not repaired by moving
the security feature out of this PR.

# How to prepare and release the Android CI kernel

Use this guide to build an Android runner kernel, preserve its evidence, and hand
it to the backend release process. Building a kernel does not enable Android
jobs. The SDK catalog and the backend's host checks keep admission closed until
the exact installed combination has passed qualification.

This is a maintainer runbook. For the Android tools, runner image, host packages
and placement steps, continue with the backend's
[`docs/operations/android-ci-setup.md` runbook in PR #1310](https://github.com/CelestoAI/backend/blob/722e33d650a1ae15bedc44ec950e4312128c866e/docs/operations/android-ci-setup.md).
The related source changes are [SDK PR #725](https://github.com/CelestoAI/celesto/pull/725)
and [backend PR #1310](https://github.com/CelestoAI/backend/pull/1310).

## Current release gates

- `ANDROID_CI_KERNELS` in [the SDK catalog](../../src/celesto/images/published.py)
  remains empty until real artifact receipts supply reviewed URLs and hashes.
  Android cannot fall back to an ordinary kernel.
- Candidate hardware testing, draft uploads, public release publication, host
  installation, isolation activation and restoring placement are separate
  authorized operations. The commands below do not grant that authorization.
- The initial backend policy accepts AWS Intel x86_64 `m6i.metal` and
  `m6id.metal`. An M7i, AMD or Mac workload result does not qualify that policy.
- **Open release blocker:** cancelling asynchronous startup of a computer without
  public egress can abandon the startup thread. QEMU may start after the operation
  guard is released while saved inventory still has no PID. This also reproduces
  on the preexisting main code; the current console fixes do not repair it.
  Resolve and verify [the cancellation finding](https://github.com/CelestoAI/celesto/pull/725#discussion_r4605282149)
  before production release. See `_async_start_claimed` in
  [the runtime manager](../../src/celesto/vm.py).

## Terms used in the checks

| Term | Meaning and evidence needed |
| --- | --- |
| Guest kernel | Linux running inside the Celesto runner VM. This process does not replace the outer AWS machine's kernel. |
| KVM / nested acceleration | Linux's hardware virtualization interface. The Android emulator uses it inside the runner VM, so both virtualization layers must work. An installed `/dev/kvm` file alone is insufficient. |
| THP / `madvise` | Transparent huge pages let Linux use larger memory pages. The `madvise` setting lets a program request them. Record actual emulator memory mappings and KVM page sizes; a configuration setting alone is insufficient. |
| W+X | Memory that is writable and executable at the same time. Boot qualification must show that the kernel's W+X check passes. |
| RWX / ROX | Read, write and execute permission rules. Strict RWX keeps writable memory separate from executable memory; ROX means read-only and executable. The Android execmem patch retains that separation for built-in executable allocations. |
| Qualification | Recorded checks against exact artifact hashes and installed identities. Preliminary candidate results and final installed-host qualification are different evidence. |

## Check the SDK source before hardware work

Follow [contributor setup](../../CONTRIBUTING.md#development-setup): install `uv`
and the Rust toolchain used to build the local `celesto-core` extension. The
[default test workflow](../../.github/workflows/pytest.yml) uses Python 3.13/3.14
on Linux and 3.14 on macOS. From the repository root, a Linux Python 3.13 check is:

```bash
set -euo pipefail
uv sync --extra dev --extra dashboard --extra server --python 3.13
uv run pytest --ignore=tests/test_generated_cloud_client.py
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

The generated cloud-client contracts have their own
[path-filtered workflow](../../.github/workflows/cloud-openapi.yml); the ignore
matches ordinary CI rather than declaring that coverage unnecessary. The
dashboard and server extras are required by the default test suite. Type checks
follow [contributor quality checks](../../CONTRIBUTING.md#quality-checks), and
the format check matches [lint CI](../../.github/workflows/lint.yml).

Run subprocess, local-socket and saved-inventory tests with normal local process
and filesystem permissions. A restricted execution environment can prevent
those operations before the behavior is exercised; record that as unavailable
coverage rather than weakening a guard. These checks do not install KVM, load
host policy or prove real Android acceleration. Any runtime setup or hardware
campaign remains a separate operation.

## 1. Build a local candidate from reviewed source

Use a clean checkout at the full SHA reviewed **after all code fixes**. Record
that SHA rather than copying a historical PR head from an earlier handoff. On
Linux, install the compiler and dependencies listed in the
[kernel build guide](../../kernel/microvm/README.md#building-locally), including
Python 3. Use new task-owned build and output directories.

Set `REVIEWED_SHA` to that approved full commit. From the repository root:

```bash
set -euo pipefail
: "${REVIEWED_SHA:?Set the approved full source SHA}"
test -z "$(git status --porcelain)"
test "$(git rev-parse HEAD)" = "$REVIEWED_SHA"
git rev-parse HEAD
build_dir=$(mktemp -d)
output_dir=$(mktemp -d)
CELESTO_KERNEL_PROFILE=github-ci-android CELESTO_ARCH_OVERRIDE=amd64 \
  WORK_DIR="$build_dir" OUT_DIR="$output_dir" \
  bash kernel/microvm/build.sh
sha256sum "$output_dir"/vmlinux-github-ci-android-amd64.{image,elf,config}
```

The outputs are `.image` for QEMU, `.elf` for Firecracker, and the resolved
`.config`. `JOBS` can limit compiler parallelism. Do not use
`CELESTO_VERIFY_ONLY=1` when requesting binaries: it exits after configuration
verification. The Android patch currently requires the pinned Linux 7.3 source;
a Linux update requires a separate patch/configuration review.

Record the source SHA, pinned Linux tarball hash, build-script/fragment/patch
hashes, compiler versions, resolved config and all artifact hashes. Keep failed
attempts as well as successful ones.

## 2. Prepare a reviewed draft build when uploads are authorized

The [kernel workflow](../../.github/workflows/build-microvm-kernel.yml) accepts
`release_tag` and `force_overwrite`. Choose a new empty draft tag and leave
`force_overwrite=false`. Do not reuse a published tag or overwrite existing
assets to make a check pass.

Set these values deliberately:

- `REVIEWED_SHA`: the full approved post-fix source commit.
- `REVIEWED_REF`: a new immutable tag such as `android-ci-reviewed-<identifier>`
  pointing to that commit. Avoid package-release prefixes such as `v...`.
- `KERNEL_TAG`: a new unused kernel release tag.
- `RELEASE_NOTES`: the path to reviewed notes describing scope and evidence.

After checking that both names are unused, create the source ref and draft with
an explicit target, then dispatch:

```bash
set -euo pipefail
: "${REVIEWED_SHA:?Set the approved full source SHA}"
: "${REVIEWED_REF:?Set an unused reviewed source tag}"
: "${KERNEL_TAG:?Set an unused kernel release tag}"
: "${RELEASE_NOTES:?Set the reviewed release notes path}"
git tag "$REVIEWED_REF" "$REVIEWED_SHA"
git push origin "refs/tags/$REVIEWED_REF"
gh release create "$KERNEL_TAG" --repo CelestoAI/celesto --draft \
  --target "$REVIEWED_SHA" --title "$KERNEL_TAG" --notes-file "$RELEASE_NOTES"
gh workflow run build-microvm-kernel.yml --repo CelestoAI/celesto \
  --ref "$REVIEWED_REF" -f release_tag="$KERNEL_TAG" -f force_overwrite=false
```

`--ref` names the branch or tag containing the workflow version to run. The
workflow's automatic missing-draft creation omits `--target`, which otherwise
defaults to the default branch. Pre-creating the draft as above binds its target
to the reviewed SHA. Check both the run's `headSha` and the draft target; one
does not prove the other.

An explicit `release_tag` applies to **all four matrix cells**:

| Profile | Architecture | Assets |
| --- | --- | --- |
| sandbox | amd64 | `vmlinux-amd64.{elf,image,config}` |
| github-ci | amd64 | `vmlinux-github-ci-amd64.{elf,image,config}` |
| github-ci-android | amd64 | `vmlinux-github-ci-android-amd64.{elf,image,config}` |
| sandbox | arm64 | `vmlinux-arm64.{elf,image,config}` |

The draft can therefore contain **12 assets**. Publishing it publishes the
attached ordinary-profile artifacts too, although their installed SDK pins need
not change. Review that scope before publication. There is no Android-only
matrix input in this workflow.

`force_overwrite=false` skips filenames already present. A skipped filename is
not proof that the uploaded bytes came from this attempt. The workflow also
caches builds by kernel input hashes; `force_overwrite` does not force a fresh
compile. Record cache-hit status and the cache key along with the actual bytes.

## 3. Download and qualify exact candidate bytes

Set `RUN_ID` to the resulting workflow run ID and `PRIVATE_KERNEL_DIR` to a new
private evidence directory. Read the completed run and draft metadata:

```bash
set -euo pipefail
: "${RUN_ID:?Set the completed workflow run ID}"
: "${PRIVATE_KERNEL_DIR:?Set the private download directory}"
gh run view "$RUN_ID" --repo CelestoAI/celesto \
  --json headSha,event,status,conclusion,jobs,url
gh release view "$KERNEL_TAG" --repo CelestoAI/celesto \
  --json tagName,targetCommitish,isDraft,assets,url
gh release download "$KERNEL_TAG" --repo CelestoAI/celesto \
  --pattern 'vmlinux-github-ci-android-amd64.*' --dir "$PRIVATE_KERNEL_DIR"
sha256sum "$PRIVATE_KERNEL_DIR"/vmlinux-github-ci-android-amd64.{image,elf,config}
```

Use a new private download directory. Require the approved `headSha`, explicit
dispatch event, successful expected jobs, correct draft target and expected
asset inventory. Match downloaded binary hashes to the workflow SHA summary and
remote asset digests. Hash `.config` separately: the workflow uploads it but the
summary lists only the two binary hashes. Retain asset IDs, sizes, logs, metadata
and local hashes together. Authenticated draft downloads allow qualification
before publication; do not assume public release URLs work for a draft.

With the Android catalog empty, use a verified local candidate kernel. A direct
SDK boot supplies its path through `VMConfig.kernel_path`; it is not selected by
a global CLI kernel override. The backend image builder accepts
`SMOLVM_KERNEL_PATH` or `CelestoImageBuilder(kernel_path=...)` for an isolated
candidate build. Its ordinary `uv run` target still uses the backend's locked
SDK, so record the actual imported SDK and native extension, or invoke the
builder with an explicit task-only candidate interpreter. Follow the backend
runbook for the complete rootfs build and boot configuration.

These paths do not enable the normal pool launch path. It independently resolves
the Android catalog and compares the selected kernel hash with qualification
evidence. `CELESTO_KERNELS_RELEASE_TAG` only changes URLs for existing AMD64
catalog entries while retaining their checksums; it does not populate Android.

Preliminary candidate checks must include exact-kernel boot, a passing W+X
check, working nested acceleration, actual large-page mappings and fresh-AVD
application instrumentation on Large and XL. Record failures, tools, APK/JUnit
identities, setup conditions, cleanup and timing. API35/36, standard Action/direct
flows, repeated samples and host-density checks have separate declared coverage.
The backend reference campaign requires an independently reviewed application;
it is not a bundled upstream Android conformance suite. A previous 38-case sample
does not replace the expected-case inventory or full campaign.

The existing [`smoke/run.sh`](../../kernel/microvm/smoke/run.sh) exercises only
sandbox and ordinary github-ci with software CPU emulation. Its success does not
qualify the Android artifact, nested KVM, host confinement or production density.

## 4. Pin accepted Android artifacts and release a new SDK

After candidate acceptance, separately authorize publishing the unique kernel
draft. Keep existing assets immutable. Add only an `amd64` `BaseKernel` entry to
`ANDROID_CI_KERNELS`, with the accepted Android `.elf` and `.image` URLs and their
actual SHA-256 values. Use literal Android-specific URLs to the new tag.

Do not change shared `KERNELS_RELEASE_TAG`, `BASE_KERNELS`, `CI_KERNELS`, ordinary
URLs/digests or rootfs pins as part of Android-only adoption. The shared URL helper
uses the shared tag; using it with a new global tag would also move ordinary
AMD64 URLs. Review any future Android-specific URL helper separately.

Resolve the open cancellation blocker and run the relevant SDK/kernel/release
checks before releasing. Choose an unused SDK version; the existing
`0.1.15a1` must not receive changed bytes. Review the version and Android pin
update, merge the approved SDK changes, and only then create a matching
`v<version>` or `celesto-v<version>` package tag through the normal release
process. Kernel build, SDK pin/release and backend integration commits are
different identities; retain each full SHA in the handoff.

The [package publisher](../../.github/workflows/publish.yml) checks that the tag
matches `pyproject.toml`, the required native core is already available and the
pinned standalone guest-agent assets match. It then builds, publishes and checks
the PyPI installer index. The package tag also triggers the dashboard release.
Wait for those workflows and verify installed-wheel behavior; a source checkout
test does not prove the published wheel/native dependency combination.

The source PR may be merged earlier with the catalog empty if that source-only
scope is separately approved. That does not authorize a package release or
Android admission, and does not remove the cancellation release blocker.

## 5. Hand off the released SDK to backend operations

Use the backend [Android setup runbook](https://github.com/CelestoAI/backend/blob/722e33d650a1ae15bedc44ec950e4312128c866e/docs/operations/android-ci-setup.md)
for dependency pins/locks, the uniquely versioned runner image, separate parser
package distribution and the host rollout. Backend main merges can publish a
host-runtime fleet target, so coordinate dependency migration and rollout before
merging that change.

Final qualification must use the actual published SDK wheel/native extension,
backend runtime archive, installed helper/parser/QEMU and immutable kernel/rootfs
assets. Drain and verify the supported host before authorized isolation
activation. Then test exact-role filesystem/process/network denials, resource
limits, lifecycle/restart/replay, deadline/cancellation cleanup, API35/36
workloads and safe concurrent density. A new install, reboot, artifact or runtime
identity can invalidate prior evidence; do not reuse a preliminary receipt as a
fresh installed-host result.

Only a reviewed, root-owned, fresh qualification receipt matching the installed
host can open admission. The SDK release itself never restores placement.

## Handoff checklist

- Reviewed kernel source ref/SHA, SDK release SHA/version and backend integration
  SHA; current release blockers and their disposition.
- Kernel release tag/target, run URL/head SHA, matrix/job results, cache status,
  all three Android artifact hashes and resolved build configuration.
- Preliminary boot/workload receipts and their limits; final installed-stack
  qualification recorded separately.
- Published wheel/sdist/native hashes and verified installer-index availability.
- Backend image/runtime/helper/parser versions and hashes, supported host
  identity, freshness policy, rollback owner and explicit admission decision.

## Troubleshooting

| Observation | Action |
| --- | --- |
| No Android kernel is registered | Keep admission closed; use a verified local path for an authorized candidate test or finish the reviewed Android pin update. |
| Android upload was skipped | Check that the event was an explicit dispatch with a nonempty new draft `release_tag`; do not bypass the publication guard. |
| An asset was skipped or a cache was reused | Preserve the attempt, compare actual downloaded hashes and source inputs, and choose a fresh draft for different bytes. |
| A kernel checksum fails | Stop that attempt and reconcile the artifact with its build receipt; do not change expected hashes to fit unknown bytes. |
| A build passes but KVM/THP/W+X evidence is missing | Treat runtime qualification as incomplete and run the separately authorized exact-artifact checks. |
| A source test passes but installed launch refuses | Compare the actual wheel/native/helper/parser/runtime identities and backend pins; do not remove a guard to force launch. |

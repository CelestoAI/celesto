# Celesto microvm Kernel

Celesto builds separate guest kernels for ordinary sandboxes and GitHub CI.
Both use the same pinned Linux source, common configuration, and architecture
configuration. GitHub CI adds an XFS overlay for filesystem-intensive workloads. Builds need
Python 3 in addition to the compiler and kernel build dependencies; arm64 uses
it to generate DRM register headers.

```text
linux.version + linux.sha256
  config.fragment + config.<arch>.fragment
    profiles/sandbox.fragment       -> vmlinux-<arch>.{elf,image,config}
    profiles/github-ci.fragment     -> vmlinux-github-ci-<arch>.{elf,image,config}
```

The sandbox profile keeps XFS disabled. The CI overlay enables it as a built-in
driver; neither profile requires kernel modules or an initrd in production.
Each build produces an ELF for Firecracker and an Image/bzImage for QEMU.

Build a specific profile and architecture on Linux:

```sh
CELESTO_KERNEL_PROFILE=github-ci CELESTO_ARCH_OVERRIDE=amd64 \
  OUT_DIR=/tmp/kernel-out bash kernel/microvm/build.sh
```

Cross builds also set `CROSS_COMPILE` to the matching toolchain prefix.
`JOBS` limits compile parallelism. Work directories include both profile and
architecture so one build cannot reuse another profile's configuration.
Fragment validation checks the final requested value after child overrides,
then rejects any value that Kconfig changes while resolving dependencies.

Kernel releases use `KERNELS_RELEASE_TAG`, independently of rootfs releases at
`IMAGES_RELEASE_TAG`. Candidate AMD64 kernel URLs can be selected with
`CELESTO_KERNELS_RELEASE_TAG` before importing the SDK. ARM sandbox kernels
retain their existing `ARM_KERNELS_RELEASE_TAG`. Pin the actual SHA-256
for every profile, architecture, and format after building and qualification;
changing a release tag does not waive checksum verification.

Runtime caches include the complete kernel digest in the filename. Existing
saved VM configurations keep their original kernel path across an upgrade.
Callers choose a workload profile when resolving the guest kernel.

## Boot qualification

The smoke recipe in `smoke/` builds an Ubuntu guest with Docker and filesystem
tools. Export one guest filesystem per architecture, then run on a Linux host
with QEMU, e2fsprogs, xfsprogs, and Python 3 installed:

```sh
docker build --platform linux/amd64 -f kernel/microvm/smoke/Guest.Dockerfile \
  -t celesto-kernel-smoke:amd64 kernel/microvm/smoke
container=$(docker create celesto-kernel-smoke:amd64)
mkdir -p /tmp/kernel-guest
docker export "$container" | tar -C /tmp/kernel-guest -xf -
docker rm "$container"
bash kernel/microvm/smoke/run.sh amd64 /tmp/kernel-out /tmp/kernel-guest /tmp/kernel-proof
```

The AMD64 release runner boots each profile from an ext4 root filesystem
in QEMU twice, checks ext4 persistence, namespaces, Docker overlay storage,
container memory/CPU limits, bridge DNS/HTTP, and CI XFS mounting with reflinks.
`receipt.json` records the tested kernel digests, sizes, checks, and console log
paths. A failed rerun removes any previous success receipt. Run the negative
control with a separate output directory to prove an XFS-enabled CI kernel is
rejected when presented as the sandbox kernel:

```sh
bash kernel/microvm/smoke/reject-ci-as-sandbox.sh \
  amd64 /tmp/kernel-out /tmp/kernel-guest /tmp/kernel-negative-proof
```

The negative-control receipt requires both rejection for the expected reason
and removal of a deliberately planted stale success receipt. Applications should also qualify guest-agent integration and networking in
their own environments before adopting a new kernel.

## Why this exists

Before 0.0.14a0 Celesto fetched kernels from two external CDNs:

- **Firecracker's CI S3 bucket** (`s3.amazonaws.com/spec.ccfc.min/.../vmlinux-5.10.198`) — for Firecracker on Linux. Pinned to Linux 5.10.
- **Ubuntu cloud-images** (`cloud-images.ubuntu.com/.../vmlinuz-generic`) — paired with a matching initrd for the QEMU+Ubuntu auto-config path.

Two kernels meant two CVE-watch lists, two test surfaces, and two CDN
failure modes (we hit a `cloud-images.ubuntu.com` outage in practice).
Both upstream kernels are also generic-purpose with hundreds of drivers
we don't need (Bluetooth, USB, sound, gpio, …) — extra attack surface
for a sandbox that just needs virtio + ext4 + sshd.

The kernel built here closes that gap: a single in-house source build,
microvm-tuned, on the upstream release pinned in `linux.version`.

## Runtime ↔ format compatibility

What each runtime accepts as `-kernel` / `--kernel-image-path`:

| Runtime           | ELF (`.elf`) | Image / bzImage (`.image`) | Why we ship which |
|---                |---           |---                          |---|
| **Firecracker**   | ✅ required  | ❌ rejects with `Invalid Elf magic number` | Firecracker only loads ELF. |
| **QEMU on x86 q35** | ✅ accepts | ✅ accepts                  | We ship `.image` (bzImage) for parity with the aarch64 path. |
| **QEMU on aarch64 virt** | ❌ silent hang at boot | ✅ required | Empirically QEMU's aarch64 ELF loader fails to bring up the kernel; only the Linux ARM64 boot-protocol Image works. |
| **libkrun**       | ✅ required (Firecracker-API-compatible) | ❌ same as Firecracker | Same loader as Firecracker. |

Bottom line: ship both formats per arch. The runtime-side mapping lives
in [`_kernel_format_for_vmm`](../../src/celesto/images/published.py).

## What features each runtime actually exercises

Driver / Kconfig matrix — what's *required* (not just nice-to-have) for
the runtimes Celesto uses today:

| Feature group          | Kconfig (relevant)              | Firecracker | QEMU virt aarch64 | QEMU q35 amd64 | libkrun |
|---                     |---                              |---          |---                |---             |---|
| **Virtio transport**   | `CONFIG_VIRTIO_MMIO`            | required    | not used          | not used       | required |
|                        | `CONFIG_VIRTIO_MMIO_CMDLINE_DEVICES` | required (devices passed via cmdline) | – | – | required |
|                        | `CONFIG_VIRTIO_PCI`             | not used    | required          | required       | not used |
|                        | `CONFIG_VIRTIO_PCI_LEGACY`      | not used    | nice-to-have      | nice-to-have   | required (libkrun uses legacy) |
| **Console**            | `CONFIG_SERIAL_8250` + `_CONSOLE` | required (ttyS0 on both archs) | – | required (ttyS0) | required |
|                        | `CONFIG_SERIAL_AMBA_PL011` + `_CONSOLE` | – | required (ttyAMA0) | – | – |
| **PCI host bridge**    | `CONFIG_PCI`                    | – (off via `pci=off`) | required | required | – |
|                        | `CONFIG_PCI_HOST_GENERIC`       | – | required (arm64 virt) | – (x86 has built-in PCI host) | – |
|                        | `CONFIG_PCI_MSI`                | – | required (virtio-PCI uses MSI-X) | required | – |
| **Block devices**      | `CONFIG_VIRTIO_BLK`             | required    | required          | required       | required |
| **Network**            | `CONFIG_VIRTIO_NET`             | required    | required          | required       | required |
| **Vsock (host↔guest)** | `CONFIG_VSOCKETS`, `CONFIG_VIRTIO_VSOCKETS` | – | – | – | required (libkrun init protocol) |
| **Filesystems** (no-initrd boot of guest rootfs) | `CONFIG_EXT4_FS` | required (rootfs) | required | required | required |
|                        | `CONFIG_ISO9660_FS`             | – | required (cloud-init NoCloud seed disk on `/dev/vdb`) | required | – |
|                        | `CONFIG_FUSE_FS`                | required (guest FUSE filesystems such as JuiceFS) | required | required | required |
| **Workspace mounts**   | `CONFIG_NET_9P`, `CONFIG_NET_9P_VIRTIO`, `CONFIG_9P_FS` | – | required (`celesto <preset> start --mount …`) | required | – |
|                        | `CONFIG_OVERLAY_FS`             | – | required (read-only mount = 9p+overlay) | required | – |
| **No modules**         | `# CONFIG_MODULES is not set`   | required (no initrd to load modules from) | required | required | required |

"required" / "not used" describe what the runtime actually *needs* — we
enable everything in the union so one build covers all four columns.
That's what the fragments in this directory encode.

## What's NOT enabled (and why)

- `CONFIG_RANDOM_TRUST_CPU`, `CONFIG_RANDOM_TRUST_BOOTLOADER` — removed
  as Kconfig symbols in the Linux 6.x random.c rewrite. They're now
  cmdline params (`random.trust_cpu=on`, default ON) — we get the
  fast-sshd-hostkey-gen behavior for free.
- `CONFIG_VIRTIO_FS` (virtiofs) — Celesto's workspace mounts use
  virtio-9p instead. Adding virtiofs is a future enhancement; not
  load-bearing today.
- KVM / Hypervisor.framework paravirt symbols (`CONFIG_KVM_GUEST`,
  `CONFIG_PARAVIRT`) — `KVM_GUEST` is x86-only (arm64 doesn't have the
  symbol); the perf wins are minor and the upstream defconfig already
  enables what's needed.
- Kernel modules — see "no modules" row above. The kernel ships without
  `/lib/modules/$(uname -r)`, so userspace `modprobe` will fail with
  "module not found" even for built-in drivers. The Celesto facade's
  workspace-mount probe treats `/proc/filesystems` as the source of
  truth for what's registered (see the fast-path in
  `_ensure_9p_workspace_support`).

## What's pinned

| File | Role |
|---|---|
| `linux.version` | Single line: the upstream Linux release we build (e.g. `6.12.10`). Updated after checking upstream stable releases and advisories. |
| `linux.sha256` | One `sha256sum -c` line for the tarball at `cdn.kernel.org`. |
| `config.fragment` | Common deltas vs `x86_64_defconfig` (x86) / `defconfig` (arm64) — symbols that exist on both archs. Every line carries an inline `# why:` comment — that's the source of truth for "why is this in our kernel." |
| `config.amd64.fragment` | x86-only deltas (8250 console). Merged on top of `config.fragment` for amd64 builds. |
| `config.arm64.fragment` | arm64-only deltas (PCI host-generic, PL011 console). Merged on top of `config.fragment` for arm64 builds. |
| `build.sh` | The exact recipe CI runs. Also runnable locally — see below. |

This release qualifies new AMD64 kernels. Existing ARM sandbox
kernel pins remain unchanged; the GitHub CI profile is available on AMD64.

## Building locally

```sh
cd kernel/microvm
bash build.sh
# Produces vmlinux-<host_arch>.elf and vmlinux-<host_arch>.image
# (and vmlinux-<host_arch>.config) in the current directory.
```

The build needs GNU Make 4.0 or newer. macOS ships an older `make`,
so install the Homebrew version with `brew install make` and run:

```sh
MAKE=gmake bash build.sh
```

Cross-builds work too if you have the toolchain:

```sh
CELESTO_ARCH_OVERRIDE=arm64 ARCH=arm64 \
    CROSS_COMPILE=aarch64-linux-gnu- \
    bash build.sh
```

### Validating in Docker

`make defconfig` itself needs GNU `ld`, which macOS doesn't ship. Easiest
path on a Mac is to run the build in an Ubuntu container — same toolchain
CI uses. On Apple Silicon, **always pass `--platform`** (Docker silently
selects amd64 otherwise, then emulates, and the kernel build dies on
mismatched gcc flags):

```sh
# Quick: stop after fragment verification (~30 s, no kernel compile).
docker run --rm --platform=linux/arm64 \
    -v "$PWD":/src:ro -e CELESTO_VERIFY_ONLY=1 \
    -e CELESTO_ARCH_OVERRIDE=arm64 ubuntu:24.04 \
    bash -c 'apt-get update -qq && \
        apt-get install -y --no-install-recommends \
        build-essential bc bison flex libssl-dev libelf-dev \
        xz-utils curl ca-certificates kmod cpio python3 >/dev/null && \
        cp -r /src/kernel /tmp/kernel && \
        cd /tmp/kernel/microvm && bash build.sh'

# Full: produces a real vmlinux in /tmp/out (~5–8 min on M-series).
mkdir -p /tmp/out && docker run --rm --platform=linux/arm64 \
    -v "$PWD":/src:ro -v /tmp/out:/out -e OUT_DIR=/out \
    -e CELESTO_ARCH_OVERRIDE=arm64 ubuntu:24.04 \
    bash -c '<same setup as above, drop CELESTO_VERIFY_ONLY>'
```

Swap `--platform=linux/amd64` + `CELESTO_ARCH_OVERRIDE=amd64` for the x86 build.

## Smoke-testing locally

The example below is for **macOS Apple Silicon**, which uses the
Hypervisor.framework accelerator (`hvf`). On **Linux** with KVM,
swap `accel=hvf` for `accel=kvm` and drop `-cpu host` (or keep it —
KVM accepts it too). On Linux without KVM, use `accel=tcg` and expect
slow boot.

```sh
qemu-system-aarch64 -machine virt,accel=hvf -cpu host -smp 2 -m 1024 \
    -kernel vmlinux-arm64.image \
    -drive file=/path/to/rootfs.ext4,format=raw,if=none,id=root \
    -device virtio-blk-pci,drive=root \
    -netdev user,id=net0 -device virtio-net-pci,netdev=net0 \
    -append "console=ttyAMA0 reboot=k panic=1 init=/init root=/dev/vda rw" \
    -nographic -no-reboot
```

Expected: kernel boot messages, `/init` log lines, sshd listening on
`10.0.2.15:22`. If you see `<<< pl011 console >>>` text but the boot stalls,
check the rootfs has a valid `/init`. If you see nothing at all, check
`config.fragment` against the actual `.config` (also written to
`vmlinux-<arch>.config` next to the artifact).

## Updating Linux

1. Check [kernel.org](https://kernel.org/releases.json) for the current stable
   `latest_stable.version` value (rather than the maintained `stable` series entry)
   and review advisories against the configured features.

1. Download its tarball and detached `.tar.sign` from the matching `v<major>.x`
   directory. Verify the uncompressed tar signature against a maintainer
   fingerprint published in [kernel.org's instructions](https://www.kernel.org/signature.html):

   ```sh
   xz -cd linux-<version>.tar.xz | gpg --verify linux-<version>.tar.sign -
   sha256sum linux-<version>.tar.xz
   ```

1. Update `linux.version` and `linux.sha256`, then build both profiles on AMD64. Resolve every fragment validation failure against upstream
   Kconfig; preserve existing Docker and networking capabilities.

1. Run the boot qualification above. Save the source signature result,
   compiler versions, effective configurations, artifact sizes and hashes,
   and boot receipts.

1. Publish the qualified artifacts under a new immutable kernel release tag.
   Update `KERNELS_RELEASE_TAG`, `BASE_KERNELS`, and `CI_KERNELS` from those
   exact artifacts. Keep rootfs pins separate.

1. Qualify SDK integration and networking in each supported runtime environment.
   Existing saved VMs retain their older kernels; upgrading the default does
   not patch a running guest. Recreating those guests needs a separate
   lifecycle plan that preserves their data.

## Naming convention (asymmetric, by design)

Sandbox artifacts are named `vmlinux-<arch>.elf` (Firecracker / libkrun) and
`vmlinux-<arch>.image` (QEMU) — both preset-independent. CI inserts `github-ci-` before the architecture. The existing
**Firecracker** artifacts produced by the old per-preset build are named
`<preset>-<arch>-vmlinux.bin` — per-preset, even though the kernel itself
doesn't depend on the preset. That asymmetry is intentional for now: the
kernel really is preset-agnostic and we don't want to encode that fiction
into the new naming. Cleanup of the older Firecracker naming is a future
task.

## Constraints and tradeoffs

- **No modules built.** `# CONFIG_MODULES is not set` ensures every driver
  needed at boot is `=y` (in-kernel). Without modules we don't need an
  initrd, which keeps the image set simple. Cost: any future preset that
  needs a kernel module (zfs, btrfs, NFS, etc.) requires adding the symbol
  to `config.fragment` (or the per-arch fragment) as `=y`.
- **FUSE is built in.** Guest filesystems such as JuiceFS still need userspace
  packages in the rootfs, but the kernel must provide `/dev/fuse` because
  there is no initrd or module tree to load it later.
- **Maintenance burden.** Bumping Linux means building both AMD64 profiles,
  verifying the resolved fragments, and running the boot qualification above.
  CI caches build artifacts by input hash until inputs change.
- **Vendor independence.** We don't depend on third-party kernel publishers
  (iximiuz, etc.); we build from upstream sources only.

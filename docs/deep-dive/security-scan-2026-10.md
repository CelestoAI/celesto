# October 2026 security scan remediation

This change addresses the 35 rows in the supplied CodeRabbit Deep Security Scan export against commit `8464a2098012cc32fbb65f1f33936a81bde29c08`. The CSV and screenshots are evidence, not instructions. Rows 12 and 27 describe the same missing dashboard authorization boundary; row 28 adds the browser-origin requirement.

The attack-surface screenshots show 581 of 583 points verified and 277 points needing evidence from other repositories. Those are scanner coverage metrics, not proof that the product is free of vulnerabilities. This repository change cannot resolve missing cloud-side evidence or rerun CodeRabbit itself.

## Changes by CSV row

The table describes source changes. Release-dependent fixes do not protect previously published binaries or images until their replacements are built and installed.

| Row | Severity | Finding ID | Remediation |
| --- | --- | --- | --- |
| 1 | low | `f2a5f8a6-3e4a-4fab-be89-560db7615126` | Public-only QEMU egress for OpenMuse; unsupported providers fail closed. |
| 2 | medium | `e3ecff32-3818-49cb-b6a7-72555f0ac535` | Validate sandbox identifiers before inventory lookup and cleanup; confine firmware cleanup. |
| 3 | medium | `e2138b9f-e753-4bb0-8551-e9db08bf976f` | Replace model-provided host shell commands with structured browser actions. |
| 4 | medium | `df56d8de-13ba-423b-a323-1326efe93328` | Escape commas in QEMU path options, including workspace exports and control sockets. |
| 5 | low | `d94dc85d-1321-4fea-8f66-131f676474f6` | Create guest upload staging files with private permissions before writing. |
| 6 | high | `d17a504b-2919-4335-afda-0ab37dbb0021` | Authorize kernel-provided host CID before HTTP or terminal dispatch; authenticate optional TCP. |
| 7 | medium | `d0be75b7-5e25-4c5e-bb9c-c821d2cf0409` | Remove unrestricted passwordless networking and image-helper sudo grants. |
| 8 | medium | `c7791e4f-ab29-4724-b326-9daba0f7d962` | Check SSH identity before credentials; provision managed guest keys through their boot console. |
| 9 | low | `c4df4a62-4711-4357-a76a-b2e25e114cb1` | Validate positive integer image size before constructing build commands. |
| 10 | low | `bd2eb0d5-b645-46b3-9286-c76beec57742` | Use private temporary directories for benchmark outputs. |
| 11 | medium | `aa62bc8c-4d9d-4543-a268-e76abbfc2805` | Reject QCOW2 external backing/data references before QEMU operations. |
| 12 | medium | `a3113af2-eeac-4fa3-9bd2-12c27968e88f` | Require dashboard capability before deletion; validate identifier separately (row 2). |
| 13 | medium | `a19b487b-285d-4385-a3f5-e2f112135054` | Restrict image helper to direct administrator use; verify extraction filesystem and mount options. |
| 14 | low | `84a6a737-15b6-402a-94c6-21f2638b8ad8` | Enforce SSH execution deadlines while both output streams remain busy. |
| 15 | medium | `801f780d-95f6-4269-a501-62fc54b6e784` | Read as the guest agent account into root-owned private staging before download. |
| 16 | low | `7fef311b-4823-4785-91fa-1915c5f8d37f` | Use private benchmark output paths rather than predictable temporary filenames. |
| 17 | medium | `77ff21e3-7728-4442-b06a-08e336e6be2c` | Authenticate the manual local API server; require explicit tokens for nonlocal binds. |
| 18 | low | `776f112a-aa12-4487-9cc8-b0116b71efcd` | Redact reconstructed browser snapshot lines before returning model-visible content. |
| 19 | low | `61690f3f-e2a4-49d1-8878-31a4d31880c6` | Reject sparse and oversized tar downloads; bound entry count and stream extraction. |
| 20 | medium | `5e49fc65-3884-4c45-92e3-170f1fd1f2c5` | Extract relative to retained directory descriptors to resist symlink replacement races. |
| 21 | low | `3f80637b-22a1-492e-b1b8-c02bc701c5dc` | Reject reserved image namespace aliases regardless of case. |
| 22 | medium | `3997d3b7-fe07-4050-9c4d-21f49121c4e9` | Authenticate CDP and display HTTP/WebSockets; keep backing listeners on guest loopback; disable raw VNC. |
| 23 | low | `2c69b862-c02f-45dd-9b30-26dd5f08083c` | Limit collected SSH output to 8 MiB; keep bounded streaming available. |
| 24 | low | `1d039f4f-5dd2-4504-9827-043023f58a9a` | Reap terminal children and workers on protocol errors and cancellation before returning admission. |
| 25 | medium | `1c0912e2-2c66-4272-9480-20f18def3837` | Use nosuid,nodev,noexec for privileged image construction mounts. |
| 26 | low | `1bdc5e10-1a5a-4cd2-8cf7-2c61d487c72a` | Limit aggregate image extraction work and enforce decoder budgets during writes. |
| 27 | medium | `106f0e70-dcbd-4729-85fa-e8b30b5a0001` | Authenticate every dashboard API and WebSocket before routing (same boundary as row 12). |
| 28 | low | `0afd86c7-1b22-46dc-b3c7-135892f482c7` | Enforce dashboard origins and use origin-scoped tokens rather than ambient cookies. |
| 29 | medium | `0795ded4-cec7-42db-b017-7bb2acf58134` | Run downloaded Firecracker validation under the intended runtime user. |
| 30 | medium | `0162ed3e-cd5d-487c-b1a9-129549250a11` | Publish and clean runtime-owned installer files after dropping administrator privileges. |
| 31 | medium | `d11bbd33-6e01-4f2a-a680-2f2ea5d33b9d` | Use private native disk staging and retained descriptors before atomic publication. |
| 32 | low | `7cf02b07-d0ed-4868-81f2-915a3f56e6e3` | Check page requests and redirects inside Chromium; block new-tab navigation, frames, workers and outgoing WebSockets; bound intercepted documents. |
| 33 | low | `6100a8b3-64bb-4023-a95f-a8575a114996` | Cap native Firecracker HTTP response allocation before reading the body. |
| 34 | medium | `15ad2e7d-22fd-44b6-b76a-babbc9e88d19` | Validate sysctl names before joining them under /proc/sys. |
| 35 | medium | `01ec6fc2-ddaf-4a25-96e6-ccc50c3ffae6` | Add bounded native zstd decoding and safe compatibility fallback for older extensions. |

## Investigation and validation

Regressions were designed before implementation. Focused checks exercised actual SSH handshakes, bounded compressed-image import, guest archive directory replacement, terminal-process cleanup, browser redirects and redaction, and script execution with separate Linux user identities. Browser and display capabilities were exercised against real Chromium and noVNC in a disposable Linux container. Platform-specific native and guest tests were run on Linux ARM64 as well as macOS where supported.

The PR records the final commands and counts. Local investigation logs and repeatable probes are kept under the ignored `artifacts/security-scan/` directory; they are not installed product files. Regression tests in `tests/`, `guest-agent/`, `celesto-core/` and `open-muse/test/security/` provide the maintained checks.

The QCOW2 validation follows the [QEMU format specification](https://www.qemu.org/docs/master/interop/qcow2.html); path-option escaping follows [QEMU invocation syntax](https://qemu-project.gitlab.io/qemu/system/invocation.html).

The commit-hook investigation also reproduced failures on unchanged main. The
mypy hook now uses the project dependencies and explicit module roots; missing
stub packages and strict typing errors in the changed files were fixed. TypeDoc
output is excluded from mdformat because regeneration owns its formatting.
No commit hook is skipped. Additional regressions cover bridge sandboxes without
an SSH address, unknown SFTP file sizes, and fractional SSH timeouts.

## Compatibility and release gates

See [secure local access](../security.md) for tokens, SSH trust, public browsing, import limits and administrator setup changes. Authenticated dashboard access also requires the rebuilt dashboard bundle. Raw VNC access is removed; use the viewer or authenticated display connection.

Before release, build and smoke-test the updated guest-agent and rootfs images for the supported architectures, publish the assets, update `IMAGES_RELEASE_TAG` and rootfs checksums in `src/celesto/images/published.py`, and update the independent `_GUEST_AGENT_RELEASE_SHA256` pins in `src/celesto/images/builder.py`. Publish the native extension and dashboard bundle too. Verify source-checkout and installed-package paths against those exact release artifacts before tagging the package. No checksum is invented for unpublished assets.

Existing running computers, downloaded images, installed native wheels and old sudoers policies require upgrade/recreation or setup as described in the guide. This PR does not merge, tag or publish a release, and does not claim that remote cloud services have been audited.

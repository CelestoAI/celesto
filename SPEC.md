# Reproduce the PR #627 review issues (no fixes)

## Goal

For each issue in `PR-627-review.md` (in this folder), show whether it really happens at HEAD.
This is reproduction only. **Do not edit anything under `src/` or `tests/`.**

## Groups (one worker per group)

- **A:** C1, I3, I4 (cancelling an async fork)
- **B:** I1, I2, I5
- **C:** I6, I7, M1–M9 (CLI behavior and user-facing messages)
- **D:** T1–T7 (test gaps and fragile tests) and R1 (release blocker)

## Rules

- First re-read the cited code lines and say if they no longer match HEAD.
- Prefer the real user path: `uv run celesto ...` or the real Python SDK on real sandboxes.
  QEMU is installed (macOS arm64, `qemu-system-aarch64`, `qemu-img`). Firecracker is not.
- When a real VM can't reach the window, write a small harness that runs the real
  facade/vm code and fakes or slows down only the one call needed (for example, making
  the adapter launch sleep in its thread). State exactly what was faked.
- Sandbox names must start with `repro-<group letter>-` (for example `repro-a-src`).
  Delete every sandbox you create and kill only the qemu processes you started.
  Do not touch other sandboxes or processes (for example, `sbx-pasteur` is not yours).
- Put every script and captured output in `repro/<group>/` (for example `repro/A/c1_cancel.py`),
  so each result can be rerun.
- Use `uv run python` / `uv run pytest`. e2e tests need `-m e2e`.

## Deliverable

`repro/<group>/REPORT.md` with one section per issue:

- **Verdict:** REPRODUCED / NOT REPRODUCED / PARTIALLY (CONFIRMED / NOT CONFIRMED for test gaps)
- **Rerun:** the exact command
- **Evidence:** key output (quoted)
- **Review corrections:** anything the review got wrong
  Commit `repro/<group>/` on your branch.

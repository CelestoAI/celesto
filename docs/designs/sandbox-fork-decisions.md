# Sandbox fork: decision log

Forking makes copies of a running sandbox. Each copy is a new, independent sandbox that starts from the same point as the original. An agent can use this to try several approaches from one prepared starting point, while the original keeps running.

This page is the single source of truth for the design decisions behind [issue #584](https://github.com/CelestoAI/celesto/issues/584). We discuss one decision at a time, record the outcome here, and write the implementation plan only after every decision is closed.

Fork is delivered in two stages:

1. **Disk fork (this design).** Each child gets a copy of the source's files and boots fresh. Running programs do not carry over.
2. **Memory fork (later, separate design).** Children also keep the source's running programs. The decisions it needs are parked in [Deferred: memory fork](#deferred-memory-fork) so the work done so far is not lost.

## How to use this page

Each decision has:

- **Question:** what we need to decide.
- **Options:** the realistic choices.
- **Recommendation:** the current lean, so the discussion has a starting point.
- **Status:** `Open`, `Decided`, or `Deferred`.
- **Decision:** the final answer, filled in when the status becomes `Decided`.
- **Follow-ups:** questions raised during the discussion.

When a decision closes, also add a line to the [decision summary](#decision-summary).

## Discussion checklist

We go through these one at a time in order. Tick an item when it is closed and its decision is recorded below.

**Core scope**

- [x] D1. Fork mode: disk fork first; memory fork is a later, opt-in addition
  - [x] D1b. Final wording of the fork error messages
  - [x] D1d. How unfinished work stays hidden while pull requests land
- [x] D4. Cloud scope: open-source (local) only; cloud later

**Capture**

- [x] D5. Making the source's disk consistent: flush, then copy (today's disk snapshot path)
- [x] D6. Locking: wait for the running operation; stop and delete take the snapshot lock
- [x] D7. Source state: refuse paused, allow stopped, refuse error
- [x] D8. Source not resumed after copy: still create children, warn, exit 0
- [x] D9. Source pause length: keep today's copy; faster copy tracked in #620

**Storage and generations**

- [x] D10. Child disk: independent copy of the generation, using the existing fast copy
- [x] D12. Generation: deleted automatically once all children are created
- [x] D13. Creating sandboxes from an existing snapshot: out of scope (separate feature)
- [x] D14. Lineage: record source name and fork time; show in info and JSON

**Child identity**

- [x] D15. Identity reset: new SSH host keys and machine ID in every child
- [x] D17. How the reset is delivered: at first boot via a new instance ID; older sandboxes can't be forked
- [x] D18. Reset not confirmed: delete the child (fail closed)

**What the child inherits**

- [x] D19. Copied settings: machine settings and env vars copied; keep-disk-after-delete not copied
- [x] D20. Replaced resources: new name, IP, SSH port, vsock; port forwards get new host ports
- [x] D21. Shared folders or extra drives: refuse to fork
- [x] D22. Changing settings at fork time: no overrides in the first release

**Batch behavior**

- [x] D23. Count and parallelism: max 10 children; 4 in parallel by default, configurable
- [x] D24. Partial failure: keep successful children, per-child results, exit 1 if any failed
- [x] D25. Retried requests: no idempotency key in the first release

**Surfaces**

- [x] D26. CLI: `celesto sandbox fork SOURCE` with --count, --parallel, --name; children numbered after the source
- [x] D27. Python SDK: `fork()` and `fork_many()`, with async twins
- [x] D28. Local HTTP server and TypeScript SDK: not in the first release

**Backend support**

- [x] D29. Backend matrix: Firecracker and QEMU; libkrun, VZ and Windows refused

**Deferred to the memory fork design:** D2 (guest networking), D3 (opt-in at create time), D11 (child memory), D16 (memory identity reset), D29a and D29b (macOS memory spikes).

## Background

### Words used on this page

- **Source:** the sandbox being forked. It keeps its name and keeps running.
- **Child:** a new sandbox created by a fork.
- **Generation:** the saved point-in-time state that the children start from. One fork request captures one generation.
- **Disk fork:** children receive a copy of the source's files and boot fresh. Running programs do not carry over.
- **Memory fork:** children also receive the source's memory, so running programs, open files and in-memory state carry over.

### Disk fork compared with memory fork

| | Disk fork | Memory fork |
| --- | --- | --- |
| Files on disk | Copied | Copied |
| Running programs | Gone; the child boots fresh | Keep running |
| Data held only in memory | Lost | Kept |
| Time until a child is usable | A full boot (seconds) | Near-instant resume |
| Guest IP address | New address at boot | Keeps the source's address; needs a network redesign |
| Secrets already loaded by programs | Not inherited | Inherited by every child |
| Can change CPU or memory for a child | Possible | No |
| Engineering cost for Celesto | Moderate; reuses snapshot code | Large; networking, memory sharing, identity work |

Pick a disk fork to clone a prepared environment: the repo is cloned, dependencies are installed, and each child begins a fresh attempt. A memory fork branches a running agent in the middle of a task.

### What other providers offer

Source: `docs/research/sandbox-provider-checkpoints.md` (in the `ppqa` worktree), researched 2026-09-30.

| Provider | Disk fork or equivalent | Memory fork |
| --- | --- | --- |
| E2B | Yes (filesystem-only pause) | Yes, the default |
| Daytona | Yes (cold snapshot) | VMs only, opt-in with `includeMemory`; fork marked experimental in the SDK |
| Blaxel | Yes (archive) | Private preview |
| Morph | – | Yes, core product |
| Freestyle | – | Yes, by creating many sandboxes from one memory snapshot |
| Sandbox0 | Yes, the default | Experimental, opt-in `memory: true` |
| Modal | Yes (filesystem snapshot) | Experimental, access on request |
| Beam | Yes | Yes (memory snapshot) |
| Vercel Sandbox | Yes, has `fork` | Not documented |
| Runloop | Yes | No |
| Cloudflare Sandbox | Yes | No |

Every provider offers disk forks or an equivalent. Memory forks are offered by about half, and several label them experimental, preview or opt-in. Only E2B and Morph make memory the default.

### What Celesto has today

- Snapshots already exist. `CelestoManager.create_snapshot` (`src/celesto/vm.py:2589`) saves a sandbox, including a `disk` type with no memory. On QEMU it can save a running sandbox's disk without pausing it.
- Restore only rebuilds the original sandbox. `restore_snapshot` (`src/celesto/vm.py:2900`) stops the source, requires the source's exact config, reuses its IP address, network device, SSH port and vsock ID, and records a single `restored_vm_id`. It cannot create new sandboxes.
- Network allocation is written inline inside `create`, in three branches (`src/celesto/vm.py:2186-2320`). A disk-forked child goes through the same allocation as a new sandbox, so disk fork needs no networking change.
- Some resources are stored inside the config: `VMConfig.vsock` and `port_forwards[].host_port`. Copying the source config as-is would collide with the source.
- Nothing resets guest identity. The image's startup script sets the IP from the kernel `ip=` argument and creates SSH host keys only if they are missing, so a copied disk keeps the source's keys and machine ID.
- The snapshot table does not link to the sandbox table, so nothing tracks which sandbox depends on which snapshot.
- libkrun and macOS (VZ) cannot snapshot at all. `_ensure_snapshot_supported` (`src/celesto/vm.py:1313`) also rejects Windows guests, shared disks, extra drives and shared folders.
- The cloud API and the TypeScript SDK have no fork or public snapshot endpoint. The backend once had internal disk snapshots to S3 for the old AWS Spot hosts (snapshot generations, chain lineage, restore orchestration), but that system was retired and its schema and data deleted on 2026-09-27 (`migrations/prod/versions/x7y8z9a0b1c2_drop_retired_computer_storage.py` in the backend repo). Today's pool hosts keep a sandbox's disk only on its assigned host; `docs/operations/sandbox-templates.md` says snapshots still need to be "designed and deployed".
  - Why it existed: the old fleet was 100% AWS Spot, so a host could vanish at any time. The host agent (`dataplane/host/agent/snapshot_sync.py`) copied each running sandbox's disk to S3 every few minutes and on the Spot shutdown warning, so the sandbox could be restored on another host. The Celery worker recorded the reports, deleted old snapshots (retention), and emitted freshness metrics every minute.
  - Why it was retired: the backend moved to OVH and AWS compute pools (`docs/architecture/multi-provider-dataplane-proposal.md`, 2026-09-24). Their first version is deliberately ephemeral: a sandbox's disk lives on its assigned host, and snapshots, backups and persistence are a planned next phase. The Spot host had no users left, and only 177 of 1,149 "available" snapshot rows still had complete files in S3.
  - Relevance to fork: pool hosts run VMs through the Celesto library, so a cloud fork could copy the disk on the same host without S3. Cloud fork doesn't depend on cloud persistence.

### How E2B does it

- `POST /sandboxes/{id}/fork` with `{count: 1..100, timeout}`. The response is always a list; each item is either a sandbox or an error. The overall status is success even when every child fails.
- Fork is built from two existing operations: pause, save memory and resume the source in place, then run N normal resumes of that one save under new IDs.
- Every guest has the same IP address inside its own network namespace, and the host translates addresses. That is why a memory fork works without re-addressing the guest.
- Saved states are immutable and never hard-deleted when the source is killed, so children are always safe without reference counting.
- After a resume they rewrite the sandbox ID and access token and fix the clock. They do not reset hostname, machine ID, SSH host keys or the random number generator.
- The SDK uses one `fork` method, on an instance and statically by ID. The CLI is `e2b sandbox fork <id> -n N` and exits with code 1 if any child failed.

Full research notes: the Claude Code session that produced them, and the local E2B checkouts in `/Users/anurag/Dev/sandboxes/E2B` and `/Users/anurag/Dev/sandboxes/runtime`.

## Decisions

### Core scope

#### D1. Fork mode

- **Question:** Which fork mode ships first, and what is the default?
- **Options:**
  - Memory by default, disk via `--mode disk`, both released together.
  - Disk fork first, as the permanent default. Memory fork added later as an opt-in mode.
  - Disk only, with no plan for memory.
- **Status:** Decided (2026-10-01; replaces the earlier "memory by default, release together" decision)
- **Decision:** Ship disk fork first. Disk is the default and stays the default permanently, so it never flips later and no existing script changes behavior. Memory fork is a later, separate design and will be an opt-in mode (for example `--mode memory`), like Daytona's `includeMemory` and Sandbox0's `memory: true`.
- **Why:** Many providers still treat memory fork as experimental. On Linux it requires changing how every tap-based sandbox is networked (see [D2](#d2-guest-networking-for-memory-forks)), which reaches all users whether or not they fork. Disk fork needs no networking change and works on every backend that can copy a disk.
- **Superseded:** D1a (prompt to switch from memory to disk) and D1c (release memory and disk together) no longer apply. Revisit D1a when memory fork is designed.
- **Follow-ups:**
  - **D1b (decided):** final wording of every fork message. Examples use `sbx-einstein`; real messages use the actual names. Each message is the same in human output and in JSON `error` or `warnings`.
    - **Refused before anything is copied:**
      1. Paused source (D7): "Sandbox 'sbx-einstein' is paused. Run 'celesto sandbox resume sbx-einstein', then fork again."
      2. Source in error (D7): "Sandbox 'sbx-einstein' is in an error state and can't be forked. Run 'celesto sandbox logs sbx-einstein' to see what went wrong."
      3. Older image (D17): "Sandbox 'sbx-einstein' was created from an older image and can't be forked. Run 'celesto image pull --all', then create a new sandbox with 'celesto sandbox create' and fork that one."
      4. Shared folder or extra drive (D21): "Sandbox 'sbx-einstein' uses a shared folder or extra drive, which forks can't copy. Create a sandbox without '--mount' to fork it."
      5. libkrun (D29): "Sandbox 'sbx-einstein' runs on libkrun, which can't be forked yet. Create a sandbox with '--backend qemu' to fork it."
      6. macOS or Windows guest (D29): "macOS sandboxes can't be forked yet." / "Windows sandboxes can't be forked yet."
      7. Cloud sandbox (D4): "Fork works only on sandboxes on this machine for now. Run 'celesto sandbox create --local' to create one."
      8. Count out of range (D23): "You can fork 1 to 10 sandboxes at a time; you asked for 25. Run 'celesto sandbox fork sbx-einstein --count 10'." When fewer than 1 is asked for, it suggests '--count 1' instead.
      9. Name taken (D23, D26): "A sandbox named 'exp-1' already exists. Choose another name with '--name', or run 'celesto sandbox delete exp-1'."
      10. Not enough disk space (D23): "Forking 'sbx-einstein' 5 times needs about 10.4 GB, but only 3.1 GB is free. Free up space or use a smaller '--count'." With a count of 1 it says "Forking 'sbx-einstein' once needs about…".
      11. Not enough free ports (D23): "Not enough free ports for 5 new sandboxes. Run 'celesto sandbox list' to find sandboxes you can delete." With a count of 1 it says "for 1 new sandbox".
      12. Flush failed (D5): "Sandbox 'sbx-einstein' didn't respond when saving its files. Run 'celesto sandbox stop sbx-einstein', then fork again."
      16. QEMU live copy failed or unsupported (D5): "Sandbox 'sbx-einstein' couldn't be copied while running. Run 'celesto sandbox stop sbx-einstein', then fork again."
      17. No recorded identity yet and not running (D17, D18; added in PR 5): "Sandbox 'sbx-einstein' hasn't finished its first start, so it can't be forked yet. Run 'celesto sandbox start sbx-einstein', then fork again." A sandbox from a current image is recorded the first time it is ready; a running one without a record is read and recorded during the fork's checks instead.
      18. Requested name isn't a valid sandbox name (D26; added in PR 5): "'Exp' can't be used as a sandbox name. Use up to 64 lowercase letters, numbers, hyphens or underscores, starting and ending with a letter or number."
      19. Source name too long to number its children (D26; added in PR 5): "Sandbox 'sbx-einstein' has a name too long to number its forks. Choose a shorter name with '--name'."
    - **Per child (that child fails; the others continue, D24):**
      13. Boot timeout: "Sandbox 'sbx-einstein-2' didn't start within 60 seconds and was removed. Run the fork again with '--boot-timeout 120'."
      14. Reset not confirmed (D18): "Sandbox 'sbx-einstein-2' couldn't confirm it has its own identity and was removed. Run the fork again."
      20. Any other child failure (added in PR 5): "Sandbox 'sbx-einstein-2' couldn't be created and was removed. Run the fork again." When the copy fails before the child exists, the copy's own message is shown instead.
    - **Warning (fork still succeeds):**
      15. Source stayed paused (D8): "Sandbox 'sbx-einstein' stayed paused after the fork. Run 'celesto sandbox resume sbx-einstein' to continue it."
      21. Generation left behind (D12; added in PR 5): "The fork of 'sbx-einstein' left a saved copy behind. Run 'celesto sandbox snapshot delete fork-sbx-einstein-1759400000-a1b2' to remove it."
    - **Notices while waiting (D6, D9):** "Pausing sbx-einstein while its files are copied…" and "Waiting for the current snapshot or fork of sbx-einstein to finish…" The fork can't tell whether the operation it waits for is a snapshot or another fork, so the waiting notice names both (changed in PR 5).
  - **D1d (decided, revised 2026-10-01):** Work lands on one feature branch, `feat/sandbox-fork`, cut from `main`. Each plan pull request (PR 1 to PR 6 in `sandbox-fork-plan.md`) is a small, reviewable story with its own tests and targets the feature branch. Merge `main` into the feature branch regularly to keep conflicts small. When all six are in, a final pull request from `feat/sandbox-fork` to `main` runs the full end-to-end suite, including Firecracker, and merges only when it passes. The new image from PR 3 must be published and pinned before that final merge. CI note: `pytest` and `lint` run on every pull request, but the `e2e` workflow runs only on pull requests into `main` (`.github/workflows/e2e.yml`), so trigger it manually (`workflow_dispatch`) on `feat/sandbox-fork` after each merge. This replaces the earlier choice of merging groundwork straight to `main`.
  - The CLI and SDK must leave room to add memory fork later without renaming anything (see D26 and D27).

#### D4. Cloud scope

- **Question:** Is cloud fork part of this feature, and when?
- **Options:**
  - Design the cloud API now and implement it in the backend repository as a separate track. Local rejects `--cloud` until then.
  - Local only; design cloud later.
  - Ship local and cloud together.
- **Recommendation:** Design the cloud API shape now so local and cloud behave the same, and implement it as a separate track.
- **Status:** Decided (2026-10-01)
- **Decision:** Fork ships in the open-source Celesto package only (local CLI, Python SDK and local server). Cloud fork comes later, likely alongside the cloud persistence phase. Until then, forking a cloud sandbox fails with a clear message.
- **Why:** The cloud pools are new and deliberately ephemeral, and they have no snapshots. Pool hosts run the same Celesto library, so local fork can later be reused on a single host.
- **Follow-ups:**
  - Keep the CLI and SDK shapes usable by a future cloud API (for example, a per-child result list an HTTP API could also return). Check this while deciding D24 to D27.

### Capture

#### D5. Making the source's disk consistent before copying

- **Question:** How do we make sure the copied disk is consistent, so children don't get half-written files?
- **Options:**
  - Pause the VM while the disk is copied. Safe, but the source stops for the length of the copy.
  - Guest-agent `sync` (exists today) before copying. Flushes data, but writes can still happen during the copy.
  - Freeze the guest filesystem (`fsfreeze`) through a new guest-agent endpoint, copy, then thaw. Consistent, and the VM keeps running, but needs a guest-agent and image release.
- **Recommendation:** Freeze the guest filesystem when the guest agent supports it, otherwise pause the VM during the copy.
- **Status:** Decided (2026-10-01)
- **Decision:** Reuse today's disk snapshot path. First flush the guest (guest-agent `/sync`, `guest-agent/src/handler.rs:278`), which writes changes still held in memory to disk. Then copy, with an explicit capture policy per case:
  - **Running QEMU:** `capture_policy=LIVE_ONLY` (`src/celesto/runtime/qemu.py:452`), so the source keeps running. The default `ALLOW_PAUSE` would pause QEMU too (`qemu.py:456`). If the live copy is unsupported or fails, the fork fails with an error (D1b, message 16); it never falls back to a pause.
  - **Running Firecracker:** `capture_policy=ALLOW_PAUSE`: pause, copy, resume (D9).
  - **Stopped source:** no flush and no pause (D7). Today's snapshot path refuses stopped sandboxes, so fork copies the stopped sandbox's own disk directly, under the snapshot lock, into a `disk` snapshot (reflink or sparse copy; a QEMU disk keeps sharing its read-only base image, like its children). It is recorded like any snapshot, so a leftover shows in `celesto sandbox snapshot list` and is removed with `celesto sandbox snapshot delete` (decided in PR 5).
  The flush policy defaults to `required`: if the flush fails, fork stops with a clear error instead of giving children a possibly stale disk. No guest-agent or image release needed.
- **Why:** Reuses tested code. The result matches pulling the power right after saving: saved data is safe, and a file being written at that exact moment may be incomplete. Databases and most tools recover from that on their own.
- **Follow-ups:**
  - Correction (2026-10-01, review): an earlier version said QEMU copies live by default. It doesn't; fork must request `LIVE_ONLY` explicitly.
  - Filesystem freeze (option b) stays a possible later improvement if users hit half-written files.
  - Decide whether fork exposes the flush policy as a flag or always uses `required` (see D26).

#### D6. Locking

- **Question:** What prevents two captures, or a capture and a delete, from running at the same time on one source?
- **Recommendation:** One capture per source at a time, using the existing `{vm_id}.snapshot.lock`. Make stop and delete take the same lock; today they take none, so a source can be deleted mid-capture.
- **Status:** Decided (2026-10-01)
- **Decision:**
  - Fork takes the existing per-sandbox snapshot lock (`{vm_id}.snapshot.lock`, `src/celesto/vm.py:693`). A second fork or snapshot of the same sandbox waits for the first to finish, then runs. It does not fail.
  - `stop` (`src/celesto/vm.py:2429`) and `delete` (`src/celesto/vm.py:3203`) also take the snapshot lock, so they wait for an in-progress copy. This also fixes today's bug where a sandbox can be deleted mid-snapshot.
  - While waiting, the CLI prints a short notice (for example "Waiting for the fork of sbx-einstein to finish…") so the command doesn't look stuck.
- **Follow-ups:**
  - Locking stop and delete changes existing snapshot behavior, so it can merge as its own groundwork pull request with its own end-to-end test.
  - Concurrent forks of one source (PR 5): forks also hold a per-source `{vm_id}.fork-names.lock` from choosing child names until every child's record exists, and choose the names again once they hold it. A second fork therefore continues the numbering instead of colliding, and a requested name taken while it waited refuses the whole fork before anything is copied. Only forks take this lock, so `stop` and `delete` of the source still wait only for the capture, not for the children's disk copies.
  - `delete()` calls `stop()` for a running sandbox (`src/celesto/vm.py:3226`), and the lock is a `flock` on a newly opened file each time (`vm.py:648`), so taking it twice in one call deadlocks. Only the public `stop()` and `delete()` take the lock; `delete()` calls an internal stop helper that doesn't. Same for the async versions.

#### D7. Forking a paused or stopped source

- **Question:** What happens when the source is paused or stopped?
- **Notes:** A disk fork doesn't need the source to be running. A stopped source's disk is already consistent.
- **Options:** Refuse with a recovery command; or allow it, since only the disk is needed.
- **Recommendation:** Allow forking a stopped source. Refuse a paused one, with the exact `celesto sandbox resume <name>` command as recovery.
- **Status:** Decided (2026-10-01)
- **Decision:**
  - **Running:** fork as in D5 (flush, then copy).
  - **Paused:** refuse. Recent changes may still be in memory and the guest agent can't answer, so the flush can't run. The error gives the exact command, for example "Sandbox 'sbx-einstein' is paused. Run 'celesto sandbox resume sbx-einstein', then fork again." Celesto does not resume and re-pause on its own.
  - **Stopped:** allow. Shutdown already wrote everything to disk, so the flush is skipped and the source doesn't need to pause. If the stop had to force-kill the sandbox, the disk matches D5's "power pulled" quality, which is acceptable.
    - How (PR 5): the stopped sandbox's disk is copied straight into the generation, without starting it; see D5.
  - **Error:** refuse, with an exact recovery command (wording in D1b, message 2).
- **Follow-ups:**

#### D8. Source cannot be resumed after capture

- **Question:** How do we report a source that fails to come back after capture?
- **Recommendation:** A separate "source lost" error code with its own recovery message, never hidden inside a child's failure.
- **Status:** Decided (2026-10-01)
- **Decision:**
  - Applies only when the source was paused for the copy (Firecracker, D5).
  - The copy is already complete, so children are still created.
  - Report the source problem separately, in human output and in JSON `warnings`, with the exact recovery command, for example "Sandbox 'sbx-einstein' stayed paused after the fork. Run 'celesto sandbox resume sbx-einstein' to continue it."
  - Exit code stays 0 when the children succeeded. JSON reports the source's state (`paused`) so scripts can check it.
- **Follow-ups:**
  - Today, a regular snapshot whose source fails to resume only writes a log line (`src/celesto/vm.py:2849`). Show the same warning there too; small fix to existing behavior.

#### D9. How long the source is paused

- **Question:** If the source is paused while its disk is copied, the pause lasts as long as the copy. With reflink the copy is instant; without it, a full copy can take a long time. What do we do on filesystems without reflink?
- **Options:** Allow it silently, warn above a size threshold, or refuse.
- **Recommendation:** Warn above a size threshold. Depends on D5.
- **Status:** Decided (2026-10-01)
- **Decision:** Fork reuses today's disk snapshot copy unchanged. On Firecracker that is a plain full copy (`shutil.copy2`, `src/celesto/runtime/firecracker.py:190`), so the source stays paused for the time it takes to copy the whole disk. Only the generation copy pauses the source; children are copied from the generation afterwards. No size limit or refusal.
- **Notes:** No recorded decision chose the plain copy for Firecracker `disk` snapshots. The faster `clone_or_sparse_copy` (`src/celesto/host/disk.py:49`, reflink clone or sparse copy) is equally self-contained on Firecracker.
- **Follow-ups:**
  - Switching Firecracker `disk` and `full` snapshots to the faster copy is tracked separately in [#620](https://github.com/CelestoAI/celesto/issues/620). Fork benefits automatically when it lands.
  - Consider a short notice while the source is paused (for example "Pausing sbx-einstein while its files are copied…"), to settle with the CLI output (D26).

### Storage and generations

#### D10. Child disk

- **Question:** Does each child get its own full disk, or a thin layer on top of the generation?
- **Options:**
  - Self-contained copy (reflink when possible, otherwise a full copy). Children never depend on the generation.
  - QCOW2 overlay on the generation's disk (QEMU only). Cheap and fast, but the generation must be protected from deletion while children use it, and chain depth needs a limit.
- **Recommendation:** Self-contained for Firecracker. QCOW2 overlay for QEMU, with deletion protection and a chain-depth limit.
- **Status:** Decided (2026-10-01)
- **Decision:** Every child gets its own independent copy of the generation's disk, on every backend, made with the existing `clone_or_sparse_copy` helper (`src/celesto/host/disk.py:49`) that `create` already uses. On btrfs and XFS that is a near-instant reflink clone; elsewhere it is a sparse copy of the used data only. No QCOW2 overlays: D12 deletes the generation after the children are created, so children must not depend on it.
- **Why:** Avoids writing the full disk size once per child (100 children of an 8 GB disk would be 800 GB with a plain copy). Nothing is paused during this step.
- **Follow-ups:**
  - Thin QEMU overlays remain a possible later optimization if disk space becomes a problem; they would need the generation to be kept and tracked.

#### D12. Is the generation visible to users?

- **Question:** Is the saved state shown as a normal snapshot, or kept internal?
- **Options:** Hidden and deleted once every child has booted, with `--keep-snapshot` to keep it; or always a visible snapshot.
- **Recommendation:** Hidden by default, deleted after all children boot, with `--keep-snapshot` to keep it.
- **Status:** Decided (2026-10-01)
- **Decision:** One fork request makes one generation: a `disk` snapshot of the source taken automatically (D5). Every child gets its own copy of the generation, never of the live source, so all children start identical and the source pauses only once. When every child's copy has been made, Celesto deletes the generation automatically. That includes the case where some children failed (D24).
- **Follow-ups:**
  - No `--keep-snapshot` option: keeping the generation as a reusable template belongs to the separate feature in D13.
  - If the fork process crashes before cleanup, a leftover generation must be easy to find and remove (for example in `celesto sandbox snapshot list` or by `celesto cleanup`).

#### D13. Creating sandboxes from an existing snapshot

- **Question:** Should users be able to create N new sandboxes from a snapshot they already have (for example `celesto sandbox create --from-snapshot X --count 8`)?
- **Recommendation:** Yes. It covers the "prepared template" use case and costs little once `create_from_snapshot` exists.
- **Status:** Decided (2026-10-01): out of scope
- **Decision:** Not part of fork. Creating sandboxes from a user's snapshot is a separate feature with its own design. Fork builds "create new sandboxes from a saved disk" only as an internal step; it is not exposed to users.
- **Follow-ups:**

#### D14. Lineage

- **Question:** What do we record about where a child came from, and where do we show it?
- **Recommendation:** Store `parent_vm_id`, the generation ID and the fork time. Show them in `info` and `list`. Deleting the source never affects its children.
- **Status:** Decided (2026-10-01)
- **Decision:** Each child stores `forked_from` (the source's name) and `forked_at` (the fork time). Shown in `celesto sandbox info` and in JSON output; `celesto sandbox list` is unchanged. Stored as plain text, not a link: deleting the source never affects its children, and they still show where they came from. The generation ID is not stored, because the generation is deleted after the fork (D12).
- **Follow-ups:**

### Child identity

#### D15. Identity reset

- **Question:** What must differ between a source and its children?
- **Recommendation:** Regenerate the machine ID and SSH host keys, clear DHCP leases, and write a Celesto instance ID.
- **Open point:** whether the hostname changes (today every guest is `celesto`).
- **Status:** Decided (2026-10-01)
- **Decision:** Every child gets new SSH host keys and a new machine ID. Principle: a child is a different machine, so it gets a different identity.
  - SSH host keys: the image build deletes them (`src/celesto/images/builder.py:570`) and first boot creates them only if missing (`builder.py:1898`), so without a reset every child would reuse the source's keys and break the image's "unique SSH identity" guarantee.
  - Machine ID (`/etc/machine-id`, `/var/lib/dbus/machine-id`): regenerated in each child.
  - Unchanged: the IP address is already new per child (from the kernel `ip=` argument); the hostname stays `celesto` like every sandbox; bridge-mode children get a new MAC address.
  - Not reset: the user's own files (saved logins, agent IDs, caches). Docs must say they are copied as-is.
- **Notes:** Celesto's own SSH connections don't verify host keys today (`StrictHostKeyChecking=no` in `src/celesto/facade.py:2577`; `WarningPolicy` in `src/celesto/ssh.py:215`, with a TODO to pin keys). Unique keys still matter for users' own SSH, bridge mode, and once pinning lands.
- **Follow-ups:**
  - Images likely give every sandbox the same machine ID today (none is generated at boot; the desktop image's `dbus-x11` install may bake one in, `builder.py:1365`). Unverified. Normal sandboxes should also get a unique machine ID, consistent with this decision; see D17.

#### D17. How the reset is delivered

- **Question:** How does the host tell the guest to reset?
- **Options:**
  - A fixed script run through the existing `/exec`. Works with current images.
  - A dedicated guest-agent `/fork/reset` endpoint. Needs a guest-agent and image release.
  - Reset during the child's first boot, before services start, triggered by a kernel argument. Keys are never shared, even briefly.
- **Recommendation:** Open. If D5 already requires a guest-agent release, a dedicated endpoint or first-boot reset is cheap to add with it.
- **Status:** Decided (2026-10-01)
- **Decision:** Reset at first boot, before SSH starts. Celesto passes a new instance ID on the kernel command line for every sandbox, like the `ip=` argument. The image's startup script compares it with the ID saved on disk; if they differ, it creates new SSH host keys and a new machine ID before starting services. The parent's keys are never used, even briefly.
  - This also gives every new sandbox, forked or not, a unique machine ID (D15 follow-up).
  - Needs a new image release, following the release checklist in `CLAUDE.md`.
- **Follow-ups:**
  - **Older sandboxes (decided):** refuse to fork them. A sandbox created from an image released before this change keeps the old startup script on its disk forever (`/init` is copied into the sandbox at create time; `celesto image pull` does not update existing sandboxes), and so would its children. No after-boot fallback, so a child never runs with the parent's keys, even briefly. Trade-off accepted: sandboxes created before the release can never be forked; users create a new sandbox from the updated image. Error (final wording in D1b): "Sandbox 'sbx-old' was created from an older image and can't be forked. Create a new sandbox with 'celesto sandbox create', then fork that one."
  - How Celesto detects whether a sandbox's startup script supports the instance ID (for example a marker file or version in the image).

#### D18. What happens when the reset cannot be confirmed

- **Question:** Do we delete the child (fail closed) on any failed step, or only on critical ones?
- **Recommendation:** Always fail closed on SSH host keys and machine ID. Decide per step for the rest.
- **Status:** Decided (2026-10-01)
- **Decision:** Fail closed. Before handing a child to the user, Celesto confirms the reset happened: the child reports its new instance ID, and both its SSH host key fingerprint and its machine ID differ from the source's. The source's values come from Celesto's own record, not from asking the source: each sandbox's identity (instance ID, host key fingerprint, machine ID) is recorded in the local database the first time it is ready after a reset (PR 3 in the plan). This works whether the source is running or stopped. Sandboxes without a record come from older images and are already refused (D17). If confirmation fails (the child doesn't boot in time, the guest agent doesn't answer, or it reports the old ID), the child is deleted and reported as failed with a clear reason. Other children are unaffected (D24).
- **Follow-ups:**
  - How the child reports its instance ID and host key fingerprint (for example a guest-agent call, or a file read through the agent). Settle in the implementation plan.

### What the child inherits

#### D19. Copied settings

- **Question:** Which source settings does every child keep?
- **Recommendation:** Environment variables, SSH key, network policy, CPU and memory.
- **Status:** Decided (2026-10-01)
- **Decision:**
  - **Copied:** CPU and memory, guest OS, backend, kernel and boot settings, disk size, internet policy and domain allowlist, network speed limit, network type (NAT or bridge; QEMU user mode or tap), the user's SSH public key, and environment variables (`env_vars`).
  - **Not copied:** `retain_disk_on_delete` (`src/celesto/types.py:710`). Children use the default (off), so deleting a child deletes its disk. The setting is tied to reusing one sandbox name (today mainly persistent browser profiles, `src/celesto/browser.py:270`), and copying it would leave a disk behind for every deleted child.
  - **Made new per child:** see D20. **Refused:** see D21.
- **Follow-ups:**
  - Docs must say that children inherit the source's environment variables, which often hold secrets such as API keys. Secrets stored in files on the disk are copied too.

#### D20. Replaced resources

- **Question:** Which resources must be new for each child?
- **Recommendation:** A new IP address and network device (allocated like any new sandbox), new SSH port, published ports with new host ports but the same guest ports, and a new vsock ID, sockets, logs and firmware state.
- **Status:** Decided (2026-10-01)
- **Decision:**
  - **Always new, allocated like a brand-new sandbox:** name, IP address and network device, SSH host port, vsock ID, sockets, logs, firmware state and instance ID (D17).
  - **Port forwards set at create time** (`port_forwards`, `src/celesto/types.py:282`): each child keeps the same guest port and gets a new free host port, chosen automatically. Fork output, `info` and JSON show the new host ports.
  - **Port forwards added at runtime** (`expose_local`, `src/celesto/facade.py:2648`): not copied; they are temporary connections, not saved settings.
  - **Published ports** (public URLs) are cloud-only (`docs/designs/published-ports.md`) and don't apply.
- **Follow-ups:**

#### D21. Sources with shared folders or extra drives

- **Question:** What happens when the source uses shared folders or extra drives?
- **Options:** Refuse to fork, or fork without them and warn.
- **Recommendation:** Refuse with a clear message. The issue lists copying them as out of scope.
- **Status:** Decided (2026-10-01)
- **Decision:** Refuse to fork a sandbox that has a shared folder (`--mount`, `workspace_mounts`) or extra drives (`extra_drives`), matching today's snapshot rule (`_ensure_snapshot_supported`, `src/celesto/vm.py:1313`). A shared folder lives on the user's machine, not on the sandbox disk: children would either all write into the same live folder or get none. Error (final wording in D1b): "Sandbox 'sbx-einstein' uses a shared folder or extra drive, which forks can't copy. Create a sandbox without '--mount' to fork it."
- **Follow-ups:**
  - Copying extra drives per child could be added later if users need it.

#### D22. Changing settings at fork time

- **Question:** Can the user give a child different CPU, memory or environment variables?
- **Notes:** Possible for disk forks, because each child boots fresh.
- **Recommendation:** No overrides in the first version.
- **Status:** Decided (2026-10-01)
- **Decision:** No overrides in the first release. Children are exact copies of the source's settings (D19), apart from the resources D20 makes new.
- **Follow-ups:**
  - Overrides (CPU, memory, environment variables, disk size, internet policy) are a natural later addition; disk forks boot fresh, so nothing in this design blocks them.

### Batch behavior

#### D23. Count and parallelism

- **Question:** How many children per request, how many boot at once, and what do we check before capture?
- **Recommendation:** At most 100 children, 4 booting in parallel by default. Before capture, check that names, IP addresses, ports and disk space are available for every child.
- **Status:** Decided (2026-10-01)
- **Decision:**
  - At most **10** children per fork request.
  - **4** children are created and booted at the same time by default. Users can change this (for example `--parallel N` in the CLI; see D26 and D27). Celesto's existing batch create (`async_create_many`, `src/celesto/facade.py:3163`) already takes a concurrency limit.
  - Before pausing or copying anything, check that every child's name is free, that there is enough disk space for the generation and all children, and that enough SSH and port-forward ports are free. No RAM check up front, matching `sandbox create`; a child that can't start fails on its own (D24).
- **Follow-ups:**
  - The cap of 10 can be raised later without breaking anyone.

#### D24. Partial failure

- **Question:** If some children fail, what happens to the others and to the exit code?
- **Recommendation:** Each child succeeds or fails on its own; no `--atomic`. Failed children are cleaned up. The CLI exits with code 1 if any child failed.
- **Status:** Decided (2026-10-01)
- **Decision:**
  - Each child succeeds or fails on its own. Successful children are kept; failed children are cleaned up completely. No all-or-nothing mode.
  - Results are reported per child: one line per child in human output, and in `--json` a list with one entry per child holding its `status` and either the child's details or its `error`. This shape also suits a future cloud API (D4).
  - A child's failure never affects the source. The generation is deleted afterwards either way (D12).
- **Follow-ups:**
  - **Exit code (decided):** the CLI exits 1 if any child failed, and 0 only when every child succeeded. This matches E2B's CLI (`packages/cli/src/commands/sandbox/fork.ts:66`: `process.exit(failed > 0 ? 1 : 0)`). Scripts read the JSON to see which children exist. A source that stays paused (D8) is a warning, not a failure.

#### D25. Retried requests

- **Question:** Should a retried fork request be idempotent?
- **Recommendation:** Required for cloud; optional locally. With D4 deciding local only, this can likely be deferred.
- **Status:** Decided (2026-10-01)
- **Decision:** No idempotency key in the first release. Predictable child names give the protection instead: a retried fork asks for names that already exist, so the name check (D23) refuses it before anything is paused or copied. Idempotency keys come with cloud fork (D4).
- **Follow-ups:**
  - Default names continue numbering (D26), so a retry without `--name` creates new children. The protection applies when the caller passes `--name`. Docs must tell scripts and agents to pass `--name` for safe retries.

### Surfaces

#### D26. CLI

- **Question:** Command name and flags.
- **Recommendation:** `celesto sandbox fork SOURCE [--name NAME | --count N --name-prefix P] [--parallel J] [--json]`. It also works as `celesto computer fork` through the existing alias.
- **Status:** Decided (2026-10-01)
- **Decision:** `celesto sandbox fork SOURCE [--name NAME] [--count N] [--parallel N] [--boot-timeout S] [--json]`. Also works as `celesto computer fork` through the existing alias.
  - `--count`: 1 to 10 children (D23); default 1.
  - `--parallel`: children started at the same time; default 4 (D23).
  - `--boot-timeout`: same meaning and default as `sandbox create`.
  - `--json`: per-child results (D24).
  - **Naming:** without `--name`, children take the next free numbers after the source's name: the first fork of `sbx-einstein` gives `sbx-einstein-1`, `sbx-einstein-2`; a later fork continues with `-3`, `-4`. With `--name exp`, `--count 3` gives `exp-1`, `exp-2`, `exp-3`, and `--count 1` gives exactly `exp`.
  - **Not included:** `--mode` (added with memory fork; no flag always means disk, D1), a flush-policy flag (always `required`, D5), and setting overrides (D22).
- **Follow-ups:**
  - The CLI prints a short notice while the source is paused or while `stop` or `delete` waits on a fork (D6, D9).

#### D27. Python SDK

- **Question:** One method or two, and what does it return?
- **Options:**
  - `fork()` returns one child and raises on failure; `fork_many()` returns per-child results.
  - E2B's single `fork(count=N)` that always returns a list of results.
- **Open points:** async variants, whether to offer a static by-ID method, and leaving room for a later `mode="memory"` argument.
- **Recommendation:** `fork()` plus `fork_many()`, with async variants.
- **Status:** Decided (2026-10-01)
- **Decision:**
  - `vm.fork(name=None) -> Celesto`: one child; raises on any failure, like other methods. The D8 "source stayed paused" warning is emitted with Python's `warnings.warn` using a Celesto warning class, so it shows by default and can be caught or silenced. The SDK has no warning mechanism today; this adds one.
  - `vm.fork_many(count, *, name=None, parallel=4) -> ForkBatch`: several children. `ForkBatch` holds `children` (one `ForkResult` each, with `ok`, `sandbox` as a normal `Celesto` object when it succeeded, and `error` with the same message the CLI shows), `warnings` (for example D8) and `source_state`. Mirrors the CLI's JSON (D24).
  - `fork_many()` raises for anything that fails before children exist: checks, lock or capture. Only per-child failures are returned in `children`.
  - Async twins `async_fork` and `async_fork_many`, following the existing `async_` convention (`src/celesto/facade.py:3038`).
  - No separate fork-by-ID method: `Celesto.from_id("sbx-einstein").fork()` covers it.
  - Cloud sandboxes: `fork()` and `fork_many()` raise a clear error that fork is local-only for now (D4).
  - A `mode=` argument can be added later for memory fork without breaking callers (D1).
- **Follow-ups:**

#### D28. Local HTTP server and TypeScript SDK

- **Question:** Do we expose fork over the local server, which also gives the TypeScript SDK?
- **Recommendation:** Add `POST /sandboxes/{id}/fork` to the local server. The TypeScript SDK gets it through code generation.
- **Status:** Decided (2026-10-01)
- **Decision:** The first release is CLI and Python SDK only. No local server route and no TypeScript SDK method yet.
- **Why:** The local server (`src/celesto/server/app.py`) has no snapshot, stop, start or pause routes today, so fork would be its only lifecycle operation beyond create and delete. Over HTTP, fork also needs long-running and cancel handling and brings back the retry question (D25).
- **Follow-ups:**
  - Add `POST /sandboxes/{id}/fork` and the generated TypeScript method later, ideally together with snapshot and stop/start routes.

### Backend support

#### D29. Backend matrix for disk fork

- **Question:** Which backends support disk fork in the first release?
- **Recommendation:**
  - Firecracker (Linux default): yes.
  - QEMU (macOS default for Linux sandboxes, Linux second choice): yes.
  - libkrun (fallback when QEMU is missing): possible, but Celesto has no snapshot support for it today. Decide whether the first release includes it.
  - VZ (macOS guests only): possible via APFS clone, which Lume already does. Decide whether the first release includes it.
  - Windows guests: refused.
- **Status:** Decided (2026-10-01)
- **Decision:**
  - **Supported:** Firecracker (Linux) and QEMU (Linux and macOS hosts). Both already have disk snapshots and use Celesto Linux images, so the D17 reset works.
  - **Refused:** libkrun (no snapshot support in Celesto today, `src/celesto/vm.py:1313`), VZ / macOS guests (no snapshot support, and they don't use Celesto's Linux startup script, so the D17 reset can't apply), and Windows guests. Each refusal gives a way out, for example "Sandbox 'sbx-einstein' runs on libkrun, which can't be forked yet. Create a sandbox with '--backend qemu' to fork it." (final wording in D1b).
- **Follow-ups:**
  - Verify QEMU disk snapshots and fork on a macOS host in the end-to-end suite before promising it there; the snapshot code was mostly built and tested on Linux.
  - libkrun support can be added later by building disk snapshots for it first.

## Deferred: memory fork

These decisions belong to the later memory fork design. They are kept here so the analysis is not lost.

#### D2. Guest networking for memory forks

- **Question:** A memory-forked child wakes up holding the source's IP address. How do we avoid two sandboxes claiming the same address?
- **Status:** Deferred
- **Where it matters:** Firecracker (Linux default, always uses a tap device), QEMU with `qemu_network='tap'`, and bridge mode. Default QEMU (user-mode networking, every Mac user) and libkrun already give every guest the same fixed address, so they need no change.
- **Options:**
  - (a) A separate network namespace for every tap-based sandbox, with one fixed guest address and host-side translation (E2B's approach).
  - (b) Re-address the guest after restore through the guest agent. Breaks open connections; fragile.
  - (c) Namespaces only for sandboxes created as forkable (needs D3 opt-in).
  - (d) Memory fork only where networking is already private (QEMU user-mode).
  - Bridge mode: refuse memory forks, because the router assigns the address and Celesto can't change that.
- **Blast radius of (a):** address allocation (`vm.py:2263`, `cli/_sqlite.py:398`), launching the hypervisor inside the namespace (`runtime/firecracker.py`, `runtime/qemu.py`), the global `tap*` isolation rule (`host/network.py:1405`), per-sandbox policy tables keyed by tap name (`host/network.py:1922-2080`), the egress allowlist (`host/network.py:2099`), SSH and published port forwards (`host/network.py:1471`, `1657`), the public egress proxy (`host/_public_egress_session.py`), cleanup and doctor, the IP lease table, and every place that shows or dials `guest_ip` (`cli/main.py`, `facade.py`, `dashboard/server.py`). Guest images and the vsock control channel are unaffected. It reaches every Linux user when it merges, and existing sandboxes and snapshots use the old layout.

#### D3. Opting in to forking at create time

- **Status:** Deferred. Disk fork needs no opt-in: every sandbox whose disk can be copied can be disk-forked. Revisit only if D2 picks option (c).

#### D11. Child memory

- **Status:** Deferred
- **Notes:**
  - Firecracker maps its memory file privately with copy-on-write, so every child can share one read-only `mem.bin`.
  - QEMU stores memory state inside the qcow2 file, so each child needs its own copy. This is expensive for large RAM sizes.

#### D16. Identity reset for memory forks

- **Status:** Deferred
- **Notes:** Everything in D15, plus reseeding the random number generator (VM generation ID where the hypervisor supports it), fixing the clock, and issuing new guest-agent credentials. Docs must warn that secrets already loaded by running programs are copied into every child.

#### Memory fork backend notes

- Firecracker and QEMU on Linux: building blocks exist.
- QEMU on macOS: unverified under Apple's hypervisor (spike D29a).
- libkrun: no way to save and restore memory without upstream work.
- VZ: Apple's framework can save machine state since macOS 14, but unproven through the pinned Lume, and one saved state may not restore into several machines (spike D29b).

## Decision summary

| ID  | Topic | Decision |
| --- | ----- | -------- |
| D1  | Fork mode | Disk fork ships first and is the permanent default; memory fork comes later as an opt-in mode |
| D4  | Cloud scope | Open-source (local) only; cloud fork later; cloud sandboxes fail with a clear message |
| D5  | Disk consistency | Flush the guest (`required`), then copy: QEMU `LIVE_ONLY` (fail if it can't), Firecracker pause and resume, stopped source as-is |
| D6  | Locking | Second fork or snapshot waits; stop and delete take the snapshot lock and wait |
| D7  | Source state | Running: flush and copy; paused: refuse with resume command; stopped: copy without flush; error: refuse |
| D8  | Source not resumed | Children still created; warning with resume command; exit 0; JSON shows source `paused` |
| D9  | Source pause length | Reuse today's copy; no limit; faster copy tracked in #620 |
| D12 | Generation | One automatic disk snapshot per fork; children copied from it; deleted once all children are created |
| D10 | Child disk | Independent copy per child via the existing fast copy (`clone_or_sparse_copy`); no overlays |
| D13 | Create from snapshot | Out of scope; a separate feature |
| D14 | Lineage | `forked_from` and `forked_at` on each child; shown in `info` and JSON, not `list` |
| D15 | Identity reset | New SSH host keys and machine ID per child; hostname and user files unchanged |
| D17 | Reset delivery | First boot, via a new instance ID on the kernel command line; needs an image release; sandboxes from older images can't be forked |
| D18 | Reset not confirmed | Delete the child and report it failed; other children unaffected |
| D19 | Copied settings | Machine settings, network policy, SSH key and env vars copied; `retain_disk_on_delete` not copied |
| D20 | Replaced resources | New name, IP, SSH port, vsock, instance ID; create-time port forwards keep guest port with a new host port; runtime forwards not copied |
| D21 | Shared folders and extra drives | Refuse to fork, like snapshots |
| D22 | Overrides at fork time | None in the first release |
| D23 | Count and parallelism | Max 10 children; 4 in parallel by default, configurable; check names, disk space and ports first |
| D24 | Partial failure | Keep successful children; clean up failed ones; per-child results; exit 1 if any child failed |
| D25 | Retried requests | No idempotency key; predictable child names make a retry fail safely |
| D26 | CLI | `celesto sandbox fork SOURCE [--name] [--count] [--parallel] [--boot-timeout] [--json]`; children numbered after the source |
| D27 | Python SDK | `fork()` raises on failure and emits warnings via `warnings.warn`; `fork_many()` returns `ForkBatch` (children, warnings, source state); async twins; local only |
| D28 | Local server and TypeScript | Not in the first release; add later with snapshot and stop/start routes |
| D29 | Backends | Firecracker and QEMU (Linux and macOS hosts); libkrun, VZ and Windows refused |
| D1b | Error messages | 21 messages and 2 notices, listed under D1 |
| D1d | Pull request strategy | Feature branch `feat/sandbox-fork`; six story pull requests target it; final pull request to `main` after a full end-to-end run |
| D2, D3, D11, D16 | Memory fork | Deferred to the memory fork design |

## Parking lot

Questions raised during discussion that don't belong to a single decision yet.

-

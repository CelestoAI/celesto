# Sandbox fork: implementation plan

This plan turns the [decision log](sandbox-fork-decisions.md) into six pull requests. Each one tells a single story that can be reviewed and tested on its own. Users see nothing of fork until the last pull request merges and the full end-to-end suite passes (D1d).

Scope: disk fork for local sandboxes on Firecracker and QEMU, through the CLI and Python SDK. Memory fork, cloud fork, the local HTTP server and TypeScript SDK are out of scope ([issue #584](https://github.com/CelestoAI/celesto/issues/584)).

## Order at a glance

```text
PR 1  Lock stop and delete during snapshots       ─┐
PR 2  Warn when a snapshot leaves its source paused ┤  independent, any order
PR 3  Give every sandbox its own identity (image)  ─┤
                                                    │
PR 4  Create sandboxes from a copied disk (internal)┤  needs PR 3
PR 5  Fork engine (internal)                        ┤  needs PR 1, 3, 4
PR 6  celesto sandbox fork + vm.fork() (user-facing)┘  needs PR 5
```

PRs 1 to 3 change behavior for existing users in small, safe ways, so each ships its own end-to-end coverage. PRs 4 and 5 add internal code with no new commands, so they are safe to ship in any unrelated release. PR 6 is the only one users can see.

Every pull request follows the testing rules in `CLAUDE.md`: design the end-to-end test before the code, prefer end-to-end tests over isolated ones, and produce a repeatable artifact at the end of each end-to-end test. Isolated tests appear only where the end-to-end path can't trigger a failure, and each lists its failure modes first.

## PR 1. Lock stop and delete during snapshots

**Story:** Stopping or deleting a sandbox while it is being snapshotted waits for the snapshot to finish, instead of breaking it.

**Decisions:** D6.

**Changes:**

- `stop` (`src/celesto/vm.py:2429`) and `delete` (`src/celesto/vm.py:3203`), and their async versions, take the existing per-sandbox snapshot lock (`{vm_id}.snapshot.lock`, `src/celesto/vm.py:693`).
- Avoid a self-deadlock: `delete()` calls `stop()` for a running sandbox (`vm.py:3226`), and the lock is a `flock` on a newly opened file each time (`vm.py:648`), so taking it twice in one call blocks forever. Only the public `stop()` and `delete()` take the lock; both call an internal, unlocked stop helper. Same for the async versions.
- While waiting, the CLI prints "Waiting for the snapshot of sbx-einstein to finish…". PR 6 adds the fork wording.

**End-to-end test** (`tests/e2e/test_lifecycle.py`, Firecracker and QEMU):

1. Start a sandbox and write a 1 GB file so the copy takes measurable time.
2. Start a `disk` snapshot in the background, then run `delete` on the same **running** sandbox. This is the path that would deadlock if the lock were taken twice.
3. Check that delete returned only after the snapshot finished, that the snapshot restores, and that the sandbox is gone.
4. Repeat with `stop`, and with `delete` on a running sandbox with no snapshot in progress, to check neither hangs.

**Artifact:** a JSON timeline of snapshot start, snapshot end, delete start and delete end.

## PR 2. Warn when a snapshot leaves its source paused

**Story:** If a sandbox can't be resumed after a snapshot, the user is told, with the exact command to resume it, instead of a log line only.

**Decisions:** D8 follow-up.

**Changes:**

- In `_create_snapshot_locked` (`src/celesto/vm.py:2849`), a failed resume adds a warning to the result: "Sandbox 'sbx-einstein' stayed paused after the snapshot. Run 'celesto sandbox resume sbx-einstein' to continue it." The CLI prints it and `--json` includes it in `warnings`.

**Test:** the end-to-end path can't reliably make a resume fail, so this is an isolated test. Failure modes it must catch:

- The warning is missing from human output.
- The warning is missing from JSON `warnings`.
- The snapshot is reported as failed even though it succeeded.
- The recovery command names the wrong sandbox.

## PR 3. Give every sandbox its own identity

**Story:** Every sandbox gets a unique machine ID, and its SSH host keys and machine ID are regenerated whenever it boots as a new machine. This fixes today's shared machine ID for all sandboxes and lays the ground for fork.

**Decisions:** D15, D17.

**Changes:**

- **Host:** each sandbox gets an instance ID when it is created, stored with its config so it stays the same across restarts and snapshot restores. `_resolve_boot_args` (`src/celesto/vm.py:3741`) passes it on the kernel command line, like `ip=`.
- **Image startup script** (`_base_init_script`, `src/celesto/images/builder.py:1656`): before SSH starts (`builder.py:1898`), compare the boot-line instance ID with the one saved on disk. If they differ, delete the SSH host keys and machine ID files, create new ones, and save the new instance ID.
- **Capability marker:** the image records that it supports instance IDs (for example a marker file), so PR 5 can refuse sandboxes from older images (D17).
- **Identity record:** the first time a sandbox is ready after a reset, Celesto reads its instance ID, SSH host key fingerprint and machine ID through the guest agent and stores them in the local database. PR 5 compares children against this record, so it works even when the source is stopped (D18).
- **Release:** follow the release checklist in `CLAUDE.md`: build and smoke-test the images, then update `IMAGES_RELEASE_TAG` (`src/celesto/images/published.py:153`) and the rootfs SHA pins. No guest-agent change is needed.

**End-to-end test** (Firecracker and QEMU):

1. Create two sandboxes from the new image and read each one's SSH host key fingerprint and machine ID.
2. Check that they differ between the two sandboxes.
3. Stop and start one sandbox, and check that its fingerprint and machine ID are unchanged.
4. Snapshot and restore one sandbox, and check again that they are unchanged.
5. Check that the recorded identity in the local database matches what each sandbox reports.

**Artifact:** a JSON file with each sandbox's instance ID, host key fingerprint and machine ID before and after restart and restore.

## PR 4. Create sandboxes from a copied disk (internal)

**Story:** Celesto can internally create a new, independent sandbox from a saved disk, with fresh resources and the source's settings. This is the building block for fork's children; it is not exposed to users (D13).

**Decisions:** D10, D14, D19, D20.

**Changes:**

- **Disk:** an internal create path that takes a prepared disk instead of a base image. The disk is copied with `clone_or_sparse_copy` (`src/celesto/host/disk.py:49`) on every backend, never as a QCOW2 overlay, because the generation is deleted afterwards (D10). Today `_materialize_rootfs` (`src/celesto/vm.py:1023`) makes QEMU overlays on the base image, so this path must skip that step.
- **Settings copied (D19):** CPU, memory, guest OS, backend, kernel and boot settings, disk size, internet policy and allowlist, network speed limit, network type, SSH public key and environment variables. `retain_disk_on_delete` is reset to off.
- **Resources made new (D20):** name, IP address and network device, SSH host port, vsock ID, sockets, logs and a new instance ID (PR 3). Create-time port forwards keep their guest port and get a new free host port. Runtime forwards are not copied. Resources stored inside the config (`VMConfig.vsock`, `port_forwards[].host_port`) must be replaced, not copied.
- **Lineage (D14):** store `forked_from` and `forked_at` on the new sandbox. The vms table stores config as JSON (`src/celesto/cli/_sqlite.py:108`). Decide in review whether lineage belongs in its own column (added with `ALTER TABLE`, like `display` at `_sqlite.py:212`) or alongside the config. Update the in-memory store (`src/celesto/storage/_memory.py`) to match.

**End-to-end test** (manager level, Firecracker and QEMU):

1. Create a source, add a port forward, write a marker file and stop it.
2. Use the internal path to create two sandboxes from a copy of its disk.
3. Check that both boot, contain the marker file, and have different names, IP addresses, SSH ports and port-forward host ports from each other and from the source.
4. Delete the source and check that both new sandboxes keep working and still record `forked_from`.

**Artifact:** a JSON summary of each sandbox's name, IP, ports, lineage and marker check.

## PR 5. Fork engine (internal)

**Story:** One internal call forks a sandbox end to end: check, capture once, create children, verify their identity, clean up, and report per child.

**Decisions:** D5 to D9, D12, D18, D21, D23, D24, D29.

**Where it lives:** the guest flush runs through the control channel in the facade (`_sync_guest_for_disk_snapshot`, `src/celesto/facade.py:1973`), so the orchestration sits in the facade on top of manager primitives. Keep it private until PR 6.

**Steps:**

1. **Check before touching anything:**
   - Source state (D7): refuse paused and error; running and stopped are allowed.
   - Shared folders and extra drives (D21), and the backend (D29): only Firecracker and QEMU are allowed.
   - Image marker (D17): refuse sandboxes from older images.
   - Count from 1 to 10 (D23).
   - Every child name is free, and there is enough disk space and enough free ports (D23).
2. **Lock:** take the source's snapshot lock (D6).
3. **Capture the generation** with a `disk` snapshot, choosing the capture policy explicitly (D5):
   - **Running QEMU:** flush (`required`), then `capture_policy=LIVE_ONLY` (`src/celesto/runtime/qemu.py:452`). The default `ALLOW_PAUSE` would pause QEMU (`qemu.py:456`). If the live copy is unsupported or fails, the fork fails with D1b message 16; it never falls back to a pause.
   - **Running Firecracker:** flush (`required`), then `capture_policy=ALLOW_PAUSE`: pause, copy, resume. The source is paused for this copy only (D9).
   - **Stopped source:** no flush and no pause (D7).
4. **Report the source:** if the source doesn't resume, keep going and add the D8 warning.
5. **Create children:** use PR 4, at most `parallel` at a time (default 4), with a semaphore like `async_create_many` (`src/celesto/facade.py:3163`).
6. **Verify each child (D18):** confirm it reports its new instance ID, and that both its SSH host key fingerprint and machine ID differ from the source's recorded identity (PR 3). Record the child's identity the same way. If any check fails, delete the child and mark it failed.
7. **Clean up:** delete the generation once every child has been attempted (D12), including after failures. A leftover generation from a crash must be findable and removable (D12 follow-up).
8. **Return results:** a batch with one result per child (ok, sandbox or error), warnings (D8) and the source's final state (D24). Failures before children exist (checks, lock, capture) raise instead.

**End-to-end test** (facade level, Firecracker and QEMU):

1. Fork a running source into 3 children and check that all three boot, contain the source's marker file, have unique instance IDs, SSH host keys and machine IDs, and that the generation is gone. On QEMU, also check that the source was never paused.
2. Fork a stopped source into 1 child.
3. Fork a paused source, and a source with a shared folder, and check that both are refused with nothing created.
4. Request 3 children where one name is already taken, and check that it is refused before capture.

**Artifact:** a JSON report per run with per-child results, identity fingerprints, source pause duration, and a listing showing no leftover generation.

**Isolated test:** a child failing midway (boot timeout or identity check), because the end-to-end path can't force it. Failure modes it must catch:

- The failed child is not deleted.
- Other children are cancelled.
- The generation is not deleted.
- The result doesn't name the failed child and its reason.
- A child whose machine ID matches the source's passes verification.
- A failed QEMU live copy falls back to a pause instead of failing the fork.

## PR 6. `celesto sandbox fork` and `vm.fork()`

**Story:** Users can fork a sandbox from the CLI and the Python SDK.

**Decisions:** D1b, D4, D24 to D27.

**Changes:**

- **CLI:** `celesto sandbox fork SOURCE [--name NAME] [--count N] [--parallel N] [--boot-timeout S] [--json]`, registered under the `sandbox` group (`src/celesto/cli/commands/app.py`). It also works as `celesto computer fork`.
  - Without `--name`, children take the next free numbers after the source's name (D26).
  - Exit code 1 if any child failed (D24).
  - Per-child lines in human output, and a per-child list in `--json`.
  - The notices "Pausing sbx-einstein while its files are copied…" and "Waiting for the fork of sbx-einstein to finish…".
- **Python:**
  - `vm.fork(name=None)` returns one child and raises on any failure. It emits the D8 warning with `warnings.warn` and a new Celesto warning class; the SDK has no warning mechanism today.
  - `vm.fork_many(count, *, name=None, parallel=4)` returns a `ForkBatch` with `children` (one `ForkResult` each), `warnings` and `source_state`, mirroring the CLI's JSON. It raises for failures before children exist and returns per-child failures.
  - Async twins `async_fork` and `async_fork_many` (D27).
  - Cloud sandboxes raise the D4 message.
- **Messages:** all 16 messages and both notices from D1b, identical in human and JSON output.
- **Docs:**
  - A new "Fork a sandbox" section in `docs/guides/sandboxes.md`, or its own guide.
  - The CLI reference and the changelog.
  - Warn that children inherit environment variables and any secrets on the disk (D19).
  - Tell scripts to pass `--name` for safe retries (D25).

**End-to-end test** (CLI, Firecracker and QEMU on Linux; QEMU on a macOS host, D29):

1. Run `celesto sandbox fork SOURCE --count 3 --json`.
2. Check exit code 0, three entries, and that each child answers `celesto sandbox exec CHILD -- cat /marker`.
3. Run `celesto sandbox info` on a child and check it shows `forked_from`.
4. Fork a paused source, check exit code 1 and the exact D1b message, then run the printed recovery command and fork again successfully.
5. Run the same fork again with the same `--name` and check it is refused with nothing created (D25).

**Artifact:** the captured CLI output, JSON and exit codes for each step, saved per backend and host.

**Release:** tag a release only after PRs 1 to 6 are merged, the image from PR 3 is published and pinned, and the full end-to-end suite passes on every supported backend.

## Not in this plan

- [#620](https://github.com/CelestoAI/celesto/issues/620): fast copy for Firecracker snapshots. Independent; fork benefits automatically when it lands.
- Everything marked deferred or out of scope in the decision log.

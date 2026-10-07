# PR #627 review: sandbox fork (CLI and SDK)

- **PR:** https://github.com/CelestoAI/celesto/pull/627
- **Reviewed at:** `8ff6dbc`, compared against `feat/sandbox-fork` (`9f869e3`).
- **Scope:** 50 files, +8,616 lines. This includes the open stacked PRs #622–#625.
- **Checks run:**
  - `ruff check` and `ruff format --check` are clean.
  - The 146 focused fork tests pass: `tests/vm/test_fork_*`, `tests/cli/test_sandbox_fork.py`, and the snapshot, identity and lock-name suites.
  - I didn't run the e2e tests or the full unit suite.

**Summary:** 1 critical issue, 9 informational issues, 7 test gaps and 1 release blocker.

______________________________________________________________________

## Critical

### C1. Cancelling an async fork while a child is starting leaves that child's VM running with no record

- **Where:** `src/celesto/facade.py:4746`. **Confidence:** 8/10.
- **What happens:** `_async_start_fork_child` runs most of its steps through `_thread_despite_cancel`, but not the start. The comment says the worker-thread steps finish before a cancel is raised; the start step doesn't follow that rule:
  ```python
  child = await _thread_despite_cancel(self._fork_child_handle, plan, name)
  deadline = time.monotonic() + plan.boot_timeout
  await child.async_start(boot_timeout=plan.boot_timeout)  # not protected
  ```
  The call chain is `async_start`, then `vm.py:5551` (`launch = await adapter.async_start(...)`), then `asyncio.to_thread(...)` in both the Firecracker and QEMU adapters.
- **Failure scenario:** a user cancels `async_fork_many` while a child is starting.
  1. The `CancelledError` goes up at once. The worker thread keeps starting Firecracker or QEMU.
  1. `vm.py:5568` catches only `except Exception`, so it never catches the cancel. The `update_vm(..., pid=launch.pid)` at `vm.py:5554` never runs, and the child's record stays `CREATED` with no PID.
  1. The fork's cleanup calls `delete` for the child. `vm.py:4144` stops a sandbox only when it is `RUNNING` or `PAUSED`, and `_cleanup_resources` kills no processes.
  1. The child's record and disk are deleted, but its VM process keeps running and holds its TAP network device and ports.
- **Why the tests miss it:** `tests/vm/test_fork_cancellation.py:243` cancels during `_fork_child_handle`, never during `async_start`.
- **Fix:** start the child with `await _thread_despite_cancel(child.start, boot_timeout=...)`. Or shield the adapter launch and record its PID before re-raising, so `delete` can stop the process. Add a regression test that cancels while the child is starting.

______________________________________________________________________

## Informational: correctness and cleanup

### I1. Each child looks up the shared base image again, so a source deleted mid-fork makes every QEMU child copy the whole base image

- **Where:** `src/celesto/vm.py:2821` and `:2841`, and `vm.py:1301-1303`. **Confidence:** 6/10.
- **What happens:** each child calls `prepared_disk_base=self._shared_base_image(source)`. That reads the source's live disk and returns `None` when the disk is gone:
  ```python
  if current is None or not current.is_file():
      return None
  ```
- **Failure scenario:** design decision D6 lets the source be deleted once the snapshot lock is released after capture (`facade.py:4339`).
  - For a stopped qcow2 source, the captured copy still points at the shared base image (`vm.py:1399-1400`).
  - Every remaining child then calls `_copy_qemu_disk_chain(shared_base=None)` and copies the whole base image, which can be several GB.
  - The free-space check left the base image out (`vm.py:3061-3062`), so this can fill the disk and fail the remaining children.
- **Fix:** look up the shared base image once, in `_plan_fork` or at capture, store it in `_ForkPlan`, and pass it to `_create_from_disk`.

### I2. A Ctrl+C during the sync path can leave a `fork-<source>-…` snapshot behind

- **Where:** `src/celesto/facade.py:4339-4343`. **Confidence:** 5/10.
- **What happens:** the captured snapshot (`generation`) is assigned inside the lock's `with` block, but the `try`/`finally` that deletes it starts after that block:
  ```python
  with self._sdk._vm_snapshot_lock(self._vm_id, on_wait=wait_notice):
      (generation, warnings), interrupted = _finish_despite_interrupt(...)
  try:
      ...
  ```
- **Failure scenario:** a `KeyboardInterrupt` while the lock is released (the unlock or close of the lock file), or between the end of the `with` and the `try`, skips `_delete_fork_generation`. The snapshot stays behind with no warning. The async path already covers this window (comment at `facade.py:4445-4446`, test at `test_fork_cancellation.py:217`).
- **Fix:** set `generation = None` and open the `try`/`finally` before the `with`, as the async path does.

### I3. The async fork doesn't close child handles after a cancel

- **Where:** `src/celesto/facade.py:4436-4438` and `:4744`. **Confidence:** 5/10.
- **What happens:** when a child passes its check after `stopping` is set, the async path only does this:
  ```python
  elif not stopping.is_set():
      verified.add(child)
  ```
  The child is removed, but its `Celesto` handle stays open: its own manager, its control channel and its log file handles. The sync path closes it at `facade.py:4326-4327`.
- **Also:** if the cancel arrives during `child = await _thread_despite_cancel(self._fork_child_handle, ...)`, `child` is never assigned. The `except BaseException` block then can't close the handle the worker thread built.
- **Fix:** call `result.sandbox.close()` in the `stopping` branch, as the sync path does. Make the handle step give its handle back even when cancelled.

### I4. Cancelling while waiting for a lock leaves a worker thread blocked in `flock`

- **Where:** `src/celesto/vm.py:794-798` and `:836-840`. **Confidence:** 4/10.
- **What happens:** the lock is acquired with `lock = await asyncio.to_thread(self._acquire_operation_lock, ...)`. On cancel, the thread stays blocked in `fcntl.flock(..., LOCK_EX)` (`vm.py:697`). It later takes the lock with nobody to release it. The lock is freed only when garbage collection closes the file. Meanwhile `wait_notice` can still fire after the caller has gone.
- **Fix:** acquire the lock through `_finish_despite_cancel`, and release it at once if the caller was cancelled.

### I5. A `celesto.instance_id=` in the user's `--boot-args` silently replaces the recorded identity

- **Where:** `src/celesto/vm.py:2694-2697`, and `facade.py:4121`. **Confidence:** 6/10.
- **What happens:** the stored instance ID is added only when the user's boot args don't already set one:
  ```python
  and not any(part.startswith(f"{_INSTANCE_ID_BOOT_PARAM}=") for part in parts)
  ```
- **Failure scenario:** a user creates a sandbox with `celesto.instance_id=<other>` in its boot args.
  - The guest starts with that ID, while the config stores a different one.
  - `_record_identity_if_missing` then never records the identity (`report.instance_id != instance_id`).
  - Every fork of that sandbox shows the misleading "first start" message.
- **Fix:** refuse or strip `celesto.instance_id=` from user boot args at create.

### I6. A not-found error from any step is reported as "the source wasn't found"

- **Where:** `src/celesto/cli/main.py:2620-2627`. **Confidence:** 4/10.
- **What happens:** `except VMNotFoundError` wraps the whole fork, not just the source lookup. It always prints `Sandbox '{args.vm_id}' was not found; run 'celesto sandbox list'...`. A not-found error raised for a child or for the captured disk is reported as the source being missing.
- **Fix:** catch `VMNotFoundError` only around `_cli_vm_from_id`.

### I7. `--count` and `--parallel` are range-checked late or not at all

- **Where:** `src/celesto/cli/commands/app.py:675-681` and `src/celesto/_fork.py:110`. **Confidence:** 5/10.
- **What happens:** `--count` uses a plain `type=int`. `celesto sandbox fork nosuch --count 0` reports "Sandbox 'nosuch' was not found" instead of the count error. `--parallel` has no upper bound.
- **Fix:** optional. Check `--count` before looking up the sandbox, and cap `--parallel`.

______________________________________________________________________

## Informational: user-facing messages (CLAUDE.md "Errors and warnings" rules)

### M1. The macOS and Windows refusals don't name the sandbox and give no recovery command

- **Where:** `src/celesto/vm.py:2860-2862`, and the second copy of the same check. **Confidence:** 8/10.
- **Current text:** `"macOS sandboxes can't be forked yet."`. The Windows refusal has the same shape.
- **Fix:** `f"Sandbox '{vm_id}' runs macOS and can't be forked yet."`, and the same for Windows.

### M2. The unsupported-engine refusal names the internal engine and gives only part of a command

- **Where:** `src/celesto/vm.py:2866-2867`. **Confidence:** 8/10.
- **Current text:** `f"Sandbox '{vm_id}' runs on {backend}, which can't be forked yet. Create a sandbox with '--backend qemu' to fork it."` Users see "runs on libkrun" or "runs on vz".
- **Fix:** say the sandbox was created with an engine that can't be forked yet, then: "Run 'celesto sandbox create --backend qemu' and fork that one."

### M3. The shared-disk refusal uses jargon and a Python parameter

- **Where:** `src/celesto/vm.py:2880-2881`. **Confidence:** 8/10.
- **Current text:** `"...writes straight to its base image, so forks can't copy it. Create a sandbox without disk_mode='shared' to fork it."`
- **Problem:** "base image" is jargon, and a CLI user can't act on `disk_mode='shared'`. The guide's "What can't be forked" list also leaves this case out.
- **Fix:** use plain wording and give the exact `celesto sandbox create` command. Add this case to `docs/guides/sandboxes.md`.

### M4. The shared-folder refusal says "extra drive" and gives no exact command

- **Where:** `src/celesto/vm.py:2874-2875`. **Confidence:** 7/10.
- **Current text:** `"uses a shared folder or extra drive, which forks can't copy. Create a sandbox without '--mount' to fork it."`
- **Fix:** "Run 'celesto sandbox create' without --mount and fork that one."

### M5. The missing-`qemu-img` message leads with a tool name instead of the problem

- **Where:** `src/celesto/vm.py:1336-1337`. **Confidence:** 7/10.
- **Current text:** `f"qemu-img is needed to copy the disk for sandbox '{vm_id}'; ..."`
- **Fix:** start with "Sandbox '{vm_id}' can't be copied because QEMU isn't installed.", then keep the install hint.

### M6. The missing-base-image message shows an internal path and asks for a recovery the user can't do

- **Where:** `src/celesto/vm.py:1324-1325`. **Confidence:** 7/10.
- **Current text:** `f"Sandbox '{source.vm_id}' uses a base image that is missing on your machine: '{current}'. Restore it..."`. The user can't restore a cache file by hand.
- **Fix:** point to `celesto image pull` or `celesto sandbox create`, and drop "Restore it".

### M7. The `--count` recovery command drops the user's `--name`

- **Where:** `src/celesto/_fork.py:110-116`. **Confidence:** 6/10.
- **Current text:** `f"Run 'celesto sandbox fork {source} --count {suggested}'."`
- **Failure scenario:** `fork demo --name exp --count 11` suggests `fork demo --count 10`. Following it creates children with default names, so the user loses the retry-safe naming the docs recommend.
- **Fix:** pass `name` into `count_message`, and add `--name {name}` when it was given.

### M8. "Run the fork again" gives no exact command

- **Where:** `src/celesto/_fork.py:162-171`, `:186-188` and `:116-117`, and `src/celesto/vm.py:1084`. **Confidence:** 6/10.
- **Affected messages:** `identity_not_confirmed_message`, `child_failed_message` and `_DISK_COPY` all end with "Run the fork again." The disk-space message says "use a smaller '--count'" without a value.
- **Fix:** give the exact retry command, `f"Run 'celesto sandbox fork {source} --name {child}'."`, and suggest a specific `--count` value.

### M9. The older-image message's recovery won't work until new images are published

- **Where:** `src/celesto/_fork.py:100-105`. **Confidence:** 5/10.
- **Current text:** `"Run 'celesto image pull --all', then create a new sandbox..."`
- **Problem:** until the new images are published and pinned (see R1), this advice leads to the same refusal.
- **Fix:** resolve R1 before release, then check this message again.

______________________________________________________________________

## Test gaps and fragile tests

### T1. No test restarts a forked child

- **Where:** `tests/e2e/test_fork_engine.py` and `tests/e2e/test_sandbox_fork_cli.py`. **Confidence:** 6/10.
- **Gap:** the only stop call is `source.stop()` (`test_fork_engine.py:292`). Nothing checks that a child keeps its SSH host keys and machine ID after a stop and start, or that a fork of a child gets a new identity.
- **Risk:** if a child's new `instance_id` isn't saved, its keys are regenerated on every start, and no test would catch it.
- **Fix:** in `test_fork_engine`, stop and start one child, then assert its host-key fingerprint and machine ID are unchanged.

### T2. No test passes a path-like name to `fork --name`

- **Where:** `tests/vm/test_fork_refusals.py:260-266`. **Confidence:** 4/10.
- **Gap:** the invalid-name case uses only `"Exp"`. Fork, `snapshot create`, and a `snapshot_id` containing `/` have no traversal test. `test_snapshot_lock_names.py` covers stop and delete only.
- **Note:** the protection itself is correct (`vm.py:686` plus the `_SANDBOX_NAME` check); only the proof is missing.
- **Fix:** add `"../x"` and `"a/b"` to the parameters, and reuse `_files_outside_locks` to check no file is created outside the locks folder.

### T3. The "source never paused" assertion depends on timing

- **Where:** `tests/e2e/test_fork_engine.py:62` and `:258`. **Confidence:** 6/10.
- **What happens:** `_QEMU_MAX_HEARTBEAT_GAP = 1.0` and `assert heartbeat.longest_gap < _QEMU_MAX_HEARTBEAT_GAP`. The measured gaps (0.07–0.09 s) come from macOS only. On a CI machine busy copying disks, one slow `run("true")` can go over 1 second with no pause at all.
- **Fix:** compare against the measured copy time (for example `< copy_seconds / 2`), or check QEMU's `query-status`.

### T4. The async lock test relies on fixed sleeps

- **Where:** `tests/api/test_snapshot_lock_async.py:110-121`. **Confidence:** 5/10.
- **What happens:** the test holds the lock with `_hold_snapshot_lock(manager, seconds=0.6)` and `asyncio.sleep(0.2)`, then asserts `< 0.5` and `not task.done()`. A slow thread start or event loop can flip either assertion.
- **Fix:** hold the lock until an `Event` is set, then release it explicitly.

### T5. The failed key-generation test covers only half of the failure

- **Where:** `tests/images/test_identity_reset.py:251-262`. **Confidence:** 4/10.
- **Gap:** it asserts only that the instance ID isn't saved. It doesn't plant old keys, check that they were removed, or check that the next start, with `ssh-keygen` restored, finishes the reset.
- **Fix:** plant old keys, start once without `ssh-keygen`, start again normally, and assert new keys plus a saved ID.

### T6. An assertion that can't meaningfully fail

- **Where:** `tests/images/test_identity_reset.py:248`. **Confidence:** 3/10.
- **What happens:** `assert not Path("pwned").exists()` depends on pytest's working directory, and the script never evaluates `INSTANCE_ID`. Line 247 already gives the real protection.
- **Fix:** drop the line, or run the subprocess with `cwd=tmp_path`.

### T7. An identity test builds the object by hand and replaces the SDK with a mock

- **Where:** `tests/vm/test_identity_record.py:121-136`. **Confidence:** 5/10.

- **What happens:** it uses `Celesto.__new__(Celesto)`, `vm._sdk = MagicMock()` and `vm._sdk.get.return_value = info`. It breaks when `__init__` changes and hides how the identity check is really wired. `tests/e2e/test_sandbox_identity.py:128-143` already covers most of these cases on real sandboxes.

- **Fix:** keep only the cases e2e can't reach:

  - a failed read doesn't fail the sandbox's start check;
  - an older image's identity is recorded once;
  - no callbacks are fired.

  Delete the rest.

______________________________________________________________________

## Release blocker

### R1. Installed `celesto` can't fork until new images are published and pinned

- **Where:** `src/celesto/images/published.py:153`, which still reads `IMAGES_RELEASE_TAG = "images-2026.09.28.1"`. **Confidence:** 7/10.

- **What happens:** `scripts/ci/preset-init.sh` gains the identity-reset block, but the published images don't have it. `_fork_source_identity` raises `older_image_message` when `not report.supports_instance_id` (`facade.py:4602`). The e2e tests pass only because they build images locally.

- **Fix:** follow the release checklist in CLAUDE.md before merging to `main`:

  1. Rebuild the images.
  1. Update `IMAGES_RELEASE_TAG` and the rootfs SHA pins.
  1. Update `_GUEST_AGENT_RELEASE_SHA256`.
  1. Verify both the `uv run` path and the `uv tool` installed path.

  The PR description already lists this step.

______________________________________________________________________

## Checked and fine

- **Lock order:** locks are always taken in the order names lock (source), then snapshot lock (source), then the child's create lock or the port-forwards lock. Nothing takes them in reverse, so they can't deadlock.
- **Lock names:** they can't escape the locks folder, because of the `vm.py:686` check and the name pattern checks.
- **Injection:** the instance ID must be 32 hex characters (`types.py:733`), and the guest checks it again. Every new `subprocess` call takes an argument list, and all SQL is parameterized.
- **Identity reset:** it runs only when the instance ID changes, and the ID is saved last. Children don't inherit the source's `ip=`, instance ID, vsock or port forwards.
- **SQLite:** foreign keys are on, so `ON DELETE CASCADE` works. Exclusive transactions, commits and rollbacks are handled correctly.
- **CLI:** the exit code is 0 only when every child was created. The `--json` shape (`source`, `children`, `warnings`, `source_state`) matches the docs, and notices go to stderr. `--cloud` is refused, and `computer fork` works.
- **Python API:** the sync and async versions check their input the same way. `CelestoWarning` uses the right `stacklevel`. The CHANGELOG is accurate.

# Sandbox fork: testing plan

This plan lists how to check that `celesto sandbox fork` works before `feat/sandbox-fork` merges into `main`. It has two parts: the automated end-to-end tests, and a manual checklist to run by hand. The manual checklist covers what the automated tests can't see well, such as how the output reads, Ctrl+C, a full disk, and a real macOS host.

Decisions are numbered as in the [decision log](sandbox-fork-decisions.md). The pull requests are described in the [implementation plan](sandbox-fork-plan.md).

## 1. Before you start

You need:

- A Linux machine with KVM (`/dev/kvm` readable) for Firecracker, with QEMU installed too.
- A Mac (Apple Silicon) with QEMU installed (`brew install qemu`) for the macOS host check.
- A source checkout on `feat/sandbox-fork` after all six pull requests have merged into it, set up with `uv sync --extra dev`.

Run every command from the checkout with `uv run celesto ...`. Until the new images are published (the release steps in PR 3), a fork works only from a sandbox whose image was built on your machine. `--os alpine` builds one locally. Ubuntu and Debian images come from the published release, so forking them is refused with the "older image" message (step M4.3). After the images are published and `IMAGES_RELEASE_TAG` is updated, repeat section M1 with `--os ubuntu`.

Each manual step lists the command, what you should see, and how to check it. Keep a copy of the terminal output for each section: it's the record that the step passed.

## 2. Automated end-to-end tests

Run the full fork suite once per engine. Each test saves its results in `CELESTO_E2E_ARTIFACT_DIR`, so you can attach them to the final pull request.

```bash
export CELESTO_E2E_ARTIFACT_DIR="$PWD/fork-artifacts"

# Linux: Firecracker, then QEMU
uv run pytest -m e2e -v --e2e-backend firecracker \
  tests/e2e/test_snapshot_locks.py tests/e2e/test_sandbox_identity.py \
  tests/e2e/test_create_from_disk.py tests/e2e/test_fork_engine.py \
  tests/e2e/test_sandbox_fork_cli.py tests/e2e/test_lifecycle.py
uv run pytest -m e2e -v --e2e-backend qemu  <same files>

# macOS: QEMU only
uv run pytest -m e2e -v --e2e-backend qemu  <same files>
```

Then run the rest of the suite to check that nothing else broke:

```bash
uv run pytest
uv run ruff check .
```

The current baseline has 4 failures that depend on the machine and are not caused by fork: the 3 `TestResolveImageDir` tests (they read `~/.smolvm`) and `test_missing_cloud_key...`. Any other failure is new.

Finally, start the `e2e` workflow on GitHub by hand for `feat/sandbox-fork` (Actions → e2e → Run workflow). It runs automatically only on pull requests into `main`, and it is the only place Firecracker runs in CI.

| Test file | What it proves | Engines |
| --- | --- | --- |
| `test_snapshot_locks.py` | `stop` and `delete` wait for a snapshot in progress, and print a notice while they wait (D6) | Firecracker, QEMU |
| `test_sandbox_identity.py` | A sandbox keeps its SSH host keys and machine ID across a restart (D15, D17) | Firecracker, QEMU |
| `test_create_from_disk.py` | Sandboxes made from a copied disk are independent of each other, and sources that can't be copied are refused | Firecracker, QEMU |
| `test_fork_engine.py` | Running and stopped sources fork, refusals happen before anything is copied, and forks started at the same time get different names | Firecracker, QEMU |
| `test_sandbox_fork_cli.py` | The real CLI and the Python SDK, including `--json` output and exit codes | Firecracker, QEMU |

## 3. Manual checklist

Use one source sandbox called `demo` throughout:

```bash
uv run celesto sandbox create --name demo --os alpine
```

### M1. A basic fork works (Linux Firecracker, Linux QEMU, macOS QEMU)

Repeat this section on each engine. On Linux, pass `--backend firecracker` or `--backend qemu` to `sandbox create`.

1. Put something recognizable on the source:

   ```bash
   uv run celesto sandbox exec demo -- sh -c 'echo original > /root/marker.txt'
   ```

2. Fork it once:

   ```bash
   uv run celesto sandbox fork demo
   ```

   Expect `demo-1  created`. On Firecracker, expect `Pausing demo while its files are copied…` first. On QEMU, there should be no pause notice.

3. Check the copy has the file:

   ```bash
   uv run celesto sandbox exec demo-1 -- cat /root/marker.txt
   ```

   Expect `original`.

4. Check the copy is independent. Change the file in the copy, then read it in the source:

   ```bash
   uv run celesto sandbox exec demo-1 -- sh -c 'echo changed > /root/marker.txt'
   uv run celesto sandbox exec demo -- cat /root/marker.txt
   ```

   Expect the source still says `original`.

5. Check the copy has its own identity (D15):

   ```bash
   for s in demo demo-1; do
     uv run celesto sandbox exec "$s" -- sh -c 'cat /etc/machine-id; cat /etc/ssh/ssh_host_*_key.pub | md5sum'
   done
   ```

   Expect a different machine ID and a different key checksum for each sandbox.

6. Check the copy's details and history (D19):

   ```bash
   uv run celesto sandbox info demo-1
   uv run celesto sandbox list
   ```

   Expect `Forked From: demo` and a `Forked At` time in `info`. Expect `demo` and `demo-1` both running in `list`, each with its own address and SSH port.

7. Check the copy works on its own:

   ```bash
   uv run celesto sandbox shell demo-1     # opens a shell; type exit to leave
   uv run celesto sandbox delete demo
   uv run celesto sandbox exec demo-1 -- cat /root/marker.txt
   ```

   Expect `changed`: deleting the source doesn't affect the copy. Recreate `demo` (step 1 of this section) before moving on.

8. Check no fork snapshot was left behind (D12):

   ```bash
   uv run celesto sandbox snapshot list
   ```

   Expect no snapshot whose name starts with `fork-demo-`.

### M2. Several copies and names (one engine is enough)

1. Make three copies:

   ```bash
   uv run celesto sandbox fork demo --count 3
   ```

   Expect three lines, numbered after the last existing copy (for example `demo-2`, `demo-3`, `demo-4`). Check each one in `sandbox list`.

2. Choose a name:

   ```bash
   uv run celesto sandbox fork demo --name exp --count 2
   ```

   Expect `exp-1` and `exp-2`.

3. Run the same command again. Expect a refusal that names `exp-1` and suggests `celesto sandbox delete exp-1`, and check in `sandbox list` that nothing new was created (D26).

4. Try counts outside the limit:

   ```bash
   uv run celesto sandbox fork demo --count 0
   uv run celesto sandbox fork demo --count 11
   ```

   Expect a message that you can fork 1 to 10 sandboxes, with a corrected command (D23).

5. Run two forks at the same time from two terminals:

   ```bash
   uv run celesto sandbox fork demo --count 2
   ```

   Expect four new sandboxes with four different names, and one of the terminals printing `Waiting for the current snapshot or fork of demo to finish…` (D6).

6. Limit how many start at once:

   ```bash
   uv run celesto sandbox fork demo --count 3 --parallel 1
   ```

   Expect all three created, one after another.

Delete the copies afterwards: `uv run celesto sandbox delete <name>` for each.

### M3. Source states (D7, D8)

1. **Stopped source.**

   ```bash
   uv run celesto sandbox stop demo
   uv run celesto sandbox fork demo
   ```

   Expect the copy created and running. Check with `sandbox list` that `demo` is still stopped.

2. **Paused source.**

   ```bash
   uv run celesto sandbox start demo
   uv run celesto sandbox pause demo
   uv run celesto sandbox fork demo
   ```

   Expect: `Sandbox 'demo' is paused. Run 'celesto sandbox resume demo', then fork again.` Run the suggested command and fork again. It should work.

3. **Source that never finished its first start.** Create a sandbox, stop it before it finishes booting, and fork it. Expect the "hasn't finished its first start" message with a `celesto sandbox start` command.

### M4. Refusals (D1b)

For each case, check that the message is one or two plain sentences, names the real sandbox, and gives a command you can copy. Then check with `sandbox list` that nothing was created.

1. **Shared folder.** `uv run celesto sandbox create --name shared --os alpine --mount "$PWD"`, then fork `shared`.
2. **libkrun engine.** On a Mac without QEMU in `PATH` (or with `--backend libkrun`), create a sandbox and fork it. Expect a message suggesting `--backend qemu`.
3. **Older image.** Create a sandbox from a published Ubuntu image (`--os ubuntu`) before the new images are released, and fork it. Expect the message that suggests `celesto image pull --all`.
4. **macOS sandbox** (Mac host only). Fork a macOS sandbox. Expect `macOS sandboxes can't be forked yet.`
5. **Cloud.** `uv run celesto sandbox fork demo --cloud`. Expect the message suggesting `celesto sandbox create --local`.
6. **Missing source.** `uv run celesto sandbox fork does-not-exist`. Expect a "not found" style error, with nothing created.
7. **Bad name.** `uv run celesto sandbox fork demo --name "Bad Name"`. Expect a name error before any waiting or copying.

### M5. Failures part way through (D24)

1. **A copy that starts too slowly.**

   ```bash
   uv run celesto sandbox fork demo --count 2 --boot-timeout 1
   ```

   Expect each failed copy to be listed with the message suggesting `--boot-timeout 2`. Check that failed copies are not in `sandbox list`, and that the exit code is 1:

   ```bash
   echo $?
   ```

2. **Not enough disk space.** On a small disk (for example a loop-mounted 2 GB filesystem used as the Celesto data folder), fork with `--count 10`. Expect the disk space message before anything is copied, with sizes in GB.

3. **Ctrl+C.** Start `uv run celesto sandbox fork demo --count 3` and press Ctrl+C:
   - once during the copy (right after the pause notice on Firecracker),
   - once while the copies are starting.

   Each time, check that `sandbox list` shows no half-made copies, `sandbox snapshot list` shows no leftover `fork-demo-` snapshot, and `demo` is running (not stuck paused). Then fork again and check it works.

4. **Source deleted during a fork.** Start a fork with `--count 3`, and while copies are starting, run `uv run celesto sandbox delete demo` in another terminal. Expect the copies that were created to be kept and reported, and `source_state` to be `null` in `--json` output.

### M6. JSON output for scripts (D24, D25)

```bash
uv run celesto sandbox fork demo --name js --count 2 --json > out.json; echo "exit=$?"
python -m json.tool out.json
```

Check:

- Standard output is valid JSON only. Notices such as `Pausing…` go to standard error.
- `data.children` has one entry per copy, each with `name`, `ok`, `status`, `sandbox`, and `error`.
- `data.source_state` is the source's state (`running` or `stopped`), and `data.warnings` is a list.
- When every copy works, `ok` is `true` and the exit code is 0.
- Repeat with `--boot-timeout 1` to make copies fail. Expect `ok: false`, `error.code: "fork_failed"`, and exit code 1.
- Repeat with a refused fork (for example a paused source). Expect `data: null`, a helpful `error.message`, and exit code 1.

### M7. Python SDK

```python
from celesto import Celesto

with Celesto(os="alpine") as vm:
    child = vm.fork(name="sdk-child")
    print(child.run("cat /etc/machine-id").stdout)

    batch = vm.fork_many(3, name="sdk-many", parallel=2)
    for result in batch.children:
        print(result.name, result.ok, result.error)
    print(batch.warnings, batch.source_state)
```

Check:

- `fork()` returns a running sandbox you can run commands in, with a machine ID different from the source's.
- `fork_many()` returns three results in name order.
- A refused fork (for example on a paused source) raises an error with the same message the CLI prints.
- Run the same with `async_fork` and `async_fork_many` inside `asyncio.run(...)`.

Delete the sandboxes you made afterwards.

### M8. Existing features still work (regression)

Fork touched `stop`, `delete`, snapshots, and the image startup script, so check them quickly on each engine:

1. Create, stop, start, and delete a sandbox that was never forked.
2. Restart a sandbox and check its machine ID and SSH host keys are unchanged (D15: a restart keeps the identity).
3. `uv run celesto sandbox snapshot create demo`, then delete `demo` from another terminal while the snapshot runs. Expect `Waiting for the current snapshot or fork of demo to finish…` and then the delete to finish.
4. Restore a snapshot made before this branch, and check the sandbox starts.

The PR 2 warning ("stayed paused after the snapshot") appears only when resuming the source fails, which can't be triggered by hand. Its isolated test covers it.

## 4. Sign-off

Before merging `feat/sandbox-fork` into `main`, record in the final pull request:

| Check | Linux Firecracker | Linux QEMU | macOS QEMU |
| --- | --- | --- | --- |
| Automated e2e suite (section 2) | | | |
| `e2e` workflow on GitHub | | — | — |
| M1 basic fork | | | |
| M2 copies and names | | | |
| M3 source states | | | |
| M4 refusals | | | |
| M5 failures | | | |
| M6 JSON | | | |
| M7 SDK | | | |
| M8 regression | | | |
| M1 again with published `--os ubuntu` images | | | |

Attach the `fork-artifacts` folder and the saved terminal output.

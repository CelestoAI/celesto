import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import { syncBuiltinESMExports } from "node:module";
import os from "node:os";
import path from "node:path";
import test, { mock } from "node:test";

import { installLinuxCommandShims } from "./fixtures/linux-tools.js";
import type { RemoteComputer } from "../src/operations.js";
import type {
  ComputerExecResponse,
  ComputerExecStreamEvent,
  ExecParams,
} from "../src/computer.js";
import { syncWorkspace, uploadInitialWorkspace } from "../src/workspace.js";

async function fixture() {
  const root = await fs.mkdtemp(
    path.join(os.tmpdir(), "celesto-destination-race-"),
  );
  const local = path.join(root, "local");
  const remote = path.join(root, "remote");
  const bin = path.join(root, "bin");
  await Promise.all([fs.mkdir(local), fs.mkdir(remote), fs.mkdir(bin)]);
  await installLinuxCommandShims(bin);
  class ShellComputer implements RemoteComputer {
    beforeRun?: (command: string) => Promise<void>;
    async run(
      command: string,
      params?: ExecParams,
    ): Promise<ComputerExecResponse> {
      await this.beforeRun?.(command);
      return new Promise((resolve) => {
        const child = execFile(
          "/bin/sh",
          [],
          {
            encoding: "utf8",
            timeout: 10_000,
            maxBuffer: 32 * 1024 * 1024,
            signal: params?.signal,
            env: {
              ...process.env,
              COPYFILE_DISABLE: "1",
              PATH: `${bin}${path.delimiter}${process.env.PATH}`,
            },
          },
          (error, stdout, stderr) =>
            resolve({
              exitCode: error
                ? typeof error.code === "number"
                  ? error.code
                  : 1
                : 0,
              stdout,
              stderr,
            }),
        );
        child.stdin?.end(command);
      });
    }
    async *runStream(
      command: string,
      params?: ExecParams,
    ): AsyncGenerator<ComputerExecStreamEvent> {
      const result = await this.run(command, params);
      if (result.stdout) yield { type: "stdout", data: result.stdout };
      if (result.stderr) yield { type: "stderr", data: result.stderr };
      yield { type: "exit", exitCode: result.exitCode };
    }
  }
  return {
    root,
    local,
    remote,
    computer: new ShellComputer(),
    cleanup: () => fs.rm(root, { recursive: true, force: true }),
  };
}

// Value: protects=sync does not overwrite an independently changed destination;
// fails_when=planned metadata is trusted without a pre-commit comparison;
// why_new=existing late-edit coverage changes upload sources, not destinations; seam=none
// Failure modes: destination bytes/mode change, deletion target changes, and an
// initially absent destination appears after planning, on either filesystem.
test("sync aborts when a destination changes after planning and preserves its baseline", async (t) => {
  const outcomes: object[] = [];
  for (const side of ["local", "remote"] as const)
    for (const mutation of ["content", "mode", "delete", "appeared"] as const)
      await t.test(`${side}: ${mutation}`, async () => {
        const f = await fixture();
        let restoreLstat: (() => void) | undefined;
        try {
          const name = "tracked.txt";
          const localPath = path.join(f.local, name);
          const remotePath = path.join(f.remote, name);
          if (mutation !== "appeared")
            await fs.writeFile(localPath, "baseline", { mode: 0o644 });
          const { revision } = await uploadInitialWorkspace(
            f.computer,
            f.local,
            f.remote,
          );
          const beforeRevision = await fs.readFile(
            path.join(f.remote, ".celesto-sync.json"),
            "utf8",
          );
          const source = side === "local" ? remotePath : localPath;
          const destination = side === "local" ? localPath : remotePath;
          if (mutation === "delete") await fs.rm(source);
          else await fs.writeFile(source, "planned-update");
          let changed = false;
          const changeDestination = async () => {
            changed = true;
            if (mutation === "mode") await fs.chmod(destination, 0o600);
            else
              await fs.writeFile(destination, "independent-change", {
                mode: 0o644,
              });
          };
          if (side === "local") {
            // The real filesystem is changed as application begins, after the
            // scanner's stat/read calls. The production safety check still runs.
            const originalLstat = fs.lstat;
            const stub = mock.method(fs, "lstat", (async (
              ...args: Parameters<typeof fs.lstat>
            ) => {
              if (!changed && String(args[0]) === destination)
                await changeDestination();
              return originalLstat(...args);
            }) as typeof fs.lstat);
            syncBuiltinESMExports();
            restoreLstat = () => {
              stub.mock.restore();
              syncBuiltinESMExports();
            };
          } else {
            // Run the external writer immediately before the guest executes
            // the destructive request, after snapshot capture and upload.
            f.computer.beforeRun = async (command) => {
              if (
                !changed &&
                command.includes(destination) &&
                (mutation === "delete"
                  ? command.includes("rm -f --")
                  : command.includes("base64 -d"))
              )
                await changeDestination();
            };
          }
          await assert.rejects(
            syncWorkspace(f.computer, f.local, f.remote, revision),
            /changed during sync/i,
          );
          assert(
            changed,
            "fixture must reach the planned destination mutation",
          );
          if (mutation === "mode") {
            assert.equal((await fs.stat(destination)).mode & 0o777, 0o600);
            assert.equal(await fs.readFile(destination, "utf8"), "baseline");
          } else
            assert.equal(
              await fs.readFile(destination, "utf8"),
              "independent-change",
            );
          assert.equal(
            await fs.readFile(
              path.join(f.remote, ".celesto-sync.json"),
              "utf8",
            ),
            beforeRevision,
          );
          restoreLstat?.();
          restoreLstat = undefined;
          f.computer.beforeRun = undefined;
          const retry = await syncWorkspace(
            f.computer,
            f.local,
            f.remote,
            revision,
          );
          assert(retry.conflicts.includes(name));
          assert.deepEqual(retry.revision, revision);
          const remoteContents = await fs
            .readFile(remotePath, "utf8")
            .catch((error: NodeJS.ErrnoException) => {
              if (error.code !== "ENOENT") throw error;
              return undefined;
            });
          const artifact = path.join(
            f.local,
            ".celesto-conflicts",
            revision.id,
            `${name}${remoteContents === undefined ? ".remote-deleted" : ".remote"}`,
          );
          assert.equal(
            await fs.readFile(artifact, "utf8"),
            remoteContents ??
              "The file was deleted in the Celesto workspace.\n",
          );
          assert.equal(
            await fs.readFile(
              path.join(f.remote, ".celesto-sync.json"),
              "utf8",
            ),
            beforeRevision,
          );
          outcomes.push({
            side,
            mutation,
            preserved: true,
            baselineUnchanged: true,
            retryConflict: true,
          });
        } finally {
          restoreLstat?.();
          await f.cleanup();
        }
      });
  if (process.env.PI_TEST_ARTIFACT_DIR) {
    await fs.mkdir(process.env.PI_TEST_ARTIFACT_DIR, { recursive: true });
    await fs.writeFile(
      path.join(process.env.PI_TEST_ARTIFACT_DIR, "destination-races.json"),
      JSON.stringify(outcomes, null, 2),
    );
  }
});

// Value: protects=sync never commits through a remote symlink ancestor;
// fails_when=an ancestor changes after snapshot and matching outside bytes pass the destination guard;
// why_new=the content/mode race table does not replace ancestor directories; seam=none
// Failure modes: upload staging or a deletion follows a replaced directory into
// an outside file whose bytes and permissions exactly match the expected file.
test("sync refuses a remote ancestor symlink even when outside bytes match the snapshot", async (t) => {
  for (const deleting of [false, true])
    await t.test(deleting ? "delete" : "replace", async () => {
      const f = await fixture();
      try {
        const folder = "folder\n";
        const name = `${folder}/tracked.txt`;
        await fs.mkdir(path.join(f.local, folder));
        await fs.writeFile(path.join(f.local, name), "baseline", {
          mode: 0o644,
        });
        const { revision } = await uploadInitialWorkspace(
          f.computer,
          f.local,
          f.remote,
        );
        const beforeRevision = await fs.readFile(
          path.join(f.remote, ".celesto-sync.json"),
          "utf8",
        );
        if (deleting) await fs.rm(path.join(f.local, name));
        else await fs.writeFile(path.join(f.local, name), "planned-update");
        const outside = path.join(f.root, "outside");
        await fs.mkdir(outside);
        await fs.writeFile(path.join(outside, "tracked.txt"), "baseline", {
          mode: 0o644,
        });
        let changed = false;
        f.computer.beforeRun = async (command) => {
          if (
            !changed &&
            command.includes(path.join(f.remote, name)) &&
            (deleting ? command.includes("rm -f") : command.includes(": >"))
          ) {
            changed = true;
            await fs.rename(
              path.join(f.remote, folder),
              path.join(f.root, "parked"),
            );
            await fs.symlink(outside, path.join(f.remote, folder));
          }
        };
        await assert.rejects(
          syncWorkspace(f.computer, f.local, f.remote, revision),
          /changed during sync/i,
        );
        assert(changed);
        assert.equal(
          await fs.readFile(path.join(outside, "tracked.txt"), "utf8"),
          "baseline",
        );
        assert.equal(
          await fs.readFile(path.join(f.root, "parked", "tracked.txt"), "utf8"),
          "baseline",
        );
        assert.equal(
          await fs.readFile(path.join(f.remote, ".celesto-sync.json"), "utf8"),
          beforeRevision,
        );
      } finally {
        await f.cleanup();
      }
    });
});

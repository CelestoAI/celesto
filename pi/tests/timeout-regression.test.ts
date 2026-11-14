import assert from "node:assert/strict";
import { execFile as execFileCallback, spawn } from "node:child_process";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { promisify } from "node:util";

import type { ExecParams, ComputerExecStreamEvent } from "../src/computer.js";
import {
  createCelestoBashOperations,
  shellQuote,
  type RemoteComputer,
} from "../src/operations.js";

const execute = promisify(execFileCallback);
const wait = (milliseconds: number) =>
  new Promise((resolve) => setTimeout(resolve, milliseconds));

// Protects actual termination after a buffered timeout event. The old mock only
// proved a cleanup command was requested; it could not detect an orphaned setsid
// process or a command that fails to kill TERM-resistant descendants. No production
// seam is needed: exercise the public BashOperations contract with real shells.
// Failure modes: timeout ignores cleanup; cleanup targets only the wrapper;
// detached descendants ignore TERM; cleanup returns before the group is stopped.
test(
  "Cloud timeout stops the real detached Linux process group",
  {
    skip:
      process.platform !== "linux" && process.env.PI_TEST_LINUX_DOCKER !== "1"
        ? "Linux process groups require Ubuntu CI or PI_TEST_LINUX_DOCKER=1"
        : false,
    timeout: 20_000,
  },
  async () => {
    const fixtureParent =
      process.platform === "linux"
        ? os.tmpdir()
        : path.join(os.homedir(), ".cache");
    await mkdir(fixtureParent, { recursive: true });
    const root = await mkdtemp(
      path.join(fixtureParent, "celesto-timeout-process-"),
    );
    const childFile = path.join(root, "child.pid");
    const wrapperFile = path.join(root, "wrapper.pid");
    const heartbeat = path.join(root, "heartbeat");
    let container: string | undefined;
    let childId: number | undefined;
    let wrapperId: number | undefined;
    const shell = (command: string) =>
      execute(
        container ? "docker" : "/bin/bash",
        container
          ? [
              "exec",
              container,
              "/bin/bash",
              "--noprofile",
              "--norc",
              "-c",
              command,
            ]
          : ["--noprofile", "--norc", "-c", command],
        { timeout: 5_000 },
      );
    try {
      if (process.platform !== "linux") {
        const started = await execute(
          "docker",
          [
            "run",
            "--rm",
            "-d",
            "--mount",
            `type=bind,source=${root},target=${root}`,
            "ubuntu:24.04",
            "sleep",
            "120",
          ],
          { timeout: 10_000 },
        );
        container = started.stdout.trim();
      }
      const computer: RemoteComputer = {
        async run(command) {
          try {
            return { exitCode: 0, ...(await shell(command)) };
          } catch (error) {
            const failure = error as {
              code?: number;
              stdout?: string;
              stderr?: string;
            };
            return {
              exitCode: failure.code ?? 1,
              stdout: failure.stdout ?? "",
              stderr: failure.stderr ?? "",
            };
          }
        },
        async *runStream(
          command: string,
          _params?: ExecParams,
        ): AsyncGenerator<ComputerExecStreamEvent> {
          const outer = `printf '%s' "$$" > ${shellQuote(wrapperFile)}; exec bash --noprofile --norc -c ${shellQuote(command)}`;
          const child = spawn(
            container ? "docker" : "/bin/bash",
            container
              ? ["exec", container, "/bin/bash", "-c", outer]
              : ["-c", outer],
            { stdio: "ignore" },
          );
          const exited = new Promise<void>((resolve) =>
            child.once("exit", () => resolve()),
          );
          const deadline = Date.now() + 3_000;
          while (true) {
            try {
              childId = Number(await readFile(childFile, "utf8"));
              wrapperId = Number(await readFile(wrapperFile, "utf8"));
              if ((await readFile(heartbeat)).length > 0) break;
            } catch {
              /* Wait for this test's child to start. */
            }
            if (Date.now() > deadline)
              throw new Error("Fixture command failed to start");
            await wait(10);
          }
          assert(Number.isSafeInteger(childId) && childId! > 1);
          assert(Number.isSafeInteger(wrapperId) && wrapperId! > 1);
          // Cloud can time out its wrapper while the setsid group continues. Return
          // that completed response; the production operations must stop the group.
          await shell(`kill -KILL ${wrapperId}`);
          await exited;
          yield { type: "exit", exitCode: 124, timedOut: true };
        },
      };
      const result = await createCelestoBashOperations(
        computer,
        root,
        root,
      ).exec(
        `exec >/dev/null 2>&1; printf '%s' "$$" > ${shellQuote(childFile)}; trap '' TERM; while :; do printf x >> ${shellQuote(heartbeat)}; sleep 0.02; done`,
        root,
        { onData() {}, timeout: 1 },
      );
      const before = (await readFile(heartbeat)).length;
      await wait(150);
      const after = (await readFile(heartbeat)).length;
      const live = await shell(
        `ps -eo pgid=,stat= | awk '$1 == ${childId} && $2 !~ /^Z/ { print }'`,
      );
      if (process.env.PI_TEST_ARTIFACT_DIR) {
        await mkdir(process.env.PI_TEST_ARTIFACT_DIR, { recursive: true });
        await writeFile(
          path.join(process.env.PI_TEST_ARTIFACT_DIR, "timeout-cleanup.json"),
          JSON.stringify(
            {
              exitCode: result.exitCode,
              heartbeatBefore: before,
              heartbeatAfter: after,
              liveGroupProcesses: live.stdout.trim(),
              linux: true,
            },
            null,
            2,
          ),
        );
      }
      assert.equal(result.exitCode, 124);
      assert.equal(
        after,
        before,
        "timed-out process kept writing after BashOperations returned",
      );
      assert.equal(
        live.stdout.trim(),
        "",
        "timed-out process group still has running members",
      );
    } finally {
      if (childId && Number.isSafeInteger(childId))
        await shell(`kill -KILL -- -${childId} 2>/dev/null || true`).catch(
          () => {},
        );
      if (wrapperId && Number.isSafeInteger(wrapperId))
        await shell(`kill -KILL ${wrapperId} 2>/dev/null || true`).catch(
          () => {},
        );
      if (container)
        await execute("docker", ["rm", "-f", container]).catch(() => {});
      await rm(root, { recursive: true, force: true });
    }
  },
);

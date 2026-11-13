import assert from "node:assert/strict";
import { execFile as execFileCallback } from "node:child_process";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import type {
  ComputerExecResponse,
  ComputerExecStreamEvent,
  ExecParams,
} from "../src/computer.js";

import {
  createCelestoBashOperations,
  createCelestoReadOperations,
  createCelestoWriteOperations,
  prepareRemoteWorkspace,
  shellQuote,
  toRemotePath,
  writeRemoteFile,
  type RemoteComputer,
} from "../src/operations.js";

const REMOTE_ROOT = "/home/celesto/workspace";

class FakeComputer implements RemoteComputer {
  commands: string[] = [];
  responses: ComputerExecResponse[] = [];
  events: ComputerExecStreamEvent[] = [];
  streamParams: ExecParams | undefined;

  async run(command: string): Promise<ComputerExecResponse> {
    this.commands.push(command);
    return (
      this.responses.shift() ?? {
        exitCode: 0,
        stdout: "",
        stderr: "",
      }
    );
  }

  async *runStream(
    command: string,
    params?: ExecParams,
  ): AsyncGenerator<ComputerExecStreamEvent> {
    this.commands.push(command);
    this.streamParams = params;
    for (const event of this.events) yield event;
  }
}

test("shellQuote protects single quotes", () => {
  assert.equal(shellQuote("it's safe"), `'it'"'"'s safe'`);
});

test("toRemotePath maps project paths and rejects escapes", () => {
  assert.equal(
    toRemotePath("/project/src/main.ts", "/project", REMOTE_ROOT),
    `${REMOTE_ROOT}/src/main.ts`,
  );
  assert.equal(
    toRemotePath(`${REMOTE_ROOT}/src/main.ts`, "/project", REMOTE_ROOT),
    `${REMOTE_ROOT}/src/main.ts`,
  );
  assert.throws(
    () => toRemotePath("/project/../secret", "/project", REMOTE_ROOT),
    /must stay inside/,
  );
  assert.throws(
    () => toRemotePath(`${REMOTE_ROOT}/../secret`, "/project", REMOTE_ROOT),
    /must stay inside/,
  );
});

test("prepareRemoteWorkspace creates the home workspace and migrates files", async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), "celesto-home-workspace-"));
  const home = path.join(root, "home");
  const legacy = path.join(root, "legacy");
  await mkdir(home);
  await mkdir(legacy);
  await writeFile(path.join(legacy, "legacy.txt"), "preserved");

  class LocalShellComputer extends FakeComputer {
    override async run(command: string): Promise<ComputerExecResponse> {
      this.commands.push(command);
      return new Promise((resolve, reject) => {
        const child = execFileCallback(
          "/bin/sh",
          [],
          {
            encoding: "utf8",
            timeout: 10_000,
            env: { ...process.env, HOME: home },
          },
          (error, stdout, stderr) =>
            error ? reject(error) : resolve({ exitCode: 0, stdout, stderr }),
        );
        child.stdin?.end(command);
      });
    }
  }

  try {
    const remoteRoot = await prepareRemoteWorkspace(new LocalShellComputer(), {
      legacyRoot: legacy,
    });
    assert.equal(path.basename(remoteRoot), "workspace");
    assert.equal(
      await readFile(path.join(remoteRoot, "legacy.txt"), "utf8"),
      "preserved",
    );
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

test("read and write operations transfer file contents as base64", async () => {
  const computer = new FakeComputer();
  computer.responses.push({
    exitCode: 0,
    stdout: Buffer.from("hello").toString("base64"),
    stderr: "",
  });

  const read = createCelestoReadOperations(computer, "/project", REMOTE_ROOT);
  assert.equal((await read.readFile("/project/a.txt")).toString(), "hello");
  assert.ok((computer.commands[0] ?? "").includes(`${REMOTE_ROOT}/a.txt`));

  const write = createCelestoWriteOperations(computer, "/project", REMOTE_ROOT);
  await write.writeFile("/project/a.txt", "updated");
  const commands = computer.commands.slice(1).join("\n");
  assert.match(commands, /mkdir -p/);
  assert.ok(commands.includes(Buffer.from("updated").toString("base64")));
  assert.match(commands, /base64 -d/);
  assert.match(commands, /mv/);
});

test("writeRemoteFile sends large payloads in bounded chunks", async () => {
  const computer = new FakeComputer();
  const content = Buffer.alloc(200_000, 0xab);
  const encoded = content.toString("base64");

  await writeRemoteFile(computer, `${REMOTE_ROOT}/large.bin`, content);

  const appendCommands = computer.commands.filter((command) =>
    command.includes("printf %s"),
  );
  assert(appendCommands.length > 1);
  const uploaded = appendCommands
    .map((command) => command.match(/printf %s '([^']*)'/)?.[1] ?? "")
    .join("");
  assert.equal(uploaded, encoded);
  assert.ok(appendCommands.every((command) => command.length <= 10_000));
});

test("bash operations stream stdout and stderr and pass the abort signal", async () => {
  const computer = new FakeComputer();
  computer.events = [
    { type: "stdout", data: "one" },
    { type: "stderr", data: "two" },
    { type: "exit", exitCode: 7 },
  ];
  const output: string[] = [];
  const controller = new AbortController();

  const result = await createCelestoBashOperations(
    computer,
    "/project",
    REMOTE_ROOT,
  ).exec("echo test", "/project/src", {
    onData: (data) => output.push(data.toString()),
    signal: controller.signal,
    timeout: 900,
  });

  assert.deepEqual(output, ["one", "two"]);
  assert.deepEqual(result, { exitCode: 7 });
  assert.equal(computer.streamParams?.signal, controller.signal);
  assert.equal(computer.streamParams?.timeout, 300);
  assert.match(
    computer.commands[0] ?? "",
    /^cd '\/home\/celesto\/workspace\/src' && \{ env CELESTO_PI_COMMAND_ID='[^']+' setsid bash --noprofile --norc -c 'echo test'/,
  );
});

test("aborting bash explicitly terminates the remote process group", async () => {
  class AbortableComputer extends FakeComputer {
    override async *runStream(
      command: string,
      params?: ExecParams,
    ): AsyncGenerator<ComputerExecStreamEvent> {
      this.commands.push(command);
      this.streamParams = params;
      await new Promise<never>((_resolve, reject) => {
        params?.signal?.addEventListener(
          "abort",
          () => reject(new DOMException("aborted", "AbortError")),
          { once: true },
        );
      });
    }
  }

  const computer = new AbortableComputer();
  const controller = new AbortController();
  const execution = createCelestoBashOperations(
    computer,
    "/project",
    REMOTE_ROOT,
  ).exec("sleep 30", "/project", {
    onData: () => {},
    signal: controller.signal,
    timeout: 60,
  });
  setTimeout(() => controller.abort(), 10);

  await assert.rejects(execution, /aborted/);
  assert.match(
    computer.commands[0] ?? "",
    /setsid bash --noprofile --norc -c 'sleep 30'/,
  );
  assert.match(computer.commands[1] ?? "", /kill -TERM/);
  assert.match(computer.commands[1] ?? "", /pgid=/);
});

test("fractional Bash timeouts are rounded into Cloud's bounded integer format", async () => {
  for (const [timeout, expected] of [
    [undefined, undefined],
    [0.5, 1],
    [1.5, 2],
    [299.2, 300],
    [301, 300],
  ]) {
    const computer = new FakeComputer();
    computer.events = [{ type: "exit", exitCode: 0 }];
    await createCelestoBashOperations(computer, "/project", REMOTE_ROOT).exec(
      "true",
      "/project",
      { onData() {}, timeout },
    );
    assert.equal(computer.streamParams?.timeout, expected);
  }
});

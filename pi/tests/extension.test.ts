import assert from "node:assert/strict";
import { mkdtemp, rm, symlink, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import type {
  ExtensionAPI,
  ExtensionContext,
  ExtensionToolContext,
  SessionStartEvent,
  ToolDefinition,
} from "@earendil-works/pi-coding-agent";
import {
  Computer,
  type ComputerExecResponse,
  type ComputerExecStreamEvent,
  type ExecParams,
} from "../src/computer.js";

import celestoPiExtension, { assertSafeLocalRoot } from "../src/index.js";

const REMOTE_ROOT = "/home/celesto/workspace";

class FakeComputer {
  readonly id = "computer-1";
  readonly name = "archimedes";
  readonly status = "running";
  readonly commands: string[] = [];

  async run(command: string): Promise<ComputerExecResponse> {
    this.commands.push(command);
    return {
      exitCode: 0,
      stdout: command.includes('home=$(cd "${HOME:?HOME is not set}"')
        ? `${REMOTE_ROOT}\n`
        : "",
      stderr: "",
    };
  }

  async *runStream(
    _command: string,
    _params?: ExecParams,
  ): AsyncGenerator<ComputerExecStreamEvent> {
    yield { type: "exit", exitCode: 0 };
  }
}

test("push refuses filesystem and home directory roots", () => {
  assert.throws(
    () => assertSafeLocalRoot(path.parse(process.cwd()).root),
    /Refusing to copy/,
  );
  assert.throws(() => assertSafeLocalRoot(os.homedir()), /Refusing to copy/);
  assert.doesNotThrow(() =>
    assertSafeLocalRoot(path.join(os.tmpdir(), "celesto-project")),
  );
});

test("/celesto push uploads once, persists its revision, and reports skipped files", async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), "celesto-push-test-"));
  const originalGet = Computer.get;
  try {
    await writeFile(path.join(root, "hello.txt"), "hello\n");
    await symlink("hello.txt", path.join(root, "hello-link.txt"));

    const computer = new FakeComputer();
    Computer.get = async () => computer as unknown as Computer;

    const flags = new Map<string, boolean | string | undefined>();
    const commands = new Map<
      string,
      (args: string, ctx: ExtensionContext) => Promise<void>
    >();
    const persisted: unknown[] = [];
    const notifications: string[] = [];
    const handlers = new Map<
      string,
      Array<(event: unknown, ctx: ExtensionContext) => unknown>
    >();
    const api = {
      registerFlag(name: string, options: { default?: boolean | string }) {
        flags.set(name, options.default);
      },
      getFlag(name: string) {
        return flags.get(name);
      },
      registerTool() {},
      registerCommand(
        name: string,
        options: {
          handler: (args: string, ctx: ExtensionContext) => Promise<void>;
        },
      ) {
        commands.set(name, options.handler);
      },
      on(
        event: string,
        handler: (event: unknown, ctx: ExtensionContext) => unknown,
      ) {
        const existing = handlers.get(event) ?? [];
        existing.push(handler);
        handlers.set(event, existing);
      },
      appendEntry(_customType: string, data: unknown) {
        persisted.push(data);
      },
    } as unknown as ExtensionAPI;

    celestoPiExtension(api);
    flags.set("celesto-computer", computer.name);
    const context = {
      cwd: root,
      sessionManager: { getBranch: () => [] },
      ui: {
        theme: { fg: (_color: string, value: string) => value },
        setStatus() {},
        notify(message: string) {
          notifications.push(message);
        },
      },
    } as unknown as ExtensionContext;
    for (const handler of handlers.get("session_start") ?? []) {
      await handler(
        {
          type: "session_start",
          reason: "startup",
        } satisfies SessionStartEvent,
        context,
      );
    }

    const push = commands.get("celesto");
    assert(push);
    await push("push", context);

    assert(
      computer.commands.some((command) =>
        command.includes(`mv '${REMOTE_ROOT}.celesto-staging-`),
      ),
    );
    const saved = persisted.at(-1) as { revision?: { files?: object } };
    assert(saved.revision?.files && "hello.txt" in saved.revision.files);
    assert(
      notifications.some((message) =>
        message.includes('Copied this project to "archimedes". Skipped 1'),
      ),
    );

    const commandCount = computer.commands.length;
    await push("push", context);
    assert.equal(computer.commands.length, commandCount);
    assert(
      notifications.some((message) =>
        message.includes("already has a shared revision"),
      ),
    );
  } finally {
    Computer.get = originalGet;
    await rm(root, { recursive: true, force: true });
  }
});

// Value: protects=remote cwd replaces the session cwd while preserving instruction examples;
// fails_when=an earlier example cwd block is replaced instead; why_new=previous inputs contained only one cwd block; seam=none
test("remote prompts replace the session cwd and preserve instruction examples", async () => {
  const originalCreate = Computer.create;
  try {
    const computer = new FakeComputer();
    Computer.create = async () => {
      return computer as unknown as Computer;
    };

    const flags = new Map<string, boolean | string | undefined>();
    const handlers = new Map<
      string,
      Array<(event: unknown, ctx: ExtensionContext) => unknown>
    >();
    const api = {
      registerFlag(name: string, options: { default?: boolean | string }) {
        flags.set(name, options.default);
      },
      getFlag(name: string) {
        return flags.get(name);
      },
      registerTool() {},
      registerCommand() {},
      on(
        event: string,
        handler: (event: unknown, ctx: ExtensionContext) => unknown,
      ) {
        const existing = handlers.get(event) ?? [];
        existing.push(handler);
        handlers.set(event, existing);
      },
      appendEntry() {},
    } as unknown as ExtensionAPI;

    celestoPiExtension(api);
    flags.set("celesto", true);
    const context = {
      cwd: process.cwd(),
      sessionManager: { getBranch: () => [] },
      ui: {
        theme: { fg: (_color: string, value: string) => value },
        setStatus() {},
        notify() {},
      },
    } as unknown as ExtensionContext;

    for (const handler of handlers.get("session_start") ?? []) {
      await handler(
        {
          type: "session_start",
          reason: "startup",
        } satisfies SessionStartEvent,
        context,
      );
    }

    const promptHandler = handlers.get("before_agent_start")?.[0];
    assert(promptHandler);
    for (const instructionsBefore of [
      "Instructions before <cwd>/example/path</cwd>",
      "Instructions before mention `<cwd>` without a closing tag",
    ]) {
      for (const cwdSection of [
        `<cwd>${context.cwd}</cwd>`,
        `<cwd>\n${context.cwd}\n</cwd>`,
        `Current working directory: ${context.cwd}`,
        "Custom prompt without a cwd section",
      ]) {
        const prompt = `${instructionsBefore}\n${cwdSection}\nInstructions after`;
        const result = (await promptHandler(
          { systemPrompt: prompt },
          context,
        )) as { systemPrompt: string };
        assert(!result.systemPrompt.includes(context.cwd), result.systemPrompt);
        assert.equal(
          result.systemPrompt.split(REMOTE_ROOT).length - 1,
          1,
          result.systemPrompt,
        );
        assert(result.systemPrompt.includes(instructionsBefore));
        assert(result.systemPrompt.includes("Instructions after"));
        if (cwdSection.startsWith("<cwd>")) {
          assert(result.systemPrompt.includes(`<cwd>${REMOTE_ROOT}</cwd>`));
          assert(!result.systemPrompt.includes("Current working directory:"));
        }
      }
    }
  } finally {
    Computer.create = originalCreate;
  }
});

test("local tools use the session cwd without --celesto", async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), "celesto-extension-test-"));
  try {
    await writeFile(path.join(root, "hello.txt"), "hello from local\n");

    const flags = new Map<string, boolean | string | undefined>();
    const tools = new Map<string, ToolDefinition>();
    const handlers = new Map<
      string,
      Array<(event: unknown, ctx: ExtensionContext) => unknown>
    >();
    const commands = new Set<string>();
    const api = {
      registerFlag(name: string, options: { default?: boolean | string }) {
        flags.set(name, options.default);
      },
      getFlag(name: string) {
        return flags.get(name);
      },
      registerTool(tool: ToolDefinition) {
        tools.set(tool.name, tool);
      },
      registerCommand(name: string) {
        commands.add(name);
      },
      on(
        event: string,
        handler: (event: unknown, ctx: ExtensionContext) => unknown,
      ) {
        const existing = handlers.get(event) ?? [];
        existing.push(handler);
        handlers.set(event, existing);
      },
      appendEntry() {},
    } as unknown as ExtensionAPI;

    celestoPiExtension(api);
    const context = {
      cwd: root,
      sessionManager: { getBranch: () => [] },
      ui: {
        theme: { fg: (_color: string, value: string) => value },
        setStatus() {},
        notify() {},
      },
    } as unknown as ExtensionToolContext;
    for (const handler of handlers.get("session_start") ?? []) {
      await handler(
        {
          type: "session_start",
          reason: "startup",
        } satisfies SessionStartEvent,
        context,
      );
    }

    const promptHandler = handlers.get("before_agent_start")?.[0];
    assert(promptHandler);
    assert.equal(
      await promptHandler({ systemPrompt: "Local session prompt" }, context),
      undefined,
    );
    assert(flags.has("celesto"));
    assert(flags.has("celesto-computer"));
    assert(commands.has("celesto"));
    assert.deepEqual([...tools.keys()].sort(), [
      "bash",
      "edit",
      "read",
      "write",
    ]);

    const result = await tools
      .get("read")
      ?.execute("call-1", { path: "hello.txt" }, undefined, undefined, context);
    assert.equal(result?.content[0]?.type, "text");
    assert.match(
      result?.content[0]?.type === "text" ? result.content[0].text : "",
      /hello from local/,
    );
  } finally {
    await rm(root, { recursive: true, force: true });
  }
});

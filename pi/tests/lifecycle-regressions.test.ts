import assert from "node:assert/strict";
import { cp, mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { setImmediate } from "node:timers/promises";
import {
  SessionManager,
  type ExtensionAPI,
  type ExtensionToolContext,
  type ToolDefinition,
  type SessionStartEvent,
  type SessionShutdownEvent,
} from "@earendil-works/pi-coding-agent";
import {
  Computer,
  type ComputerExecResponse,
  type ComputerExecStreamEvent,
  type ExecParams,
} from "../src/computer.js";
import celestoPiExtension from "../src/index.js";

async function fixture() {
  const root = await mkdtemp(path.join(os.tmpdir(), "celesto-lifecycle-"));
  const project = path.join(root, "project");
  const sessions = path.join(root, "sessions");
  await mkdir(project);
  await writeFile(path.join(project, "file.txt"), "old");
  const originalCreate = Computer.create;
  const originalGet = Computer.get;
  const resources = new Map<string, FakeComputer>();
  let creations = 0;
  let release!: () => void;
  let ready!: () => void;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  const started = new Promise<void>((resolve) => {
    ready = resolve;
  });
  let active = false;
  let overlap = false;
  const commands: string[] = [];
  class FakeComputer {
    status = "running";
    readonly name: string;
    constructor(readonly id: string) {
      this.name = id;
    }
    async run(command: string): Promise<ComputerExecResponse> {
      commands.push(command);
      if (active) overlap = true;
      return {
        exitCode: 0,
        stdout: command.includes("home=$(cd")
          ? `${root}/workspace\n`
          : command.startsWith("base64 <")
            ? Buffer.from("old").toString("base64")
            : "",
        stderr: "",
      };
    }
    async *runStream(
      command: string,
      _params?: ExecParams,
    ): AsyncGenerator<ComputerExecStreamEvent> {
      commands.push(command);
      if (command.includes("held-tool")) {
        active = true;
        ready();
        await held;
        active = false;
      } else if (active) overlap = true;
      yield { type: "exit", exitCode: 0 };
    }
    async delete() {
      resources.delete(this.id);
    }
    async start() {}
    async refresh() {}
  }
  Computer.create = async () => {
    const c = new FakeComputer(`cmp_fixture_${++creations}`);
    resources.set(c.id, c);
    return c as unknown as Computer;
  };
  Computer.get = async (id) => {
    const c = resources.get(id);
    if (!c) throw new Error("Missing fixture resource");
    return c as unknown as Computer;
  };
  function manager() {
    const session = SessionManager.create(project, sessions);
    session.appendMessage({
      role: "user",
      content: "Fixture",
      timestamp: Date.now(),
    });
    return session;
  }
  function harness(session: SessionManager, selected?: string) {
    const flags = new Map<string, unknown>();
    const handlers = new Map<string, (event: any, ctx: any) => any>();
    const tools = new Map<string, ToolDefinition>();
    const errors: string[] = [];
    let command!: (args: string, ctx: any) => Promise<void>;
    celestoPiExtension({
      registerFlag(name: string, opts: { default?: unknown }) {
        flags.set(name, opts.default);
      },
      getFlag(name: string) {
        return flags.get(name);
      },
      registerTool(tool: ToolDefinition) {
        tools.set(tool.name, tool);
      },
      registerCommand(_name: string, opts: { handler: typeof command }) {
        command = opts.handler;
      },
      on(name: string, handler: (event: any, ctx: any) => any) {
        handlers.set(name, handler);
      },
      appendEntry(type: string, data: unknown) {
        session.appendCustomEntry(type, data);
      },
    } as unknown as ExtensionAPI);
    flags.set("celesto", true);
    if (selected) flags.set("celesto-computer", selected);
    const ctx = {
      cwd: project,
      sessionManager: session,
      ui: {
        setStatus() {},
        theme: { fg: (_c: string, s: string) => s },
        notify(message: string, level: string) {
          if (level === "error") errors.push(message);
        },
      },
    } as unknown as ExtensionToolContext;
    return {
      tools,
      errors,
      ctx,
      start: (reason: SessionStartEvent["reason"]) =>
        handlers.get("session_start")!({ type: "session_start", reason }, ctx),
      shutdown: (
        reason: SessionShutdownEvent["reason"],
        targetSessionFile?: string,
      ) =>
        handlers.get("session_shutdown")!(
          { type: "session_shutdown", reason, targetSessionFile },
          ctx,
        ),
      emit: (name: string, event: unknown) => handlers.get(name)?.(event, ctx),
      command: (args: string) => command(args, ctx),
      async bash(value: string, signal?: AbortSignal) {
        return tools
          .get("bash")!
          .execute("call", { command: value }, signal, undefined, ctx);
      },
      async userBash(value: string) {
        const result = await handlers.get("user_bash")!(
          { type: "user_bash", command: value },
          ctx,
        );
        return result.operations.exec(value, project, { onData() {} });
      },
    };
  }
  const latestState = (session: SessionManager) => {
    const entry = session
      .getBranch()
      .filter((e) => e.type === "custom" && e.customType === "celesto-pi-state")
      .at(-1);
    return (
      entry as
        | { data?: { computerId?: string; keep?: boolean; revision?: unknown } }
        | undefined
    )?.data;
  };
  return {
    root,
    project,
    sessions,
    resources,
    manager,
    harness,
    latestState,
    commands,
    started,
    release,
    overlaps: () => overlap,
    creations: () => creations,
    async cleanup() {
      release();
      Computer.create = originalCreate;
      Computer.get = originalGet;
      try {
        if (process.env.PI_TEST_ARTIFACT_DIR) {
          const evidence = path.join(
            process.env.PI_TEST_ARTIFACT_DIR,
            path.basename(root),
          );
          await mkdir(evidence, { recursive: true });
          await cp(sessions, path.join(evidence, "sessions"), {
            recursive: true,
          });
          await writeFile(
            path.join(evidence, "resources.json"),
            JSON.stringify(
              { creations, remaining: [...resources.keys()], overlap },
              null,
              2,
            ),
          );
        }
      } finally {
        await rm(root, { recursive: true, force: true });
      }
    },
  };
}

test("tree navigation preserves live keep/revision metadata before reload", async () => {
  const f = await fixture();
  try {
    const manager = f.manager();
    const live = f.harness(manager);
    await live.start("startup");
    const before = manager.getLeafId()!;
    const id = f.latestState(manager)!.computerId!;
    await live.command("push");
    await live.command("keep");
    assert.deepEqual(live.errors, []);
    manager.branch(before);
    assert.equal(f.latestState(manager)!.keep, false);
    await live.emit("session_tree", {
      type: "session_tree",
      oldLeafId: null,
      newLeafId: before,
    });
    assert.equal(f.latestState(manager)!.keep, true);
    assert(f.latestState(manager)!.revision);
    await live.shutdown("reload");
    const reloaded = f.harness(manager);
    await reloaded.start("reload");
    await reloaded.shutdown("quit");
    assert.equal(f.creations(), 1);
    assert(f.resources.has(id));
  } finally {
    await f.cleanup();
  }
});

test("session replacement retains resumable computers; quit cleans them", async (t) => {
  for (const reason of ["new", "resume", "fork"] as const)
    await t.test(reason, async () => {
      const f = await fixture();
      try {
        const manager = f.manager();
        const live = f.harness(manager);
        await live.start("startup");
        const id = f.latestState(manager)!.computerId!;
        await live.shutdown(reason);
        assert(f.resources.has(id));
        const restored = f.harness(manager);
        await restored.start("resume");
        assert.equal(f.creations(), 1);
        await restored.shutdown("quit");
        assert(!f.resources.has(id));
      } finally {
        await f.cleanup();
      }
    });
});

test("an explicitly selected fork never inherits its parent's deletion right", async () => {
  const f = await fixture();
  try {
    const parent = f.manager();
    const live = f.harness(parent);
    await live.start("startup");
    const forkPoint = parent.getLeafId()!;
    const id = f.latestState(parent)!.computerId!;
    await live.command("keep");
    const child = SessionManager.open(parent.getSessionFile()!, f.sessions);
    const childFile = child.createBranchedSession(forkPoint)!;
    await live.shutdown("fork", childFile);
    const fork = f.harness(child, id);
    await fork.start("fork");
    await fork.shutdown("quit");
    assert.equal(f.creations(), 1);
    assert(f.resources.has(id));
  } finally {
    await f.cleanup();
  }
});

test("sync and all foreground remote mutations share one execution queue", async (t) => {
  for (const heldBy of ["bash", "user_bash"])
    await t.test(heldBy, async () => {
      const f = await fixture();
      try {
        const h = f.harness(f.manager());
        await h.start("startup");
        await h.command("push");
        const held =
          heldBy === "bash" ? h.bash("held-tool") : h.userBash("held-tool");
        await f.started;
        const jobs = [
          h.command("sync"),
          h.tools
            .get("write")!
            .execute(
              "write",
              { path: "file.txt", content: "new" },
              undefined,
              undefined,
              h.ctx,
            ),
          h.tools
            .get("edit")!
            .execute(
              "edit",
              { path: "file.txt", edits: [{ oldText: "old", newText: "new" }] },
              undefined,
              undefined,
              h.ctx,
            ),
          h.bash("true"),
          h.userBash("true"),
        ];
        await setImmediate();
        const overlapped = f.overlaps();
        f.release();
        await held;
        await Promise.all(jobs);
        assert.equal(overlapped, false);
        assert.equal(f.overlaps(), false);
        assert.deepEqual(h.errors, []);
      } finally {
        await f.cleanup();
      }
    });
});

test("an aborted queued mutation never reaches the remote computer", async () => {
  const f = await fixture();
  try {
    const h = f.harness(f.manager());
    await h.start("startup");
    const held = h.bash("held-tool");
    await f.started;
    const abort = new AbortController();
    const observed = h.tools
      .get("write")!
      .execute(
        "cancel",
        { path: "cancelled.txt", content: "new" },
        abort.signal,
        undefined,
        h.ctx,
      )
      .then(
        () => undefined,
        (error: Error) => error,
      );
    abort.abort();
    await setImmediate();
    f.release();
    await held;
    const error = await observed;
    assert(error instanceof Error);
    assert.match(error.message, /aborted/i);
    assert(!f.commands.some((c) => c.includes("cancelled.txt")));
  } finally {
    await f.cleanup();
  }
});

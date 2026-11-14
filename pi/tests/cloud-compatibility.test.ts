import assert from "node:assert/strict";
import { randomBytes } from "node:crypto";
import { execFile } from "node:child_process";
import { once } from "node:events";
import {
  mkdir,
  mkdtemp,
  readFile,
  readdir,
  rm,
  symlink,
  writeFile,
} from "node:fs/promises";
import { createServer } from "node:http";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { promisify } from "node:util";
import type {
  ExtensionAPI,
  ExtensionContext,
  ExtensionCommandContext,
  ExtensionToolContext,
  ToolDefinition,
} from "@earendil-works/pi-coding-agent";
import { discoverAndLoadExtensions } from "@earendil-works/pi-coding-agent";
import celestoPiExtension from "../src/index.js";
import { installLinuxCommandShims } from "./fixtures/linux-tools.js";

const execute = promisify(execFile);

test(
  "Pi Cloud commands, transfers, sync containment and ownership work end to end",
  { timeout: 30_000 },
  async (t) => {
    const root = await mkdtemp(path.join(os.tmpdir(), "celesto-cloud-http-"));
    const localRoot = path.join(root, "project");
    const remoteRoot = path.join(root, "remote", "workspace");
    const bin = path.join(root, "bin");
    await Promise.all([
      mkdir(localRoot),
      mkdir(remoteRoot, { recursive: true }),
      mkdir(bin),
    ]);
    await writeFile(path.join(localRoot, "hello.txt"), "hello from Pi\n");
    const largeContents = randomBytes(24_000).toString("hex");
    await writeFile(path.join(localRoot, "large.txt"), largeContents);
    await installLinuxCommandShims(bin);
    const calls: Array<{ method?: string; url?: string }> = [];
    const keys: string[] = [];
    const allocated = new Set(["cmp_existing"]);
    let failPreparation = false;
    let failGet = false;
    let existingStopped = true;
    const info = (id: string) => ({
      id,
      name: id,
      status: id === "cmp_existing" && existingStopped ? "stopped" : "running",
    });
    const server = createServer(async (request, response) => {
      calls.push({ method: request.method, url: request.url });
      const chunks = [];
      for await (const chunk of request) chunks.push(chunk);
      const body = JSON.parse(Buffer.concat(chunks).toString() || "{}");
      response.setHeader("content-type", "application/json");
      assert.equal(request.headers.authorization, "Bearer contract-test-key");
      if (request.method === "POST" && request.url === "/v1/computers") {
        const key = request.headers["idempotency-key"];
        if (typeof key !== "string" || !key) {
          response.writeHead(400).end(
            JSON.stringify({
              detail: "Idempotency-Key is required for computer creation",
            }),
          );
          return;
        }
        if (body.external_volume_enabled === true) {
          response.writeHead(422).end(
            JSON.stringify({
              detail: "External volumes are not available on pool computers",
            }),
          );
          return;
        }
        keys.push(key);
        const id = `cmp_contract_${keys.length}`;
        allocated.add(id);
        response.writeHead(201).end(JSON.stringify(info(id)));
        return;
      }
      const route = request.url?.match(
        /^\/v1\/computers\/([^/]+)(?:\/(exec|start))?$/,
      );
      const id = route?.[1];
      if (!id || !allocated.has(id)) {
        response.writeHead(404).end(JSON.stringify({ detail: "Not Found" }));
        return;
      }
      if (request.method === "DELETE") {
        allocated.delete(id);
        response.writeHead(204).end();
        return;
      }
      if (request.method === "GET" && failGet) {
        response
          .writeHead(503)
          .end(JSON.stringify({ detail: "Computer status unavailable" }));
        return;
      }
      if (request.method === "GET") {
        response.end(JSON.stringify(info(id)));
        return;
      }
      if (route?.[2] === "start") {
        existingStopped = false;
        response.end(JSON.stringify(info(id)));
        return;
      }
      if (request.method !== "POST" || route?.[2] !== "exec") {
        response.writeHead(404).end(JSON.stringify({ detail: "Not Found" }));
        return;
      }
      let result = { exit_code: 0, stdout: `${remoteRoot}\n`, stderr: "" };
      if (body.command.includes('home=$(cd "${HOME:?HOME is not set}"')) {
        if (failPreparation) {
          response
            .writeHead(503)
            .end(JSON.stringify({ detail: "Workspace unavailable" }));
          return;
        }
      } else {
        assert(body.command.length <= 10_000);
        try {
          const output = await execute("/bin/bash", ["-c", body.command], {
            env: {
              ...process.env,
              COPYFILE_DISABLE: "1",
              PATH: `${bin}${path.delimiter}${process.env.PATH}`,
            },
            timeout: 10_000,
          });
          result = { exit_code: 0, ...output };
        } catch (error) {
          const failure = error as {
            code?: number;
            stdout?: string;
            stderr?: string;
          };
          result = {
            exit_code: failure.code ?? 1,
            stdout: failure.stdout ?? "",
            stderr: failure.stderr ?? "",
          };
        }
      }
      response.end(
        JSON.stringify({
          ...result,
          command_id: `cmd_${calls.length}`,
          timed_out: false,
        }),
      );
    });
    server.listen(0, "127.0.0.1");
    await once(server, "listening");
    const address = server.address();
    assert(address && typeof address !== "string");
    const originalFetch = globalThis.fetch;
    const originalKey = process.env.CELESTO_API_KEY;
    globalThis.fetch = (input, init) => {
      const url = new URL(String(input));
      assert.equal(url.origin, "https://api.celesto.ai");
      return originalFetch(
        `http://127.0.0.1:${address.port}${url.pathname}`,
        init,
      );
    };
    process.env.CELESTO_API_KEY = "contract-test-key";
    async function loadSession(
      selected?: string,
      savedId?: string,
      reason = "startup",
      savedName = savedId,
    ) {
      const flags = new Map<string, unknown>();
      const tools = new Map<string, ToolDefinition>();
      const handlers = new Map<
        string,
        (event: unknown, ctx: ExtensionContext) => unknown
      >();
      const commands = new Map<
        string,
        (args: string, ctx: ExtensionContext) => Promise<void>
      >();
      const errors: string[] = [];
      if (process.env.PI_TEST_EXTENSION_PATH) {
        const loaded = await discoverAndLoadExtensions(
          [process.env.PI_TEST_EXTENSION_PATH],
          localRoot,
          path.join(root, "agent"),
        );
        assert.deepEqual(loaded.errors, []);
        assert.equal(loaded.extensions.length, 1);
        const extension = loaded.extensions[0]!;
        loaded.runtime.appendEntry = () => {};
        loaded.runtime.flagValues.set("celesto", true);
        if (selected)
          loaded.runtime.flagValues.set("celesto-computer", selected);
        for (const [name, tool] of extension.tools)
          tools.set(name, tool.definition);
        for (const [name, callbacks] of extension.handlers)
          handlers.set(name, callbacks[0]!);
        for (const [name, command] of extension.commands)
          commands.set(name, async (args, ctx) => {
            await command.handler(args, ctx as ExtensionCommandContext);
          });
      } else {
        celestoPiExtension({
          registerFlag(name: string, options: { default?: unknown }) {
            flags.set(name, options.default);
          },
          getFlag(name: string) {
            return flags.get(name);
          },
          registerTool(tool: ToolDefinition) {
            tools.set(tool.name, tool);
          },
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
            handlers.set(event, handler);
          },
          appendEntry() {},
        } as unknown as ExtensionAPI);
        flags.set("celesto", true);
        if (selected) flags.set("celesto-computer", selected);
      }
      const context = {
        cwd: localRoot,
        sessionManager: {
          getBranch: () =>
            savedId
              ? [
                  {
                    type: "custom",
                    customType: "celesto-pi-state",
                    data: {
                      version: 1,
                      computerId: savedId,
                      computerName: savedName,
                      owned: true,
                      keep: false,
                      localRoot,
                    },
                  },
                ]
              : [],
        },
        ui: {
          theme: { fg: (_color: string, value: string) => value },
          setStatus() {},
          notify(message: string, level: string) {
            if (level === "error") errors.push(message);
          },
        },
      } as unknown as ExtensionToolContext;
      await handlers.get("session_start")!(
        { type: "session_start", reason },
        context,
      );
      return { tools, handlers, commands, errors, context };
    }
    try {
      const { tools, handlers, commands, errors, context } =
        await loadSession();
      assert.deepEqual(errors, []);
      assert.equal(keys.length, 1);
      const bash = tools.get("bash")!;
      const pwd = await bash.execute(
        "pwd",
        { command: "pwd" },
        undefined,
        undefined,
        context,
      );
      assert(
        pwd.content.some(
          (item) => item.type === "text" && item.text.trim() === remoteRoot,
        ),
      );
      const silent = await bash.execute(
        "true",
        { command: "true" },
        undefined,
        undefined,
        context,
      );
      assert(!silent.isError);
      const failed = await bash.execute(
        "failure",
        { command: "printf problem >&2; exit 7" },
        undefined,
        undefined,
        context,
      );
      assert(
        failed.content.some(
          (item) =>
            item.type === "text" &&
            item.text.includes("problem") &&
            item.text.includes("7"),
        ),
      );
      await commands.get("celesto")!("push", context);
      assert.deepEqual(errors, []);
      const uploadedFile = await readFile(
        path.join(remoteRoot, "hello.txt"),
        "utf8",
      );
      assert.equal(uploadedFile, "hello from Pi\n");
      assert.equal(
        await readFile(path.join(remoteRoot, "large.txt"), "utf8"),
        largeContents,
      );
      const prompt = (await handlers.get("before_agent_start")!(
        { systemPrompt: `<cwd>\n${localRoot}\n</cwd>` },
        context,
      )) as { systemPrompt: string };
      assert.equal(prompt.systemPrompt, `<cwd>${remoteRoot}</cwd>`);
      await t.test(
        "sync applies pull, push, deletion and preserves independent changes",
        async () => {
          await writeFile(path.join(localRoot, "local-only.txt"), "local-only");
          await writeFile(
            path.join(remoteRoot, "remote-only.txt"),
            "remote-only",
          );
          await rm(path.join(remoteRoot, "hello.txt"));
          await commands.get("celesto")!("sync", context);
          assert.deepEqual(errors, []);
          assert.equal(
            await readFile(path.join(remoteRoot, "local-only.txt"), "utf8"),
            "local-only",
          );
          assert.equal(
            await readFile(path.join(localRoot, "remote-only.txt"), "utf8"),
            "remote-only",
          );
          await assert.rejects(readFile(path.join(localRoot, "hello.txt")), {
            code: "ENOENT",
          });
          await writeFile(path.join(localRoot, "large.txt"), "local-change");
          await writeFile(path.join(remoteRoot, "large.txt"), "remote-change");
          await commands.get("celesto")!("sync", context);
          assert.deepEqual(errors, []);
          assert.equal(
            await readFile(path.join(localRoot, "large.txt"), "utf8"),
            "local-change",
          );
          const conflict = (
            await readdir(path.join(localRoot, ".celesto-conflicts"), {
              recursive: true,
            })
          ).find((name) => name.endsWith("large.txt.remote"));
          assert(conflict);
          assert.equal(
            await readFile(
              path.join(localRoot, ".celesto-conflicts", conflict),
              "utf8",
            ),
            "remote-change",
          );
        },
      );
      await t.test(
        "remote sync refuses local symlink ancestors without outside writes",
        async () => {
          const outside = path.join(root, "outside");
          await mkdir(outside);
          await writeFile(path.join(outside, "target.txt"), "outside-original");
          await symlink(outside, path.join(localRoot, "linked"));
          await mkdir(path.join(remoteRoot, "linked"));
          await writeFile(
            path.join(remoteRoot, "linked", "target.txt"),
            "remote-change",
          );
          await commands.get("celesto")!("sync", context);
          assert(
            errors.some((message) => /symlink/i.test(message)),
            JSON.stringify(errors),
          );
          assert.equal(
            await readFile(path.join(outside, "target.txt"), "utf8"),
            "outside-original",
          );
        },
      );
      await t.test(
        "conflict copies refuse a linked conflict directory",
        async () => {
          await rm(path.join(localRoot, "linked"));
          await rm(path.join(remoteRoot, "linked"), { recursive: true });
          await rm(path.join(localRoot, ".celesto-conflicts"), {
            recursive: true,
          });
          const outside = path.join(root, "outside");
          await symlink(outside, path.join(localRoot, ".celesto-conflicts"));
          const before = await readdir(outside, { recursive: true });
          const errorCount = errors.length;
          await commands.get("celesto")!("sync", context);
          assert.equal(errors.length, errorCount + 1);
          assert.match(errors.at(-1)!, /symlink/i);
          assert.deepEqual(await readdir(outside, { recursive: true }), before);
        },
      );
      await handlers.get("session_shutdown")!(
        { type: "session_shutdown", reason: "quit" },
        context,
      );
      assert.deepEqual([...allocated], ["cmp_existing"]);
      await t.test(
        "failed workspace startup deletes newly allocated computers",
        async () => {
          failPreparation = true;
          const before = allocated.size;
          try {
            const failedSession = await loadSession();
            assert(
              failedSession.errors.some((message) =>
                /Workspace unavailable/.test(message),
              ),
            );
            assert.equal(allocated.size, before);
            const creations = keys.length;
            await assert.rejects(
              failedSession.tools
                .get("bash")!
                .execute(
                  "retry",
                  { command: "true" },
                  undefined,
                  undefined,
                  failedSession.context,
                ),
              /Workspace unavailable/,
            );
            assert.equal(keys.length, creations);
          } finally {
            failPreparation = false;
          }
        },
      );
      await t.test(
        "a failed saved-computer lookup does not allocate a replacement",
        async () => {
          failGet = true;
          const count = keys.length;
          try {
            const restored = await loadSession(undefined, "cmp_existing");
            assert(
              restored.errors.some((message) =>
                /Computer status unavailable/.test(message),
              ),
            );
            assert.equal(keys.length, count);
          } finally {
            failGet = false;
          }
        },
      );
      await t.test(
        "missing saved computers and owned forks allocate and clean up their own computer",
        async () => {
          for (const [savedId, reason] of [
            ["cmp_gone", "startup"],
            ["cmp_existing", "fork"],
          ]) {
            const before = allocated.size;
            const count = keys.length;
            const restored = await loadSession(undefined, savedId, reason);
            assert.deepEqual(restored.errors, []);
            assert.equal(keys.length, count + 1);
            await restored.handlers.get("session_shutdown")!(
              { type: "session_shutdown", reason: "quit" },
              restored.context,
            );
            assert.equal(allocated.size, before);
            assert(allocated.has("cmp_existing"));
          }
        },
      );
      await t.test(
        "caller-selected computers resume and remain caller-owned",
        async () => {
          const caller = await loadSession("cmp_existing");
          assert.deepEqual(caller.errors, []);
          assert.equal(existingStopped, false);
          await caller.handlers.get("session_shutdown")!(
            { type: "session_shutdown", reason: "quit" },
            caller.context,
          );
          assert(allocated.has("cmp_existing"));
        },
      );
      await t.test(
        "a reused name cannot transfer ownership to a different ID",
        async () => {
          const caller = await loadSession(
            "cmp_existing",
            "cmp_gone",
            "startup",
            "cmp_existing",
          );
          assert.deepEqual(caller.errors, []);
          await caller.handlers.get("session_shutdown")!(
            { type: "session_shutdown", reason: "quit" },
            caller.context,
          );
          assert(allocated.has("cmp_existing"));
        },
      );
      await t.test("keep preserves an extension-owned computer", async () => {
        const before = allocated.size;
        const kept = await loadSession();
        assert.deepEqual(kept.errors, []);
        await kept.commands.get("celesto")!("keep", kept.context);
        await kept.handlers.get("session_shutdown")!(
          { type: "session_shutdown", reason: "quit" },
          kept.context,
        );
        assert.equal(allocated.size, before + 1);
      });
      assert(!calls.some((call) => call.url?.endsWith("/exec/stream")));
      if (process.env.PI_TEST_ARTIFACT_DIR) {
        await mkdir(process.env.PI_TEST_ARTIFACT_DIR, { recursive: true });
        await writeFile(
          path.join(process.env.PI_TEST_ARTIFACT_DIR, "cloud-contract.json"),
          JSON.stringify(
            {
              requests: calls,
              prompt: prompt.systemPrompt,
              uploadedFile,
              expectedSymlinkRejection: errors,
              preservedComputers: [...allocated],
            },
            null,
            2,
          ),
        );
      }
    } finally {
      globalThis.fetch = originalFetch;
      if (originalKey === undefined) delete process.env.CELESTO_API_KEY;
      else process.env.CELESTO_API_KEY = originalKey;
      server.closeAllConnections();
      await new Promise<void>((resolve) => server.close(() => resolve()));
      await rm(root, { recursive: true, force: true });
    }
  },
);

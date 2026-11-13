import assert from "node:assert/strict";
import { once } from "node:events";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { Computer } from "../src/computer.js";

// Public transport/auth contracts beyond the extension's successful HTTP journey.
test("Cloud computer uses current Celesto credentials and API contracts", async (t) => {
  const root = await mkdtemp(path.join(os.tmpdir(), "celesto-pi-client-"));
  const previousHome = os.homedir;
  const previousCwd = process.cwd();
  const previousKey = process.env.CELESTO_API_KEY;
  const previousFetch = globalThis.fetch;
  const calls: Array<{
    method: string;
    url: string;
    key?: string;
    token?: string;
    body: any;
  }> = [];
  let responseStatus = 200;
  let rawResponse: string | undefined;
  let waitingCommand: (() => void) | undefined;
  let execResult: unknown = {
    exit_code: 7,
    stdout: "hello\n",
    stderr: "warn\n",
    command_id: "cmd_test",
    duration_ms: 20,
    timed_out: false,
  };
  const info = { id: "cmp_test", name: "test", status: "running" };
  const server = createServer(async (request, response) => {
    const chunks = [];
    for await (const chunk of request) chunks.push(chunk);
    const body = JSON.parse(Buffer.concat(chunks).toString() || "null");
    calls.push({
      method: request.method!,
      url: request.url!,
      key: request.headers["idempotency-key"] as string | undefined,
      token: request.headers.authorization,
      body,
    });
    response.setHeader("content-type", "application/json");
    if (rawResponse !== undefined) {
      response.writeHead(responseStatus).end(rawResponse);
      return;
    }
    if (body?.command === "wait-for-abort") {
      waitingCommand?.();
      return;
    }
    if (responseStatus !== 200) {
      response
        .writeHead(responseStatus)
        .end(JSON.stringify({ detail: "Host unavailable" }));
      return;
    }
    if (request.method === "DELETE") {
      response.writeHead(204).end();
      return;
    }
    if (request.url?.endsWith("/exec")) {
      response.end(JSON.stringify(execResult));
      return;
    }
    response
      .writeHead(
        request.method === "POST" && request.url === "/v1/computers"
          ? 201
          : 200,
      )
      .end(JSON.stringify(info));
  });
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  const address = server.address();
  assert(address && typeof address !== "string");
  const origin = `http://127.0.0.1:${address.port}`;
  let lastOrigin = "";
  globalThis.fetch = (input, init) => {
    const url = new URL(String(input));
    lastOrigin = url.origin;
    return previousFetch(`${origin}${url.pathname}`, init);
  };
  os.homedir = () => root;
  process.chdir(root);
  delete process.env.CELESTO_API_KEY;
  try {
    await mkdir(path.join(root, ".celesto"));
    await writeFile(
      path.join(root, ".celesto", "credentials"),
      JSON.stringify({ api_key: "saved-test-key", base_url: origin }),
    );
    await t.test("saved login retains the selected Cloud origin", async () => {
      await Computer.get("cmp_test");
      assert.equal(lastOrigin, origin);
      assert.equal(calls.at(-1)!.token, "Bearer saved-test-key");
    });
    await t.test("project and environment keys take precedence", async () => {
      await writeFile(
        path.join(root, ".env"),
        'CELESTO_API_KEY="project-test-key"\n',
      );
      await Computer.get("cmp_test");
      assert.equal(calls.at(-1)!.token, "Bearer project-test-key");
      process.env.CELESTO_API_KEY = "environment-test-key";
      await Computer.get("cmp_test");
      assert.equal(calls.at(-1)!.token, "Bearer environment-test-key");
      assert.equal(lastOrigin, "https://api.celesto.ai");
    });
    await t.test(
      "create uses one distinct key per persistent-home allocation",
      async () => {
        await Computer.create();
        await Computer.create();
        const creations = calls.filter((call) => call.url === "/v1/computers");
        assert.equal(creations.length, 2);
        assert.match(creations[0]!.key ?? "", /^[0-9a-f-]{36}$/);
        assert.notEqual(creations[0]!.key, creations[1]!.key);
        assert.deepEqual(creations[0]!.body, { external_volume_enabled: true });
      },
    );
    const computer = await Computer.get("cmp_test");
    await t.test(
      "buffered execution yields output and metadata without stream endpoints",
      async () => {
        const events = [];
        for await (const event of computer.runStream("echo hello", {
          timeout: 60,
        }))
          events.push(event);
        assert.deepEqual(calls.at(-1)!.body, {
          command: "echo hello",
          timeout: 60,
        });
        assert.equal(calls.at(-1)!.url, "/v1/computers/cmp_test/exec");
        assert.deepEqual(events, [
          { type: "stdout", data: "hello\n" },
          { type: "stderr", data: "warn\n" },
          {
            type: "exit",
            exitCode: 7,
            commandId: "cmd_test",
            durationMs: 20,
            timedOut: false,
          },
        ]);
        execResult = {
          exit_code: 0,
          stdout: "",
          stderr: "",
          command_id: null,
          timed_out: null,
          duration_ms: null,
        };
        const silent = [];
        for await (const event of computer.runStream("true"))
          silent.push(event);
        assert.deepEqual(silent, [{ type: "exit", exitCode: 0 }]);
      },
    );
    await t.test(
      "lifecycle routes and refresh keep the current state",
      async () => {
        await computer.start();
        await computer.refresh();
        await computer.delete();
        assert.deepEqual(
          calls.slice(-3).map(({ method, url }) => [method, url]),
          [
            ["POST", "/v1/computers/cmp_test/start"],
            ["GET", "/v1/computers/cmp_test"],
            ["DELETE", "/v1/computers/cmp_test"],
          ],
        );
        assert.equal(computer.status, "deleted");
      },
    );
    await t.test(
      "API errors and aborts never replay creation or execution",
      async () => {
        responseStatus = 503;
        let count = calls.length;
        await assert.rejects(
          Computer.create(),
          (error: unknown) =>
            error instanceof Error &&
            "status" in error &&
            error.status === 503 &&
            /Host unavailable/.test(error.message),
        );
        assert.equal(calls.length, count + 1);
        count = calls.length;
        await assert.rejects(
          computer.runStream("true").next(),
          /Host unavailable/,
        );
        assert.equal(calls.length, count + 1);
        responseStatus = 200;
        await assert.rejects(
          computer.run("true", { signal: AbortSignal.abort() }),
        );
        assert.equal(calls.length, count + 1);
      },
    );
    await t.test(
      "in-flight abort and deadlines stop pending requests without replay",
      async () => {
        let ready!: () => void;
        const started = new Promise<void>((resolve) => {
          ready = resolve;
        });
        waitingCommand = ready;
        const abort = new AbortController();
        const pending = computer.run("wait-for-abort", {
          signal: abort.signal,
        });
        await started;
        const count = calls.length;
        abort.abort();
        await assert.rejects(pending);
        assert.equal(calls.length, count);
        const originalTimeout = AbortSignal.timeout;
        let deadlineMs = 0;
        AbortSignal.timeout = (ms) => {
          deadlineMs = ms;
          return originalTimeout(20);
        };
        try {
          await assert.rejects(computer.run("wait-for-abort", { timeout: 1 }));
          assert.equal(deadlineMs, 11_000);
        } finally {
          AbortSignal.timeout = originalTimeout;
          waitingCommand = undefined;
        }
      },
    );
    await t.test(
      "malformed HTTP bodies and computer envelopes fail clearly",
      async () => {
        for (const body of [
          "not-json",
          "",
          JSON.stringify({ status: "running" }),
        ]) {
          rawResponse = body;
          await assert.rejects(Computer.get("cmp_test"), /invalid/i);
        }
        responseStatus = 404;
        rawResponse = "Not Found";
        await assert.rejects(Computer.get("cmp_test"), /404/);
        rawResponse = undefined;
        responseStatus = 200;
      },
    );
    await t.test(
      "invalid commands and responses fail before being used",
      async () => {
        const count = calls.length;
        await assert.rejects(computer.run("x".repeat(10001)), /10,000/);
        await assert.rejects(computer.run("true", { timeout: 301 }), /300/);
        assert.equal(calls.length, count);
        execResult = { stdout: "missing exit code", stderr: "" };
        await assert.rejects(computer.run("true"), /invalid command/i);
      },
    );
    await t.test(
      "unsafe or missing saved credentials never send a request",
      async () => {
        delete process.env.CELESTO_API_KEY;
        await rm(path.join(root, ".env"));
        const count = calls.length;
        for (const saved of [
          { api_key: "saved-test-key", base_url: "http://unsafe.example" },
          {},
        ]) {
          await writeFile(
            path.join(root, ".celesto", "credentials"),
            JSON.stringify(saved),
          );
          await assert.rejects(Computer.get("cmp_test"), /HTTPS|credentials/i);
          assert.equal(calls.length, count);
        }
      },
    );
  } finally {
    globalThis.fetch = previousFetch;
    os.homedir = previousHome;
    process.chdir(previousCwd);
    if (previousKey === undefined) delete process.env.CELESTO_API_KEY;
    else process.env.CELESTO_API_KEY = previousKey;
    server.closeAllConnections();
    await new Promise<void>((resolve) => server.close(() => resolve()));
    await rm(root, { recursive: true, force: true });
  }
});

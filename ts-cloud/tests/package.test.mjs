import assert from "node:assert/strict";
import { execFile } from "node:child_process";
import { once } from "node:events";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { createServer } from "node:http";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";
import { promisify } from "node:util";

const run = promisify(execFile);
const packageRoot = fileURLToPath(new URL("../", import.meta.url));
const artifacts = process.env.CELESTO_SDK_ARTIFACT_DIR
  ? resolve(process.env.CELESTO_SDK_ARTIFACT_DIR)
  : resolve(packageRoot, "../artifacts/cloud-sdk");

test("the installed npm package creates, runs commands, and deletes Cloud computers", { timeout: 60_000 }, async (t) => {
  const fixture = await mkdtemp(join(tmpdir(), "celesto-cloud-package-"));
  t.after(() => rm(fixture, { recursive: true, force: true }));
  await mkdir(artifacts, { recursive: true });
  const pack = await run("npm", ["pack", "--json", "--pack-destination", artifacts], { cwd: packageRoot });
  const packed = JSON.parse(pack.stdout);
  const [{ filename }] = Array.isArray(packed) ? packed : Object.values(packed);
  await run("npm", ["install", "--ignore-scripts", "--no-audit", "--no-fund", "--no-package-lock",
    join(artifacts, filename)], { cwd: fixture });

  const entry = join(fixture, "consumer.mjs");
  await writeFile(entry, 'export { Computer } from "@celestoai/sdk";\n');
  const { Computer } = await import(pathToFileURL(entry).href);
  const types = join(fixture, "consumer.mts");
  await writeFile(types, `
import { Computer, type CreateComputerParams } from "@celestoai/sdk";
const params: CreateComputerParams = { sizeId: "micro", idempotencyKey: "job-42" };
export async function create(): Promise<string | null | undefined> {
  return (await Computer.create(params)).sizeId;
}
`);
  await run(process.execPath, [
    join(packageRoot, "node_modules/typescript/bin/tsc"), "--noEmit", "--strict", "--skipLibCheck",
    "--module", "nodenext", "--target", "es2022", types,
  ]);

  const require = createRequire(entry);
  for (const [subpath, symbol] of [
    ["", "Computer"],
    ["/computers", "Computer"],
    ["/agents", "ManagedAgentsClient"],
    ["/gatekeeper", "GatekeeperClient"],
  ]) {
    assert.equal(typeof require(`@celestoai/sdk${subpath}`)[symbol], "function", `${subpath}:${symbol}`);
  }

  const computers = new Map();
  const requests = [];
  const creates = new Map();
  let nextId = 1;
  const server = createServer(async (req, res) => {
    const { method, url } = req;
    requests.push({ method, url });
    const reply = (status, payload) => {
      res.writeHead(status, { "Content-Type": "application/json" });
      res.end(JSON.stringify(payload));
    };
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    const body = chunks.length ? JSON.parse(Buffer.concat(chunks).toString()) : {};

    if (method === "POST" && url === "/v1/computers") {
      const key = req.headers["idempotency-key"];
      if (typeof key !== "string" || !key) {
        return reply(400, { detail: "Idempotency-Key is required for computer creation" });
      }
      if (Object.keys(body).some((field) => field !== "size_id") ||
          (body.size_id !== undefined && body.size_id !== "micro")) {
        return reply(422, { detail: "Send a supported size_id, without resource overrides" });
      }
      const prior = creates.get(key);
      if (prior) {
        if (prior.body !== JSON.stringify(body) || !computers.has(prior.id)) {
          return reply(409, { detail: "The create request cannot be replayed" });
        }
        return reply(201, computers.get(prior.id));
      }
      const id = `cmp_${nextId++}`;
      creates.set(key, { id, body: JSON.stringify(body) });
      const computer = {
        id, name: id, status: "running", size_id: body.size_id ?? null, vcpus: 1,
        ram_mb: body.size_id === "micro" ? 512 : 1024,
        disk_size_mb: 8192, image: "ubuntu", template_id: "scratch",
        created_at: "2026-11-24T00:00:00Z",
      };
      computers.set(id, computer);
      return reply(201, computer);
    }

    const match = /^\/v1\/computers\/(cmp_\d+)(\/exec)?$/.exec(url ?? "");
    const computer = computers.get(match?.[1]);
    if (!computer) return reply(404, { detail: "Not found" });
    if (method === "POST" && match[2] === "/exec" && body.command === "echo hello") {
      return reply(200, { exit_code: 0, stdout: "hello\n", stderr: "" });
    }
    if (method === "POST" && match[2] === "/exec" && body.command === "😀".repeat(10_000)) {
      return reply(200, { exit_code: 0, stdout: "", stderr: "" });
    }
    if (method === "POST" && match[2] === "/exec" && body.command === "exit 7" && body.timeout === 60) {
      return reply(200, {
        exit_code: 7, stdout: "hello\n", stderr: "warning\n",
        command_id: "cmd_fixture", duration_ms: 2, timed_out: false,
      });
    }
    if (method === "DELETE" && !match[2]) {
      computers.delete(computer.id);
      return reply(200, { ...computer, status: "deleted" });
    }
    return reply(404, { detail: "Not found" });
  });
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  t.after(() => new Promise((done) => {
    server.close(done);
    server.closeAllConnections();
  }));
  const config = { token: "contract-fixture", baseUrl: `http://127.0.0.1:${server.address().port}` };

  for (let i = 0; i < 2; i++) {
    const computer = await Computer.create({}, config);
    try {
      const result = await computer.run("echo hello");
      assert.deepEqual(result, { exitCode: 0, stdout: "hello\n", stderr: "" });
    } finally {
      await computer.delete();
    }
    assert.equal(computer.status, "deleted");
  }
  assert.equal(creates.size, 2);

  const createRequests = requests.length;
  await assert.rejects(Computer.create({ cpus: 2 }, config), /use sizeId/i);
  await assert.rejects(Computer.create({ size: "micro" }, config), /size.*sizeId/i);
  await assert.rejects(Computer.create({ labels: { job: "42" } }, config), /labels/i);
  assert.equal(requests.length, createRequests, "bad create options must not allocate a computer");

  const params = { idempotencyKey: "job-42", sizeId: "micro" };
  const computer = await Computer.create(params, { ...config, headers: { "idempotency-key": "other" } });
  try {
    const replayed = await Computer.create(params, config);
    assert.equal(replayed.id, computer.id);
    assert.deepEqual(JSON.parse(creates.get("job-42").body), { size_id: "micro" });
    assert.equal(computer.sizeId, "micro");
    assert.equal(computer.ramMb, 512);

    const beforeInvalidExec = requests.length;
    await assert.rejects(computer.run("x".repeat(10_001)), /10,000 characters/);
    await assert.rejects(computer.execStream("echo hello", { timeout: 301 }).next(), /1 and 300 seconds/);
    assert.equal(requests.length, beforeInvalidExec, "invalid commands must not run");
    assert.equal((await computer.run("😀".repeat(10_000))).exitCode, 0);

    const startedAt = requests.length;
    const events = [];
    for await (const event of computer.runStream("exit 7", { timeout: 60 })) events.push(event);
    assert.deepEqual(events, [
      { type: "stdout", data: "hello\n" },
      { type: "stderr", data: "warning\n" },
      { type: "exit", exitCode: 7, commandId: "cmd_fixture", durationMs: 2, timedOut: false },
    ]);
    const aliasEvents = [];
    for await (const event of computer.execStream("echo hello")) aliasEvents.push(event);
    assert.deepEqual(aliasEvents, [{ type: "stdout", data: "hello\n" }, { type: "exit", exitCode: 0 }]);
    assert.deepEqual(requests.slice(startedAt), [
      { method: "POST", url: `/v1/computers/${computer.id}/exec` },
      { method: "POST", url: `/v1/computers/${computer.id}/exec` },
    ]);
  } finally {
    await computer.delete();
  }
  assert.equal(computers.size, 0);
  assert.equal(creates.size, 3);
  await writeFile(join(artifacts, "cloud-contract.json"), JSON.stringify({ filename, requests }, null, 2));
});

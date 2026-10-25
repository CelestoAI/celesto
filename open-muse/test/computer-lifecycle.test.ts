import assert from "node:assert/strict";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createServer } from "node:http";
import test, { type TestContext } from "node:test";
import { ConversationManager } from "../server/manager.js";
import { ConversationStateStore } from "../server/state-store.js";
import { createComputerProvider, type ComputerProvider, type OpenMuseComputer } from "../server/computer-provider.js";
import type { ConversationContext } from "../server/types.js";

async function temporaryStore(t: TestContext) {
  const directory = await mkdtemp(join(tmpdir(), "open-muse-computer-"));
  t.after(() => rm(directory, { recursive: true, force: true }));
  return new ConversationStateStore(join(directory, "state.json"));
}

function contextOf(manager: ConversationManager): ConversationContext {
  return (manager as unknown as { context: ConversationContext }).context;
}

function computer(calls: string[], id = "cmp-persisted"): OpenMuseComputer {
  return {
    reference: { provider: "celesto", id },
    exec: async () => ({ ok: true, exitCode: 0, stdout: "", stderr: "", durationMs: 0 }),
    createBrowserConnection: async () => ({ url: "wss://gateway/browser?token=browser-secret" }),
    createDisplayConnection: async (mode) => {
      calls.push(`display:${mode}`);
      return { url: `wss://gateway/display?token=${mode}-secret` };
    },
    detach: async () => { calls.push("detach"); },
    delete: async () => { calls.push("delete"); },
  };
}

function provider(handle: OpenMuseComputer | undefined, calls: string[]): ComputerProvider {
  return {
    id: "celesto",
    create: async () => { calls.push("create"); return computer(calls, "cmp-created"); },
    reconnect: async (reference) => { calls.push(`reconnect:${reference.id}`); return handle; },
  };
}

test("shutdown detaches a cloud computer and restart reconnects the same saved ID", async (t) => {
  const store = await temporaryStore(t);
  const calls: string[] = [];
  const firstHandle = computer(calls);
  const first = new ConversationManager("", "gpt-5-mini", false, store, undefined, { computerProvider: provider(firstHandle, calls) });
  const created = await first.create();
  const context = contextOf(first);
  context.computer = firstHandle;
  context.computerReference = firstHandle.reference;
  context.sessionLifecycle = "ready";
  await first.close();

  const secondHandle = computer(calls);
  const reopened = await ConversationManager.open("", "gpt-5-mini", false, store, { computerProvider: provider(secondHandle, calls) });
  const snapshot = reopened.snapshot(created.id);

  assert.equal(snapshot.viewerReady, true);
  assert.deepEqual(contextOf(reopened).computerReference, { provider: "celesto", id: "cmp-persisted" });
  assert.deepEqual(calls.slice(0, 2), ["detach", "reconnect:cmp-persisted"]);

  await reopened.stop(created.id);
  assert.equal(contextOf(reopened).computerReference, undefined);
  assert.equal(calls.at(-1), "delete");
  const saved = JSON.parse(await readFile(store.path, "utf8")) as { conversations: Array<{ computerReference?: unknown }> };
  assert.equal(saved.conversations[0]?.computerReference, undefined);
});

test("a missing cloud computer enters recoverable state without creating a replacement", async (t) => {
  const store = await temporaryStore(t);
  const setupCalls: string[] = [];
  const manager = new ConversationManager("", "gpt-5-mini", false, store);
  const created = await manager.create();
  const context = contextOf(manager);
  context.computerReference = { provider: "celesto", id: "cmp-gone" };
  await store.save({
    fileVersion: 6,
    activeConversationId: context.id,
    conversations: [(await import("../server/state-store.js")).serializeConversationRecord(context)],
  });

  const restored = await ConversationManager.open("", "gpt-5-mini", false, store, {
    computerProvider: provider(undefined, setupCalls),
  });
  const snapshot = restored.snapshot(created.id);

  assert.equal(snapshot.runState, "interrupted");
  assert.equal(snapshot.recovery?.kind, "computer_unavailable");
  assert.deepEqual(setupCalls, ["reconnect:cmp-gone"]);
  assert.equal(setupCalls.includes("create"), false);
});

// Value: protects=explicit saved-Cloud cleanup without adopting remote compute;
// fails_when=cleanup reconnects, drops a failed deletion, or provider migration prevents startup;
// why_new=existing lifecycle fixtures allow reconnect; seam=none;
// no_claim=Cloud service availability (real SDK requests terminate at a local HTTP fixture).
for (const outcome of ["deleted", "missing", "retry"] as const) {
  test(`saved Cloud cleanup supports local migration (${outcome})`, async (t) => {
    const store = await temporaryStore(t);
    const calls: string[] = [];
    let failDelete = outcome === "retry";
    const server = createServer((request, response) => {
      calls.push(`${request.method} ${request.url}`);
      assert.equal(request.headers.authorization, "Bearer cleanup-test");
      response.setHeader("Content-Type", "application/json");
      if (outcome === "missing") {
        response.writeHead(404).end(JSON.stringify({ detail: "Computer not found" }));
      } else if (request.method === "DELETE" && failDelete) {
        response.writeHead(503).end(JSON.stringify({ detail: "Cleanup temporarily unavailable" }));
      } else if (["GET", "DELETE"].includes(request.method!) && request.url === "/v1/computers/cmp-old") {
        response.end(JSON.stringify({ id: "cmp-old", status: request.method === "DELETE" ? "deleting" : "stopped" }));
      } else response.writeHead(500).end(JSON.stringify({ detail: "Unexpected compute access" }));
    });
    await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
    t.after(() => new Promise<void>((resolve) => server.close(() => resolve())));
    const address = server.address() as { port: number };
    const local = createComputerProvider({ provider: "local" });
    const manager = new ConversationManager("", "gpt-5-mini", false, store, undefined, { computerProvider: local });
    const created = await manager.create();
    const context = contextOf(manager);
    context.computerReference = { provider: "celesto", id: "cmp-old" };
    await manager.close();

    const migrated = await ConversationManager.open("", "gpt-5-mini", false, store, {
      computerProvider: local,
      createAgent: () => { throw new Error("Recovery must not start model work"); },
    });
    const recovery = migrated.snapshot(created.id);
    assert.equal(recovery.runState, "interrupted");
    assert.equal(recovery.viewerReady, false);
    assert.match(recovery.computer.automationError!, /cmp-old.*OPENMUSE_COMPUTER_PROVIDER=celesto.*Start over/);
    assert.match(recovery.recovery?.summary!, /cmp-old.*OPENMUSE_COMPUTER_PROVIDER=celesto.*Start over/);
    await assert.rejects(migrated.continueInterrupted(created.id), /cmp-old.*OPENMUSE_COMPUTER_PROVIDER=celesto/);
    await assert.rejects(migrated.startOver(created.id), /cmp-old.*OPENMUSE_COMPUTER_PROVIDER=celesto/);
    assert.equal(migrated.snapshot(created.id).runState, "interrupted");
    assert.deepEqual((await store.load())!.conversation.computerReference, { provider: "celesto", id: "cmp-old" });
    assert.deepEqual(calls, []);

    const cloud = createComputerProvider({ provider: "celesto", apiKey: "cleanup-test", apiUrl: `http://127.0.0.1:${address.port}` });
    const cleanup = await ConversationManager.open("", "gpt-5-mini", false, store, { computerProvider: cloud });
    assert.equal(cleanup.snapshot(created.id).viewerReady, false);
    assert.match(cleanup.snapshot(created.id).recovery?.summary!, /cmp-old.*Start over.*local/);
    assert.deepEqual(calls, []);
    if (outcome === "retry") {
      await assert.rejects(cleanup.startOver(created.id), /Cleanup temporarily unavailable/);
      assert.equal(cleanup.snapshot(created.id).runState, "interrupted");
      assert.notEqual(cleanup.snapshot(created.id).sessionLifecycle, "deleted");
      assert.deepEqual((await store.load())!.conversation.computerReference, { provider: "celesto", id: "cmp-old" });
      failDelete = false;
    }
    const replacement = await cleanup.startOver(created.id);
    assert.notEqual(replacement.id, created.id);
    assert.equal((await store.load())!.conversation.computerReference, undefined);
    assert.deepEqual(calls, outcome === "missing"
      ? ["GET /v1/computers/cmp-old"]
      : Array.from({ length: outcome === "retry" ? 2 : 1 }, () => ["GET /v1/computers/cmp-old", "DELETE /v1/computers/cmp-old"]).flat());
    const ready = await ConversationManager.open("", "gpt-5-mini", false, store, { computerProvider: local });
    assert.equal(ready.snapshot(replacement.id).runState, "idle");
    t.diagnostic(`cleanup evidence: ${JSON.stringify({ outcome, requests: calls, replacement: replacement.id, statePath: store.path })}`);
  });
}

test("viewer capabilities are one-time and follow the current control owner", async () => {
  const calls: string[] = [];
  const manager = new ConversationManager("", "gpt-5-mini");
  const created = await manager.create();
  const context = contextOf(manager);
  context.computer = computer(calls);
  context.computerReference = context.computer.reference;
  context.sessionLifecycle = "ready";
  const invalidations: string[] = [];
  manager.onViewerInvalidated((conversationId) => invalidations.push(conversationId));

  const watching = manager.issueViewerNonce(created.id).viewerPath;
  const watchToken = new URL(watching, "http://localhost").searchParams.get("path")!.split("token=")[1]!;
  assert.match((await manager.consumeViewerNonce(created.id, watchToken))!, /read_only-secret/);
  assert.equal(await manager.consumeViewerNonce(created.id, watchToken), undefined);

  const stale = manager.issueViewerNonce(created.id).viewerPath;
  const staleToken = new URL(stale, "http://localhost").searchParams.get("path")!.split("token=")[1]!;
  const takeover = await manager.takeover(created.id);
  assert.equal(await manager.consumeViewerNonce(created.id, staleToken), undefined);

  const controlling = manager.issueViewerNonce(created.id).viewerPath;
  const controlToken = new URL(controlling, "http://localhost").searchParams.get("path")!.split("token=")[1]!;
  assert.match((await manager.consumeViewerNonce(created.id, controlToken))!, /read_write-secret/);

  await manager.resume(created.id, takeover.controlEpoch);
  const returned = manager.issueViewerNonce(created.id).viewerPath;
  const returnToken = new URL(returned, "http://localhost").searchParams.get("path")!.split("token=")[1]!;
  assert.match((await manager.consumeViewerNonce(created.id, returnToken))!, /read_only-secret/);
  assert.deepEqual(calls, ["display:read_only", "display:read_write", "display:read_only"]);
  assert.deepEqual(invalidations, [created.id, created.id, created.id]);
});

test("a display connection minted after Stop is discarded", async () => {
  let markMintStarted!: () => void;
  let finishMint!: () => void;
  const mintStarted = new Promise<void>((resolve) => { markMintStarted = resolve; });
  const mintFinished = new Promise<void>((resolve) => { finishMint = resolve; });
  const calls: string[] = [];
  const handle = computer(calls);
  handle.createDisplayConnection = async () => {
    markMintStarted();
    await mintFinished;
    return { url: "wss://gateway/display?token=expired" };
  };
  const manager = new ConversationManager("", "gpt-5-mini");
  const created = await manager.create();
  const context = contextOf(manager);
  context.computer = handle;
  context.computerReference = handle.reference;
  context.sessionLifecycle = "ready";
  const viewerPath = manager.issueViewerNonce(created.id).viewerPath;
  const token = new URL(viewerPath, "http://localhost").searchParams.get("path")!.split("token=")[1]!;

  const consuming = manager.consumeViewerNonce(created.id, token);
  await mintStarted;
  await manager.stop(created.id);
  finishMint();

  assert.equal(await consuming, undefined);
});

test("saved state contains the cloud ID but no API or connection token", async (t) => {
  const store = await temporaryStore(t);
  const calls: string[] = [];
  const handle = Object.assign(computer(calls), { apiKey: "api-secret", connectionUrl: "wss://gateway?token=connection-secret" });
  const manager = new ConversationManager("", "gpt-5-mini", false, store);
  await manager.create();
  const context = contextOf(manager);
  context.computer = handle;
  context.computerReference = handle.reference;
  context.sessionLifecycle = "ready";
  await manager.close();

  const saved = await readFile(store.path, "utf8");
  assert.match(saved, /cmp-persisted/);
  assert.doesNotMatch(saved, /api-secret|connection-secret|gateway/);
});

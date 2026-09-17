import assert from "node:assert/strict";
import test from "node:test";
import { ConversationManager } from "../server/manager.js";
import type { ConversationContext } from "../server/types.js";

function attachSyntheticTab(context: ConversationContext): void {
  const page = {
    url: () => "https://example.com",
    isClosed: () => false,
    context: () => ({ browser: () => ({ isConnected: () => true }) }),
  } as ConversationContext["page"];
  const id = "tab-test";
  context.page = page;
  context.activeTabId = id;
  context.tabs.set(id, { id, owner: "agent", epoch: 1, controlEpoch: context.controlEpoch!, page: page! });
  context.playwright = { isConnected: () => true, contexts: () => [{ pages: () => [page] }], close: async () => undefined } as unknown as ConversationContext["playwright"];
}

async function beginProgram(manager: ConversationManager, program: string, summary: string) {
  const context = (manager as unknown as { context: ConversationContext }).context;
  const broker = (manager as unknown as {
    broker: (active: ConversationContext) => { runProgram: (source: string, interaction: boolean, reason: string) => Promise<Record<string, unknown>> };
  }).broker(context);
  const result = broker.runProgram(program, true, summary);
  while (!context.pendingApproval) await Promise.resolve();
  return { context, pending: context.pendingApproval, result };
}

// Regression: ISSUE-002 — refreshing always created a second active conversation
// Found by /qa on 2026-09-13
// Report: .gstack/qa-reports/qa-report-127-0-0-1-2026-09-13.md
test("bootstrap callers can recover the active conversation", async () => {
  const manager = new ConversationManager("", "gpt-5-mini");
  const created = await manager.create();
  assert.equal(manager.activeConversationId, created.id);
  assert.equal(manager.snapshot(manager.activeConversationId!).id, created.id);
  await manager.stop(created.id);
  assert.equal(manager.activeConversationId, created.id);
});

test("conversation creation preserves history and human control blocks switching", async () => {
  const manager = new ConversationManager("", "gpt-5-mini");
  const created = await manager.create();
  const replacement = await manager.create();
  assert.notEqual(replacement.id, created.id);
  assert.equal(manager.list().conversations.length, 2);
  await manager.activate(created.id);

  const takeover = await manager.takeover(created.id);
  assert.equal(manager.snapshot(created.id).controlOwner, "human");
  assert.deepEqual(await manager.takeover(created.id), takeover);
  await assert.rejects(manager.activate(replacement.id), (error: unknown) => (error as { status?: number }).status === 409);
  await assert.rejects(
    manager.resume(created.id, "wrong-control-epoch"),
    (error: unknown) => (error as { status?: number }).status === 409,
  );

  const resumed = await manager.resume(created.id, takeover.controlEpoch);
  assert.equal(resumed.controlOwner, "agent");
  await manager.stop(created.id);
});

test("replacing a failed conversation releases its disposable resources", async () => {
  const manager = new ConversationManager("", "gpt-5-mini");
  const created = await manager.create();
  const context = (manager as unknown as { context: ConversationContext }).context;
  const closed: string[] = [];
  context.runState = "failed";
  context.playwright = { close: async () => { closed.push("playwright"); } } as ConversationContext["playwright"];
  context.computer = { detach: async () => { closed.push("computer"); } } as ConversationContext["computer"];

  const replacement = await manager.create();

  assert.notEqual(replacement.id, created.id);
  assert.deepEqual(closed, ["playwright", "computer"]);
});

test("takeover pauses an in-flight approved action and requires recovery", async () => {
  const manager = new ConversationManager("", "gpt-5-mini");
  const created = await manager.create();
  const context = (manager as unknown as { context: ConversationContext }).context;
  let finishAction!: () => void;
  let markStarted!: () => void;
  const actionFinished = new Promise<void>((resolve) => { finishAction = resolve; });
  const actionStarted = new Promise<void>((resolve) => { markStarted = resolve; });
  context.sessionLifecycle = "ready";
  attachSyntheticTab(context);
  context.computer = {
    status: "ready", computerId: "computer-test", sandboxId: "sandbox-test",
    display: { viewerUrl: "http://127.0.0.1:6080/vnc.html" },
    browser: { status: "ready", cdpUrl: "http://127.0.0.1:9222" },
    exec: async () => {
      markStarted();
      await actionFinished;
      return { ok: true, exitCode: 0, stdout: 'SMOLVM_BROWSER_RESULT={"ok":true,"value":{"programResult":{},"page":{"title":"","url":"about:blank","visibleText":""}}}', stderr: "", durationMs: 1 };
    },
    delete: async () => undefined,
  };
  const suspended = await beginProgram(manager, "return {};", "Read the page");
  const approval = manager.approve(created.id, suspended.pending.approvalId, suspended.pending.actionDigest, true);
  await actionStarted;
  const takeover = manager.takeover(created.id);
  const takeoverRejected = assert.rejects(takeover, (error: unknown) => (error as { status?: number }).status === 409);
  const actionRejected = assert.rejects(suspended.result, (error: unknown) => (error as { code?: string }).code === "browser_recovery_required");
  finishAction();
  await Promise.all([approval, actionRejected, takeoverRejected]);
  assert.equal(manager.snapshot(created.id).runState, "interrupted");
  assert.equal(manager.snapshot(created.id).recovery?.kind, "outcome_unknown");
  assert.equal(manager.snapshot(created.id).controlOwner, "pause_requested");
  await manager.stop(created.id);
});

test("approved browser results return to the original suspended tool call", async () => {
  const manager = new ConversationManager("", "gpt-5-mini");
  const created = await manager.create();
  const internals = manager as unknown as { context: ConversationContext };
  internals.context.sessionLifecycle = "ready";
  attachSyntheticTab(internals.context);
  internals.context.computer = {
    status: "ready", computerId: "computer-test", sandboxId: "sandbox-test",
    display: { viewerUrl: "http://127.0.0.1:6080/vnc.html" },
    browser: { status: "ready", cdpUrl: "http://127.0.0.1:9222" },
    exec: async () => ({
      ok: true, exitCode: 0,
      stdout: 'SMOLVM_BROWSER_RESULT={"ok":true,"value":{"programResult":{"title":"Amazon.in","price":"₹59,900"},"page":{"title":"Amazon.in","url":"https://amazon.in","visibleText":"iPhone ₹59,900"}}}',
      stderr: "", durationMs: 1,
    }),
    delete: async () => undefined,
  };
  const suspended = await beginProgram(manager, "return { title: await page.title() };", "Read the current price");
  const approval = manager.approve(created.id, suspended.pending.approvalId, suspended.pending.actionDigest, true);
  const [result] = await Promise.all([suspended.result, approval]);

  assert.deepEqual(result, {
    programResult: { title: "Amazon.in", price: "₹59,900" },
    page: { title: "Amazon.in", url: "https://amazon.in", visibleText: "iPhone ₹59,900" },
  });
  assert.equal(manager.snapshot(created.id).pendingApproval, undefined);
  await manager.stop(created.id);
});

test("duplicate approval submissions share one browser action", async () => {
  const manager = new ConversationManager("", "gpt-5-mini");
  const created = await manager.create();
  const internals = manager as unknown as { context: ConversationContext };
  let finishAction!: () => void;
  const actionFinished = new Promise<void>((resolve) => { finishAction = resolve; });
  let executions = 0;
  internals.context.sessionLifecycle = "ready";
  attachSyntheticTab(internals.context);
  internals.context.computer = {
    status: "ready", computerId: "computer-test", sandboxId: "sandbox-test",
    display: { viewerUrl: "http://127.0.0.1:6080/vnc.html" },
    browser: { status: "ready", cdpUrl: "http://127.0.0.1:9222" },
    exec: async () => {
      executions += 1;
      await actionFinished;
      return { ok: true, exitCode: 0, stdout: 'SMOLVM_BROWSER_RESULT={"ok":true,"value":{"programResult":{},"page":{"title":"","url":"about:blank","visibleText":""}}}', stderr: "", durationMs: 1 };
    },
    delete: async () => undefined,
  };
  const suspended = await beginProgram(manager, "return {};", "Read the page");
  const first = manager.approve(created.id, suspended.pending.approvalId, suspended.pending.actionDigest, true);
  const duplicate = manager.approve(created.id, suspended.pending.approvalId, suspended.pending.actionDigest, true);
  finishAction();
  const [firstSnapshot, duplicateSnapshot] = await Promise.all([first, duplicate, suspended.result]);

  assert.equal(executions, 1);
  assert.deepEqual(duplicateSnapshot, firstSnapshot);
  await manager.stop(created.id);
});

test("failed approved browser actions enter durable unknown-outcome recovery", async () => {
  const manager = new ConversationManager("", "gpt-5-mini");
  const created = await manager.create();
  const context = (manager as unknown as { context: ConversationContext }).context;
  context.sessionLifecycle = "ready";
  attachSyntheticTab(context);
  context.computer = {
    status: "ready", computerId: "computer-test", sandboxId: "sandbox-test",
    display: { viewerUrl: "http://127.0.0.1:6080/vnc.html" },
    browser: { status: "ready", cdpUrl: "http://127.0.0.1:9222" },
    exec: async () => ({ ok: false, exitCode: 1, stdout: "", stderr: "locator timed out", durationMs: 30_000 }),
    delete: async () => undefined,
  };
  const originalError = console.error;
  const logs: unknown[][] = [];
  console.error = (...args: unknown[]) => { logs.push(args); };

  try {
    const suspended = await beginProgram(manager, "return {};", "Read the page");
    await Promise.all([
      manager.approve(created.id, suspended.pending.approvalId, suspended.pending.actionDigest, true),
      assert.rejects(suspended.result, (error: unknown) => (error as { code?: string }).code === "browser_recovery_required"),
    ]);
  } finally {
    console.error = originalError;
  }

  const snapshot = manager.snapshot(created.id);
  assert.equal(snapshot.pendingApproval, undefined);
  assert.equal(snapshot.runState, "interrupted");
  assert.equal(snapshot.recovery?.kind, "outcome_unknown");
  assert.equal(snapshot.events.at(-1)?.type, "operation.outcome_unknown");
  assert.equal(String(logs[0]?.[0]), "OpenMuse website action failed.");
  assert.doesNotMatch(JSON.stringify(logs), /locator timed out/);
  await manager.stop(created.id);
});

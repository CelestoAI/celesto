import assert from "node:assert/strict";
import test from "node:test";
import { ConfirmationGate, availableCommands } from "../server/conversation-runtime.js";
import type { PendingApproval } from "../server/types.js";

const pending = (): PendingApproval => ({
  kind: "browser_operation",
  approvalId: "approval-one",
  actionDigest: "a".repeat(64),
  reason: "Click button “Subscribe”",
  expiresAt: new Date(Date.now() + 60_000).toISOString(),
});

test("confirmation releases only the matching suspended action", async () => {
  const gate = new ConfirmationGate();
  const approval = pending();
  const decision = gate.wait(approval);
  let responseFinished = false;
  const response = gate.resolve(approval.approvalId, approval.actionDigest, true).then(() => { responseFinished = true; });

  assert.equal(await decision, true);
  await Promise.resolve();
  assert.equal(responseFinished, false);
  gate.finish(approval.approvalId);
  await response;
  assert.equal(gate.pending, undefined);
});

test("stale confirmations fail closed and interruption rejects the waiter", async () => {
  const gate = new ConfirmationGate();
  const approval = pending();
  const decision = gate.wait(approval);

  await assert.rejects(gate.resolve("approval-old", approval.actionDigest, true), (error: unknown) => (error as { status?: number }).status === 409);
  gate.interrupt("Conversation changed.");
  await assert.rejects(decision, /Conversation changed/);
  assert.equal(gate.pending, undefined);
});

test("available commands are derived from the public activity", () => {
  assert.deepEqual(availableCommands({ activity: { kind: "human_control" }, viewerReady: true, modelReady: true }), ["return_control", "stop"]);
  assert.deepEqual(availableCommands({ activity: { kind: "recovering" }, viewerReady: false, modelReady: true }), ["continue", "start_over", "stop"]);
  assert.deepEqual(availableCommands({ activity: { kind: "stopped" }, viewerReady: false, modelReady: true }), ["change_conversation"]);
  assert.deepEqual(availableCommands({ activity: { kind: "stopping" }, viewerReady: false, modelReady: true }), []);
  assert.deepEqual(
    availableCommands({ activity: { kind: "awaiting_confirmation", approvalId: "approval-one" }, viewerReady: true, modelReady: true }),
    ["approve", "reject", "send_message", "change_conversation", "change_model", "take_control", "stop"],
  );
});

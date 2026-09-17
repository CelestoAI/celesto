import assert from "node:assert/strict";
import test from "node:test";
import { MAX_CONVERSATION_VIEW_BYTES, projectConversationView } from "../server/conversation-view.js";
import { ConversationManager } from "../server/manager.js";
import { TraceBuffer } from "../server/trace.js";
import type { ConversationContext } from "../server/types.js";

test("conversation views stay bounded while retaining the newest public state", async () => {
  const manager = new ConversationManager("", "gpt-5-mini");
  const created = await manager.create();
  const context = (manager as unknown as { context: ConversationContext }).context;
  for (let index = 0; index < 100; index += 1) {
    context.messages.push({
      id: `message-${index}`,
      role: index % 2 ? "assistant" : "user",
      text: `${index}:${"m".repeat(8_000)}`,
      createdAt: new Date().toISOString(),
    });
    context.events.push({
      id: index + 2,
      conversationId: created.id,
      stateVersion: context.stateVersion,
      createdAt: new Date().toISOString(),
      type: "message.completed",
      payload: { text: "e".repeat(8_000) },
    });
  }
  for (let index = 0; index < 4_000; index += 1) {
    context.grants.push({
      id: `grant-${index}-${"g".repeat(200)}`,
      actionKind: "add_to_cart",
      subject: { productId: `product-${index}` },
      variant: { kind: "any" },
      maxQuantity: 1,
      maxUnitPriceMinor: 100,
      currency: "INR",
      sourceMessageId: "message-99",
      expiresAt: new Date().toISOString(),
      state: "available",
    });
  }
  const traces = new TraceBuffer(created.id);
  for (let index = 0; index < 8; index += 1) {
    const execution = { conversationId: created.id, turnId: `turn-${index}`, userMessageId: `message-${index}` };
    traces.startTurn(execution);
    const step = traces.startStep(execution, "tool", "Large result");
    traces.completeStep(execution, step, { text: "x".repeat(64_000) });
    traces.setTurnState(execution, "completed");
  }

  const view = projectConversationView(context, traces.snapshot());

  assert.ok(Buffer.byteLength(JSON.stringify(view)) <= MAX_CONVERSATION_VIEW_BYTES);
  assert.equal(view.messages.at(-1)?.id, "message-99");
  assert.equal(view.activity.kind, "idle");
  assert.ok(view.availableCommands.includes("send_message"));
  assert.equal(view.grants.at(-1)?.id.startsWith("grant-3999-"), true);
});

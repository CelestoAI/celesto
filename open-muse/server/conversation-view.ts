import { redactBrowserOperation } from "./browser-operations.js";
import { availableCommands, type ConversationActivity } from "./conversation-runtime.js";
import { publicTabUrl } from "./browser-tabs.js";
import type { TraceSnapshot } from "./trace.js";
import type { ConversationContext } from "./types.js";

export const MAX_CONVERSATION_VIEW_BYTES = 256 * 1024;
const MAX_VIEW_MESSAGE_BYTES = 64 * 1024;
const MAX_VIEW_EVENT_BYTES = 64 * 1024;
const VIEW_JSON_OVERHEAD_BYTES = 1_024;

function jsonBytes(value: unknown): number { return Buffer.byteLength(JSON.stringify(value)); }

function boundedMessages(messages: ConversationContext["messages"]): ConversationContext["messages"] {
  const output = [] as ConversationContext["messages"];
  let bytes = 0;
  for (const message of messages.slice(-100).reverse()) {
    const size = jsonBytes(message);
    if (bytes + size > MAX_VIEW_MESSAGE_BYTES) break;
    output.unshift(message);
    bytes += size;
  }
  return output;
}

function boundedEvents(events: ConversationContext["events"]): ConversationContext["events"] {
  const output = [] as ConversationContext["events"];
  let bytes = 0;
  for (const event of events.slice(-100).reverse()) {
    const size = jsonBytes(event);
    if (bytes + size > MAX_VIEW_EVENT_BYTES) break;
    output.unshift(event);
    bytes += size;
  }
  return output;
}

function boundedTurns(traces: TraceSnapshot, base: object): TraceSnapshot["turns"] {
  const output: TraceSnapshot["turns"] = [];
  let bytes = jsonBytes(base);
  for (const turn of traces.turns.slice().reverse()) {
    if (bytes + jsonBytes(turn) <= MAX_CONVERSATION_VIEW_BYTES - VIEW_JSON_OVERHEAD_BYTES) {
      output.unshift(turn);
      bytes += jsonBytes(turn);
      continue;
    }
    const summary = {
      ...turn,
      steps: turn.steps.map(({ input: _input, output: _output, ...step }) => step),
    };
    if (bytes + jsonBytes(summary) <= MAX_CONVERSATION_VIEW_BYTES - VIEW_JSON_OVERHEAD_BYTES) {
      output.unshift(summary);
      bytes += jsonBytes(summary);
    }
  }
  return output;
}

export function conversationActivity(context: ConversationContext): ConversationActivity {
  if (context.controlOwner === "human") return { kind: "human_control" };
  if (context.pendingApproval) return { kind: "awaiting_confirmation", approvalId: context.pendingApproval.approvalId };
  switch (context.runState) {
    case "idle": return { kind: "idle" };
    case "model_turn": return { kind: "model_running" };
    case "tool_action": return { kind: "browser_running" };
    case "waiting_for_approval": return { kind: "recovering" };
    case "interrupted": return { kind: "recovering" };
    case "stopping": return { kind: "stopping" };
    case "stopped": return { kind: "stopped" };
    case "failed": return { kind: "failed" };
  }
}

export function projectConversationView(context: ConversationContext, traces: TraceSnapshot) {
  const activity = conversationActivity(context);
  const viewerReady = context.sessionLifecycle === "ready" && Boolean(context.computer);
  const pendingApproval = context.pendingApproval
    ? (({ program: _program, pageBinding: _pageBinding, tabControlEpoch: _tabControlEpoch, tabPageIndex: _tabPageIndex, traceStepId: _traceStepId, turnId: _turnId, userMessageId: _userMessageId, ...approval }) => ({
        ...approval,
        ...(approval.operation ? { operation: redactBrowserOperation(approval.operation) } : {}),
      }))(context.pendingApproval)
    : undefined;
  const base = {
    id: context.id,
    conversationId: context.id,
    version: context.stateVersion,
    stateVersion: context.stateVersion,
    activity,
    availableCommands: availableCommands({ activity, viewerReady, modelReady: context.modelAccessState === "ready" }),
    controlOwner: context.controlOwner,
    runState: context.runState,
    sessionLifecycle: context.sessionLifecycle,
    computer: { lifecycle: context.sessionLifecycle, automationError: context.lastBrowserError },
    viewer: { ready: viewerReady },
    providerId: context.providerId,
    modelId: context.modelId,
    modelAccessState: context.modelAccessState,
    messages: boundedMessages(context.messages),
    grants: context.grants.map(({ id: grantId, state, expiresAt }) => ({ id: grantId, state, expiresAt })),
    pendingApproval,
    recovery: context.recovery,
    tabs: [...context.tabs.values()].filter((tab) => !tab.page.isClosed()).map((tab) => ({
      id: tab.id,
      owner: tab.owner,
      epoch: tab.epoch,
      url: publicTabUrl(tab.page),
      active: tab.id === context.activeTabId,
      openerTabId: tab.openerTabId,
    })),
    viewerReady,
    traceStatus: "ready" as const,
    events: boundedEvents(context.events),
  };
  return { ...base, turns: boundedTurns(traces, base) };
}

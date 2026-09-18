import type { PendingApproval } from "./types.js";

export type ConversationActivity =
  | { kind: "idle" }
  | { kind: "model_running" }
  | { kind: "awaiting_confirmation"; approvalId: string }
  | { kind: "browser_running" }
  | { kind: "human_control" }
  | { kind: "recovering" }
  | { kind: "stopping" }
  | { kind: "stopped" }
  | { kind: "failed" };

export type ConversationCommand =
  | { kind: "send_message"; text: string }
  | { kind: "approve"; approvalId: string; actionDigest: string }
  | { kind: "reject"; approvalId: string; actionDigest: string }
  | { kind: "take_control" }
  | { kind: "return_control"; controlEpoch: string }
  | { kind: "continue" }
  | { kind: "start_over" }
  | { kind: "stop" }
  | { kind: "reconnect_model" }
  | { kind: "change_model"; providerId: string; modelId: string }
  | { kind: "adopt_popup"; tabId: string };

export interface ConversationCommandRequest {
  commandId: string;
  expectedVersion?: number;
  command: ConversationCommand;
}

interface ConfirmationLease {
  approval: PendingApproval;
  resolveDecision: (approved: boolean) => void;
  rejectDecision: (error: Error) => void;
  completion: Promise<void>;
  complete: () => void;
  decided: boolean;
}

/**
 * One in-process confirmation boundary. The original tool call waits here;
 * HTTP approval only releases it and waits for that exact action to settle.
 * The lease is deliberately not serializable: restart recovery interrupts it.
 */
export class ConfirmationGate {
  private lease?: ConfirmationLease;

  get pending(): PendingApproval | undefined { return this.lease?.approval; }

  async wait(approval: PendingApproval): Promise<boolean> {
    if (this.lease) throw new Error("Another website confirmation is already waiting.");
    let resolveDecision!: (approved: boolean) => void;
    let rejectDecision!: (error: Error) => void;
    let complete!: () => void;
    const decision = new Promise<boolean>((resolve, reject) => {
      resolveDecision = resolve;
      rejectDecision = reject;
    });
    const completion = new Promise<void>((resolve) => { complete = resolve; });
    this.lease = { approval, resolveDecision, rejectDecision, completion, complete, decided: false };
    return decision;
  }

  async resolve(approvalId: string, actionDigest: string, approved: boolean): Promise<void> {
    const lease = this.lease;
    if (!lease || lease.approval.approvalId !== approvalId || lease.approval.actionDigest !== actionDigest) {
      throw Object.assign(new Error("That approval is no longer current."), { status: 409 });
    }
    lease.decided = true;
    lease.resolveDecision(approved);
    await lease.completion;
  }

  finish(approvalId: string): void {
    const lease = this.lease;
    if (!lease || lease.approval.approvalId !== approvalId) return;
    this.lease = undefined;
    lease.complete();
  }

  interrupt(message = "The browser action was interrupted."): void {
    const lease = this.lease;
    if (!lease) return;
    if (lease.decided) return;
    this.lease = undefined;
    lease.rejectDecision(Object.assign(new Error(message), { code: "approval_interrupted" }));
    lease.complete();
  }
}

export function availableCommands(input: {
  activity: ConversationActivity;
  viewerReady: boolean;
  modelReady: boolean;
}): string[] {
  const { activity, viewerReady, modelReady } = input;
  if (activity.kind === "stopping") return [];
  if (activity.kind === "stopped") return ["change_conversation"];
  if (activity.kind === "human_control") return ["return_control", "stop"];
  if (activity.kind === "recovering") return ["continue", "start_over", "stop"];
  if (activity.kind === "awaiting_confirmation") return ["approve", "reject", "send_message", "change_conversation", "change_model", ...(viewerReady ? ["take_control"] : []), "stop"];
  return [
    ...(modelReady ? ["send_message", "change_model"] : []),
    ...(!modelReady ? ["reconnect_model"] : []),
    "change_conversation",
    ...(viewerReady ? ["take_control"] : []),
    "stop",
  ];
}

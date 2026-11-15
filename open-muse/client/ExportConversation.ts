import type { Conversation, Message } from "./api";
import type { TraceTurn } from "./trace";

function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function escapeMarkdown(text: string): string {
  return text.replace(/^(#{1,6} |---|\*\*\*|___|```)/gm, "\\$1");
}

function turnStepsSummary(turn: TraceTurn): string {
  if (!turn.steps.length) return "";
  return turn.steps.map((step) => {
    const mark = step.state === "completed" ? "done" : step.state === "failed" ? "fail" : step.state === "running" ? "run" : "skip";
    return "  " + mark + " " + (step.label || step.kind);
  }).join("\n");
}

function conversationToMarkdown(conversation: Conversation, turns: TraceTurn[]): string {
  const lines: string[] = [];
  const byTurn = new Map(
    turns.filter((t) => t.conversationId === conversation.id).map((t) => [t.turnId, t])
  );
  lines.push("# Conversation export");
  lines.push("**Model:** " + conversation.modelId + "  ");
  lines.push("**Exported:** " + new Date().toLocaleString() + "  ");
  lines.push("**Messages:** " + String(conversation.messages.length));
  lines.push("", "---", "");
  for (const msg of conversation.messages) {
    const role = msg.role === "user" ? "**You**" : "**OpenMuse**";
    lines.push("### " + role + " \u00b7 " + formatTimestamp(msg.createdAt));
    lines.push("", escapeMarkdown(msg.text.trim()), "");
    if (msg.role === "user" && msg.turnId) {
      const turn = byTurn.get(msg.turnId);
      if (turn && turn.steps.length) {
        const s = turn.steps.length;
        lines.push("<details><summary>Run details \u00b7 " + s + " step" + (s === 1 ? "" : "s") + "</summary>");
        lines.push("", "```", turnStepsSummary(turn), "```", "", "</details>", "");
      }
    }
    lines.push("---", "");
  }
  return lines.join("\n");
}

function conversationToJson(conversation: Conversation, turns: TraceTurn[]): string {
  return JSON.stringify({
    exportedAt: new Date().toISOString(),
    conversationId: conversation.id,
    modelId: conversation.modelId,
    providerId: conversation.providerId,
    messages: conversation.messages.map((m: Message) => ({
      id: m.id, role: m.role, text: m.text, createdAt: m.createdAt, turnId: m.turnId,
    })),
    turns: turns
      .filter((t) => t.conversationId === conversation.id)
      .map((t) => ({
        turnId: t.turnId, state: t.state,
        steps: t.steps.map((s) => ({ id: s.id, kind: s.kind, label: s.label, state: s.state, error: s.error })),
      })),
  }, null, 2);
}

function downloadFile(content: string, filename: string, mime: string): void {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function safeFilename(modelId: string): string {
  return "openmuse-" + new Date().toISOString().slice(0, 10) + "-" + modelId.replace(/[^a-z0-9]/gi, "-").toLowerCase();
}

export function exportAsMarkdown(conversation: Conversation, turns: TraceTurn[]): void {
  downloadFile(conversationToMarkdown(conversation, turns), safeFilename(conversation.modelId) + ".md", "text/markdown");
}

export function exportAsJson(conversation: Conversation, turns: TraceTurn[]): void {
  downloadFile(conversationToJson(conversation, turns), safeFilename(conversation.modelId) + ".json", "application/json");
}

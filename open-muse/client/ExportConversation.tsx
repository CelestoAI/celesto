import type { Conversation, Message } from "./api";
import type { TraceTurn } from "./trace";

function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function turnStepsSummary(turn: TraceTurn): string {
  if (!turn.steps.length) return "";
  const lines = turn.steps.map((step) => {
    const label = step.label ?? step.tool;
    const state = step.state === "completed" ? "✓" : step.state === "failed" ? "✗" : "·";
    return `  ${state} ${label}`;
  });
  return `\n\`\`\`\n${lines.join("\n")}\n\`\`\``;
}

function conversationToMarkdown(
  conversation: Conversation,
  turns: TraceTurn[],
): string {
  const lines: string[] = [];
  const traceByTurn = new Map(turns.map((turn) => [turn.turnId, turn]));

  lines.push(`# Conversation export`);
  lines.push(`**Model:** ${conversation.modelId}  `);
  lines.push(`**Exported:** ${new Date().toLocaleString()}  `);
  lines.push(`**Messages:** ${conversation.messages.length}`);
  lines.push("");
  lines.push("---");
  lines.push("");

  for (const message of conversation.messages) {
    const role = message.role === "user" ? "**You**" : "**OpenMuse**";
    const ts = formatTimestamp(message.createdAt);
    lines.push(`### ${role} · ${ts}`);
    lines.push("");
    lines.push(message.text.trim());
    lines.push("");

    if (message.role === "user" && message.turnId) {
      const turn = traceByTurn.get(message.turnId);
      if (turn && turn.steps.length) {
        lines.push(`<details><summary>Run details · ${turn.steps.length} step${turn.steps.length === 1 ? "" : "s"}</summary>`);
        lines.push("");
        lines.push(turnStepsSummary(turn));
        lines.push("");
        lines.push("</details>");
        lines.push("");
      }
    }

    lines.push("---");
    lines.push("");
  }

  return lines.join("\n");
}

function conversationToJson(
  conversation: Conversation,
  turns: TraceTurn[],
): string {
  return JSON.stringify(
    {
      exportedAt: new Date().toISOString(),
      conversationId: conversation.id,
      modelId: conversation.modelId,
      providerId: conversation.providerId,
      messages: conversation.messages.map((m: Message) => ({
        id: m.id,
        role: m.role,
        text: m.text,
        createdAt: m.createdAt,
        turnId: m.turnId,
      })),
      turns: turns.map((turn) => ({
        turnId: turn.turnId,
        state: turn.state,
        steps: turn.steps.map((step) => ({
          id: step.id,
          tool: step.tool,
          label: step.label,
          state: step.state,
          error: step.error,
        })),
      })),
    },
    null,
    2,
  );
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
  const date = new Date().toISOString().slice(0, 10);
  return `openmuse-${date}-${modelId.replace(/[^a-z0-9]/gi, "-").toLowerCase()}`;
}

export function exportAsMarkdown(conversation: Conversation, turns: TraceTurn[]): void {
  const content = conversationToMarkdown(conversation, turns);
  downloadFile(content, `${safeFilename(conversation.modelId)}.md`, "text/markdown");
}

export function exportAsJson(conversation: Conversation, turns: TraceTurn[]): void {
  const content = conversationToJson(conversation, turns);
  downloadFile(content, `${safeFilename(conversation.modelId)}.json`, "application/json");
}
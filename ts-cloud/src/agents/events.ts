/**
 * The run event stream.
 *
 * A run is an append-only log, and streaming is tailing it. The wire format is
 * Server-Sent Events and the event names are a versioned, closed set:
 *
 * `run.started`, `message.delta`, `message.completed`, `tool.call`,
 * `tool.result`, `usage`, `run.completed`, `run.failed`.
 *
 * **Unknown event names are ignored.** That is the forward-compatibility
 * contract: the server may add an event tomorrow and today's SDK must not
 * break on it. {@link toRunEvent} returns `undefined` for anything it does not
 * know, and {@link parseRunEvents} drops those frames.
 *
 * Every frame except `message.delta` carries an `id:` — the event's sequence
 * number. Deltas are not stored, so they are not positions you can resume
 * from, and their `seq` is `null`.
 */

import { DecimalString, RunStatus, RunUsage } from "./types";

/** The event contract this SDK was written against. */
export const EVENTS_VERSION = "1";

/** Response header naming the server's event contract version. */
export const EVENTS_VERSION_HEADER = "X-Celesto-Events-Version";

/** Every event name this SDK understands. */
export const KNOWN_EVENTS = [
  "run.started",
  "message.delta",
  "message.completed",
  "tool.call",
  "tool.result",
  "usage",
  "run.completed",
  "run.failed",
] as const;

export type RunEventName = (typeof KNOWN_EVENTS)[number];

const KNOWN_EVENT_SET = new Set<string>(KNOWN_EVENTS);

/** One raw Server-Sent Events frame, before it is understood. */
export interface SseFrame {
  event?: string;
  data: string;
  id?: string;
}

export interface RunStartedData {
  runId: string;
  agentId: string;
  agentVersionId: string;
  sessionId: string;
  endUserId: string;
  model: string;
  createdAt: string;
}

export interface MessageData {
  text: string | null;
  turn: number | null;
}

export interface ToolCallData {
  callId: string | null;
  name: string | null;
  args: unknown;
  turn: number | null;
}

export interface ToolResultData {
  callId: string | null;
  name: string | null;
  turn: number | null;
  /** Present when the tool succeeded. */
  result?: unknown;
  /** Present instead of `result` when the tool failed. */
  error?: unknown;
}

export interface UsageData extends RunUsage {
  turn: number | null;
  model: string | null;
}

export interface RunCompletedData {
  runId: string;
  status: RunStatus;
  output: string | null;
  turnCount: number | null;
  usage: RunUsage;
}

export interface RunFailedData {
  runId: string;
  status: RunStatus;
  errorCode: string | null;
  error: string | null;
  turnCount: number | null;
  usage: RunUsage;
}

interface BaseEvent<Name extends RunEventName, Data> {
  name: Name;
  /** Position in the run's log, or `null` for unstored `message.delta`. */
  seq: number | null;
  data: Data;
}

/** One thing that happened during a run. Switch on `name`. */
export type RunEvent =
  | BaseEvent<"run.started", RunStartedData>
  | BaseEvent<"message.delta", MessageData>
  | BaseEvent<"message.completed", MessageData>
  | BaseEvent<"tool.call", ToolCallData>
  | BaseEvent<"tool.result", ToolResultData>
  | BaseEvent<"usage", UsageData>
  | BaseEvent<"run.completed", RunCompletedData>
  | BaseEvent<"run.failed", RunFailedData>;

const asRecord = (value: unknown): Record<string, unknown> =>
  value && typeof value === "object" ? (value as Record<string, unknown>) : {};

const str = (value: unknown): string | null => (typeof value === "string" ? value : null);

const num = (value: unknown): number | null => (typeof value === "number" ? value : null);

const int = (value: unknown): number => (typeof value === "number" ? value : 0);

/** Money stays a string. Never `parseFloat` these. */
const money = (value: unknown): DecimalString =>
  typeof value === "string" ? value : "0.000000";

const toUsage = (value: unknown): RunUsage => {
  const raw = asRecord(value);
  return {
    inputTokens: int(raw.input_tokens),
    outputTokens: int(raw.output_tokens),
    totalTokens: int(raw.total_tokens),
    costUsd: money(raw.cost_usd),
  };
};

const toToolResultData = (raw: Record<string, unknown>): ToolResultData => {
  const data: ToolResultData = {
    callId: str(raw.call_id),
    name: str(raw.name),
    turn: num(raw.turn),
  };
  if ("error" in raw) {
    data.error = raw.error;
  } else {
    data.result = raw.result;
  }
  return data;
};

/**
 * Turn one raw frame into a run event, or `undefined` to ignore it.
 *
 * Returns `undefined` for comments, keep-alives, and — deliberately — event
 * names this SDK does not know.
 */
export const toRunEvent = (frame: SseFrame): RunEvent | undefined => {
  const name = frame.event;
  if (!name || !KNOWN_EVENT_SET.has(name)) return undefined;

  let parsed: unknown;
  try {
    parsed = frame.data ? JSON.parse(frame.data) : {};
  } catch {
    return undefined;
  }
  const raw = asRecord(parsed);
  const seq = frame.id !== undefined && frame.id !== "" ? Number(frame.id) : NaN;
  const position = Number.isFinite(seq) ? seq : null;

  switch (name as RunEventName) {
    case "run.started":
      return {
        name: "run.started",
        seq: position,
        data: {
          runId: str(raw.run_id) ?? "",
          agentId: str(raw.agent_id) ?? "",
          agentVersionId: str(raw.agent_version_id) ?? "",
          sessionId: str(raw.session_id) ?? "",
          endUserId: str(raw.end_user_id) ?? "",
          model: str(raw.model) ?? "",
          createdAt: str(raw.created_at) ?? "",
        },
      };
    case "message.delta":
      return {
        name: "message.delta",
        seq: position,
        data: { text: str(raw.text), turn: num(raw.turn) },
      };
    case "message.completed":
      return {
        name: "message.completed",
        seq: position,
        data: { text: str(raw.text), turn: num(raw.turn) },
      };
    case "tool.call":
      return {
        name: "tool.call",
        seq: position,
        data: {
          callId: str(raw.call_id),
          name: str(raw.name),
          args: raw.args,
          turn: num(raw.turn),
        },
      };
    case "tool.result":
      return { name: "tool.result", seq: position, data: toToolResultData(raw) };
    case "usage":
      return {
        name: "usage",
        seq: position,
        data: {
          turn: num(raw.turn),
          model: str(raw.model),
          inputTokens: int(raw.input_tokens),
          outputTokens: int(raw.output_tokens),
          totalTokens: int(raw.total_tokens),
          costUsd: money(raw.cost_usd),
        },
      };
    case "run.completed":
      return {
        name: "run.completed",
        seq: position,
        data: {
          runId: str(raw.run_id) ?? "",
          status: (str(raw.status) ?? "completed") as RunStatus,
          output: str(raw.output),
          turnCount: num(raw.turn_count),
          usage: toUsage(raw.usage),
        },
      };
    case "run.failed":
      return {
        name: "run.failed",
        seq: position,
        data: {
          runId: str(raw.run_id) ?? "",
          status: (str(raw.status) ?? "failed") as RunStatus,
          errorCode: str(raw.error_code),
          error: str(raw.error),
          turnCount: num(raw.turn_count),
          usage: toUsage(raw.usage),
        },
      };
    default:
      return undefined;
  }
};

/** True for `run.completed` and `run.failed`: the run is settled. */
export const isTerminal = (event: RunEvent): boolean =>
  event.name === "run.completed" || event.name === "run.failed";

/** The text an event carries, or `""`. */
export const eventText = (event: RunEvent): string => {
  switch (event.name) {
    case "message.delta":
    case "message.completed":
      return event.data.text ?? "";
    case "run.completed":
      return event.data.output ?? "";
    default:
      return "";
  }
};

/**
 * Feeds SSE text in, gets frames out. Chunk boundaries land anywhere, so the
 * decoder holds a buffer between pushes.
 */
export class SseDecoder {
  private buffer = "";

  push(chunk: string): SseFrame[] {
    this.buffer += chunk;
    const frames: SseFrame[] = [];

    let boundary = this.findBoundary();
    while (boundary) {
      const block = this.buffer.slice(0, boundary.index);
      this.buffer = this.buffer.slice(boundary.index + boundary.length);
      const frame = parseFrame(block);
      if (frame) frames.push(frame);
      boundary = this.findBoundary();
    }
    return frames;
  }

  /** Anything left in the buffer when the stream ends. */
  flush(): SseFrame[] {
    const block = this.buffer;
    this.buffer = "";
    const frame = parseFrame(block);
    return frame ? [frame] : [];
  }

  private findBoundary(): { index: number; length: number } | undefined {
    const lf = this.buffer.indexOf("\n\n");
    const crlf = this.buffer.indexOf("\r\n\r\n");
    if (crlf !== -1 && (lf === -1 || crlf < lf)) return { index: crlf, length: 4 };
    if (lf !== -1) return { index: lf, length: 2 };
    return undefined;
  }
}

const parseFrame = (block: string): SseFrame | undefined => {
  let event: string | undefined;
  let id: string | undefined;
  const dataLines: string[] = [];
  let sawField = false;

  for (const rawLine of block.split("\n")) {
    const line = rawLine.replace(/\r$/, "");
    if (line === "" || line.startsWith(":")) continue;

    const separator = line.indexOf(":");
    const field = separator === -1 ? line : line.slice(0, separator);
    let value = separator === -1 ? "" : line.slice(separator + 1);
    if (value.startsWith(" ")) value = value.slice(1);

    if (field === "event") {
      event = value;
      sawField = true;
    } else if (field === "data") {
      dataLines.push(value);
      sawField = true;
    } else if (field === "id") {
      id = value;
      sawField = true;
    }
    // "retry" and unknown fields are ignored, per the SSE spec.
  }

  if (!sawField) return undefined;
  const frame: SseFrame = { data: dataLines.join("\n") };
  if (event !== undefined) frame.event = event;
  if (id !== undefined) frame.id = id;
  return frame;
};

/** Parse a whole SSE body into frames. */
export const parseSseFrames = (body: string): SseFrame[] => {
  const decoder = new SseDecoder();
  return [...decoder.push(body), ...decoder.flush()];
};

/** Parse a whole SSE body into run events, ignoring unknown event names. */
export const parseRunEvents = (body: string): RunEvent[] => {
  const events: RunEvent[] = [];
  for (const frame of parseSseFrames(body)) {
    const event = toRunEvent(frame);
    if (event) events.push(event);
  }
  return events;
};

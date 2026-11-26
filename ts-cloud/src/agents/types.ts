/**
 * Types for managed agents: agents, runs, sessions, and end users.
 *
 * Money is a `DecimalString`, never a `number`. See the note on that type.
 */

/**
 * An amount of money, as a fixed-scale decimal string such as `"0.000450"`.
 *
 * A single generation can cost millionths of a dollar, and a JavaScript
 * `number` cannot hold those exactly — `0.1 + 0.2` is the classic example, and
 * a month of agent runs is that mistake ten thousand times over. The API sends
 * these as strings and this SDK keeps them as strings. Compare and display
 * them as-is, and if you must do arithmetic, use a decimal library
 * (`decimal.js`, `big.js`) rather than `parseFloat`.
 */
export type DecimalString = string;

/** Lets a known set autocomplete without closing it to future values. */
type Open<T extends string> = T | (string & {});

/** The lifecycle of an agent. */
export type AgentStatus = Open<"active" | "archived">;

/** Where a run ended up. */
export type RunStatus = Open<"queued" | "running" | "completed" | "failed">;

export type ReasoningEffort = "minimal" | "low" | "medium" | "high";
export type Verbosity = "low" | "medium" | "high";

/**
 * Generation settings an agent may carry.
 *
 * This is a closed set: anything else is refused by the API with a 422, so
 * these are the only keys TypeScript will accept, and the SDK checks again
 * before sending.
 */
export interface AgentConfig {
  temperature?: number;
  topP?: number;
  maxTokens?: number;
  maxOutputTokens?: number;
  frequencyPenalty?: number;
  presencePenalty?: number;
  seed?: number;
  stop?: string | string[];
  reasoningEffort?: ReasoningEffort;
  verbosity?: Verbosity;
  maxTurns?: number;
}

/** A named, versioned agent definition. */
export interface Agent {
  id: string;
  object: string;
  name: string;
  description: string | null;
  model: string;
  instructions: string | null;
  config: AgentConfig | null;
  version: number;
  currentVersionId: string;
  projectId: string;
  organizationId: string;
  status: AgentStatus;
  createdAt: string;
  updatedAt: string;
}

/** One immutable snapshot of an agent definition. */
export interface AgentVersion {
  id: string;
  object: string;
  agentId: string;
  version: number;
  name: string;
  description: string | null;
  model: string;
  instructions: string | null;
  config: AgentConfig | null;
  createdAt: string;
}

/**
 * One page of results.
 *
 * There is no total count anywhere in this API. `hasMore` is how you know
 * whether to ask for another page.
 */
export interface Page<T> {
  data: T[];
  hasMore: boolean;
}

/** What archiving an agent returns. */
export interface ArchivedAgent {
  id: string;
  status: AgentStatus;
}

export interface CreateAgentParams {
  /** Display name, 1-255 characters. */
  name: string;
  /** Model to run, such as `"openai/gpt-5.4-mini"`. Pinned per version. */
  model: string;
  /** The system prompt. */
  instructions?: string;
  /** Free text for your own dashboard, up to 1000 characters. */
  description?: string;
  /** Generation settings. Only the keys of {@link AgentConfig} are accepted. */
  config?: AgentConfig;
  /** Project to scope the agent to. Defaults to your default project. */
  projectId?: string;
}

/** A full replacement of an agent's definition, which cuts a new version. */
export type UpdateAgentParams = Omit<CreateAgentParams, "projectId">;

export interface ListAgentsParams {
  projectId?: string;
  includeArchived?: boolean;
  /** Page size, 1-100. */
  limit?: number;
  offset?: number;
}

export interface ListAgentVersionsParams {
  /** Page size, 1-100. */
  limit?: number;
  offset?: number;
}

/** Tokens and money spent by a run or a single generation. */
export interface RunUsage {
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  costUsd: DecimalString;
}

/** A run of an agent, on behalf of one end user. */
export interface Run {
  runId: string;
  object: string;
  status: RunStatus;
  errorCode: string | null;
  error: string | null;
  output: string | null;
  usage: RunUsage;
  agentId: string;
  agentVersionId: string;
  sessionId: string;
  endUserId: string;
  turnCount: number | null;
  createdAt: string;
  startedAt: string | null;
  endedAt: string | null;
}

export interface CreateRunParams {
  /** What the end user said. */
  input: string;
  /**
   * Your own identifier for the person this run acts for, such as
   * `"usr_8837"`. Celesto stores it as you send it and never parses it.
   */
  endUserId: string;
  /** Continue an existing conversation. Omit to start a new one. */
  sessionId?: string;
  /** Stop the agent after this many turns, 1-100. */
  maxTurns?: number;
  /**
   * Send the same key to retry safely: a replay returns the stored run
   * instead of running the agent again.
   */
  idempotencyKey?: string;
  /**
   * How many times to retry when the session is busy. Sessions run one at a
   * time, so a second run on the same session is refused until the first
   * settles. An idempotency key is generated for you when you ask for
   * retries, so a retry cannot charge the end user twice.
   */
  maxRetries?: number;
}

/** One stored event, as returned by the events endpoint. */
export interface StoredRunEvent {
  seq: number;
  event: string;
  data: Record<string, unknown>;
}

/**
 * One page of stored run events.
 *
 * This endpoint reports no `hasMore`: page with `afterSeq` set to the last
 * `seq` you saw, and stop when a page comes back short.
 */
export interface RunEventsPage {
  data: StoredRunEvent[];
  eventsVersion: string;
}

export interface ListRunEventsParams {
  /** Return events after this sequence number. */
  afterSeq?: number;
  /** Page size, 1-500. */
  limit?: number;
}

/** A conversation between one end user and one agent. */
export interface Session {
  id: string;
  object: string;
  agentId: string | null;
  endUserId: string;
  status: string;
  messageCount: number;
  lastMessageAt: string | null;
  createdAt: string;
}

/** One entry in a session transcript. */
export interface SessionMessage {
  seq: number;
  role: string | null;
  item: Record<string, unknown>;
  createdAt: string;
}

/** A session together with a page of its messages. */
export interface SessionTranscript {
  session: Session;
  messages: SessionMessage[];
}

export interface ListSessionsParams {
  /** Your own identifier for the end user. */
  endUserId: string;
  /** Page size, 1-100. */
  limit?: number;
  offset?: number;
}

export interface GetSessionParams {
  /** How many messages to return, 1-200. */
  limit?: number;
  /** Return messages before this sequence number. */
  beforeSeq?: number;
}

/**
 * Spend and cap for one end user, in the current 30-day window.
 *
 * The window is anchored to that user's first activity, not the calendar
 * month. A `capUsd` of `null` means no cap.
 */
export interface EndUserBudget {
  capUsd: DecimalString | null;
  source: string;
  windowStart: string;
  windowResetsAt: string;
  spentUsd: DecimalString;
  remainingUsd: DecimalString | null;
}

/** One of your users, addressed by your own identifier for them. */
export interface EndUser {
  endUserId: string;
  object: string;
  firstActivityAt: string;
  budget: EndUserBudget;
  metadata: Record<string, unknown> | null;
  createdAt: string;
}

export interface UpdateEndUserParams {
  /**
   * Spend cap for the rolling 30-day window. A decimal string, never a
   * `number` — `0.1 + 0.2` would go out as `"0.30000000000000004"`, and the
   * API refuses it. `null` clears the override and falls back to the
   * organization default. Omit the field to leave it alone.
   */
  budgetCapUsd?: DecimalString | null;
  /** Free-form JSON of your own. `null` clears it. */
  metadata?: Record<string, unknown> | null;
}

/** Organization-wide defaults for managed agents. */
export interface RuntimeSettings {
  organizationId: string;
  defaultEndUserBudgetUsd: DecimalString | null;
}

export interface UpdateRuntimeSettingsParams {
  /**
   * The budget every end user starts with, as a decimal string. `null`
   * removes the default.
   */
  defaultEndUserBudgetUsd?: DecimalString | null;
}

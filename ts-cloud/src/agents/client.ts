/**
 * Managed agents: run your agents for your end users.
 *
 * You define an agent once — a name, a model, instructions — and then run it
 * on behalf of *your* users. Every run names the end user it acts for, using
 * your own identifier for them (`"usr_8837"`, `"alice@acme.com"`). Celesto
 * keeps that user's spend, budget, and transcript together, so "what has this
 * user spent this month?" is one call.
 */

import { buildRequestContext, ClientConfig, RequestOverrides } from "../core/config";
import { request, requestStream } from "../core/http";
import { ConfigKeyNotAllowedError, SessionBusyError, toManagedAgentError } from "./errors";
import { RunEvent, SseDecoder, toRunEvent } from "./events";
import {
  Agent,
  AgentConfig,
  AgentVersion,
  ArchivedAgent,
  CreateAgentParams,
  CreateRunParams,
  EndUser,
  EndUserBudget,
  GetSessionParams,
  ListAgentVersionsParams,
  ListAgentsParams,
  ListRunEventsParams,
  ListSessionsParams,
  Page,
  Run,
  RunEventsPage,
  RunUsage,
  RuntimeSettings,
  Session,
  SessionMessage,
  SessionTranscript,
  StoredRunEvent,
  UpdateAgentParams,
  UpdateEndUserParams,
  UpdateRuntimeSettingsParams,
} from "./types";

const runtimePath = (path: string): string => `/v1${path}`;

const pickOverrides = (options?: RequestOverrides): RequestOverrides => ({
  headers: options?.headers,
  signal: options?.signal,
});

const DEFAULT_RETRY_BACKOFF_MS = 1_000;

/**
 * Every generation setting an agent may carry, and its name on the wire.
 *
 * Anything outside this set is a 422, so the SDK refuses it locally first —
 * a typo should not cost a round trip.
 */
const CONFIG_KEYS = {
  temperature: "temperature",
  topP: "top_p",
  maxTokens: "max_tokens",
  maxOutputTokens: "max_output_tokens",
  frequencyPenalty: "frequency_penalty",
  presencePenalty: "presence_penalty",
  seed: "seed",
  stop: "stop",
  reasoningEffort: "reasoning_effort",
  verbosity: "verbosity",
  maxTurns: "max_turns",
} as const satisfies Record<keyof AgentConfig, string>;

/** The keys an agent `config` may contain. */
export const ALLOWED_CONFIG_KEYS = Object.keys(CONFIG_KEYS) as (keyof AgentConfig)[];

const WIRE_TO_CONFIG_KEY = new Map<string, keyof AgentConfig>(
  (Object.entries(CONFIG_KEYS) as [keyof AgentConfig, string][]).map(([key, wire]) => [
    wire,
    key,
  ]),
);

const toConfigWire = (config: AgentConfig | undefined): Record<string, unknown> | undefined => {
  if (!config) return undefined;
  const wire: Record<string, unknown> = {};
  const unknown: string[] = [];
  for (const [key, value] of Object.entries(config)) {
    if (value === undefined) continue;
    const wireKey = CONFIG_KEYS[key as keyof AgentConfig];
    if (!wireKey) {
      unknown.push(key);
      continue;
    }
    wire[wireKey] = value;
  }
  if (unknown.length > 0) {
    throw new ConfigKeyNotAllowedError(
      `Agent config does not accept ${unknown.join(", ")}. It accepts only: ${ALLOWED_CONFIG_KEYS.join(", ")}.`,
      422,
      undefined,
      { code: "config_key_not_allowed" },
    );
  }
  return wire;
};

const toConfig = (wire: unknown): AgentConfig | null => {
  if (!wire || typeof wire !== "object") return null;
  const config: Record<string, unknown> = {};
  for (const [wireKey, value] of Object.entries(wire as Record<string, unknown>)) {
    const key = WIRE_TO_CONFIG_KEY.get(wireKey);
    // A key we do not know is kept as it arrived rather than dropped: the
    // server is the authority on what an agent carries.
    config[key ?? wireKey] = value;
  }
  return config as AgentConfig;
};

interface AgentWire {
  id: string;
  object?: string;
  name: string;
  description?: string | null;
  model: string;
  instructions?: string | null;
  config?: Record<string, unknown> | null;
  version: number;
  current_version_id: string;
  project_id: string;
  organization_id: string;
  status: string;
  created_at: string;
  updated_at: string;
}

interface AgentVersionWire {
  id: string;
  object?: string;
  agent_id: string;
  version: number;
  name: string;
  description?: string | null;
  model: string;
  instructions?: string | null;
  config?: Record<string, unknown> | null;
  created_at: string;
}

interface PageWire<T> {
  data: T[];
  has_more?: boolean;
}

interface RunUsageWire {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_usd: string;
}

interface RunWire {
  run_id: string;
  object?: string;
  status: string;
  error_code?: string | null;
  error?: string | null;
  output?: string | null;
  usage: RunUsageWire;
  agent_id: string;
  agent_version_id: string;
  session_id: string;
  end_user_id: string;
  turn_count?: number | null;
  created_at: string;
  started_at?: string | null;
  ended_at?: string | null;
}

interface RunEventsPageWire {
  data: StoredRunEvent[];
  events_version: string;
}

interface SessionWire {
  id: string;
  object?: string;
  agent_id?: string | null;
  end_user_id: string;
  status: string;
  message_count: number;
  last_message_at?: string | null;
  created_at: string;
}

interface SessionMessageWire {
  seq: number;
  role?: string | null;
  item: Record<string, unknown>;
  created_at: string;
}

interface SessionTranscriptWire {
  session: SessionWire;
  messages: SessionMessageWire[];
}

interface EndUserWire {
  end_user_id: string;
  object?: string;
  first_activity_at: string;
  budget: {
    cap_usd?: string | null;
    source: string;
    window_start: string;
    window_resets_at: string;
    spent_usd: string;
    remaining_usd?: string | null;
  };
  metadata?: Record<string, unknown> | null;
  created_at: string;
}

interface RuntimeSettingsWire {
  organization_id: string;
  default_end_user_budget_usd?: string | null;
}

const toAgent = (wire: AgentWire): Agent => ({
  id: wire.id,
  object: wire.object ?? "agent",
  name: wire.name,
  description: wire.description ?? null,
  model: wire.model,
  instructions: wire.instructions ?? null,
  config: toConfig(wire.config),
  version: wire.version,
  currentVersionId: wire.current_version_id,
  projectId: wire.project_id,
  organizationId: wire.organization_id,
  status: wire.status,
  createdAt: wire.created_at,
  updatedAt: wire.updated_at,
});

const toAgentVersion = (wire: AgentVersionWire): AgentVersion => ({
  id: wire.id,
  object: wire.object ?? "agent_version",
  agentId: wire.agent_id,
  version: wire.version,
  name: wire.name,
  description: wire.description ?? null,
  model: wire.model,
  instructions: wire.instructions ?? null,
  config: toConfig(wire.config),
  createdAt: wire.created_at,
});

const toUsage = (wire: RunUsageWire): RunUsage => ({
  inputTokens: wire.input_tokens,
  outputTokens: wire.output_tokens,
  totalTokens: wire.total_tokens,
  // Money stays a string. Never parseFloat this.
  costUsd: wire.cost_usd,
});

const toRun = (wire: RunWire): Run => ({
  runId: wire.run_id,
  object: wire.object ?? "run",
  status: wire.status,
  errorCode: wire.error_code ?? null,
  error: wire.error ?? null,
  output: wire.output ?? null,
  usage: toUsage(wire.usage),
  agentId: wire.agent_id,
  agentVersionId: wire.agent_version_id,
  sessionId: wire.session_id,
  endUserId: wire.end_user_id,
  turnCount: wire.turn_count ?? null,
  createdAt: wire.created_at,
  startedAt: wire.started_at ?? null,
  endedAt: wire.ended_at ?? null,
});

const toSession = (wire: SessionWire): Session => ({
  id: wire.id,
  object: wire.object ?? "session",
  agentId: wire.agent_id ?? null,
  endUserId: wire.end_user_id,
  status: wire.status,
  messageCount: wire.message_count,
  lastMessageAt: wire.last_message_at ?? null,
  createdAt: wire.created_at,
});

const toSessionMessage = (wire: SessionMessageWire): SessionMessage => ({
  seq: wire.seq,
  role: wire.role ?? null,
  item: wire.item,
  createdAt: wire.created_at,
});

const toBudget = (wire: EndUserWire["budget"]): EndUserBudget => ({
  capUsd: wire.cap_usd ?? null,
  source: wire.source,
  windowStart: wire.window_start,
  windowResetsAt: wire.window_resets_at,
  spentUsd: wire.spent_usd,
  remainingUsd: wire.remaining_usd ?? null,
});

const toEndUser = (wire: EndUserWire): EndUser => ({
  endUserId: wire.end_user_id,
  object: wire.object ?? "end_user",
  firstActivityAt: wire.first_activity_at,
  budget: toBudget(wire.budget),
  metadata: wire.metadata ?? null,
  createdAt: wire.created_at,
});

const toRuntimeSettings = (wire: RuntimeSettingsWire): RuntimeSettings => ({
  organizationId: wire.organization_id,
  defaultEndUserBudgetUsd: wire.default_end_user_budget_usd ?? null,
});

const toPage = <W, T>(wire: PageWire<W>, map: (item: W) => T): Page<T> => ({
  data: (wire.data ?? []).map(map),
  hasMore: wire.has_more ?? false,
});

/**
 * Amounts go out as strings so a float never rounds someone's budget.
 *
 * The types already say `DecimalString`, but types are advice at runtime: plain
 * JavaScript callers, `any`, and JSON parsed from elsewhere all reach here with
 * a `number`. `String(0.1 + 0.2)` is `"0.30000000000000004"` and `String(1e-7)`
 * is `"1e-7"` — the API refuses both, so throwing here names the fix instead of
 * surfacing a 422 from three layers down. The message does not echo the number
 * back, because its repr is the caller's rounding error.
 */
const MONEY_PATTERN = /^\d{1,8}(\.\d{1,6})?$/;

const toMoneyString = (value: string | number): string => {
  if (typeof value === "number") {
    throw new TypeError(
      `Budget amounts cannot be a number (${value}): a JavaScript number cannot hold ` +
        `these amounts exactly. Pass a decimal string instead — "5.00", not 5.0.`,
    );
  }
  const text = value.trim();
  // Refusing a number and then waving through "1e-7" — the exact form the API
  // rejects — would leave the front door open on a locked window. The pattern
  // mirrors the server's, so a refusal here is the refusal the API would make.
  if (!MONEY_PATTERN.test(text)) {
    throw new TypeError(
      `"${value}" is not a valid amount. Use a plain decimal amount with at most ` +
        `8 digits before the point and 6 after, like "5.00" — no sign, no exponent, ` +
        `no currency symbol.`,
    );
  }
  return text;
};

const sleep = (ms: number): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, ms));

const newIdempotencyKey = (): string => {
  const uuid = globalThis.crypto?.randomUUID?.();
  return uuid ?? `idem_${Date.now().toString(36)}${Math.random().toString(36).slice(2)}`;
};

abstract class BaseClient {
  protected readonly config: ClientConfig;

  constructor(config: ClientConfig) {
    this.config = config;
  }

  /** Every call goes through here, so refusals arrive already typed. */
  protected async call<T>(
    options: Parameters<typeof request>[1],
  ): Promise<T> {
    try {
      return await request<T>(buildRequestContext(this.config), options);
    } catch (error) {
      throw toManagedAgentError(error);
    }
  }
}

/**
 * Create and version the agents your end users run.
 *
 * An agent is a named pointer at an immutable definition. Every update cuts a
 * new version and moves the pointer; runs pin the version they started with,
 * so a change never rewrites history. Rolling back moves the pointer and cuts
 * nothing.
 */
export class AgentsClient extends BaseClient {
  /** Create an agent, at version 1. */
  async create(params: CreateAgentParams, options?: RequestOverrides): Promise<Agent> {
    const wire = await this.call<AgentWire>({
      method: "POST",
      path: runtimePath("/agents"),
      body: {
        name: params.name,
        model: params.model,
        instructions: params.instructions,
        description: params.description,
        config: toConfigWire(params.config),
        project_id: params.projectId,
      },
      ...pickOverrides(options),
    });
    return toAgent(wire);
  }

  /** List one page of agents. Check `hasMore`; there is no total count. */
  async list(params: ListAgentsParams = {}, options?: RequestOverrides): Promise<Page<Agent>> {
    const wire = await this.call<PageWire<AgentWire>>({
      method: "GET",
      path: runtimePath("/agents"),
      query: {
        project_id: params.projectId,
        include_archived: params.includeArchived,
        limit: params.limit,
        offset: params.offset,
      },
      ...pickOverrides(options),
    });
    return toPage(wire, toAgent);
  }

  /** Yield every agent, fetching pages as you go. */
  async *listAll(
    params: Omit<ListAgentsParams, "offset"> = {},
    options?: RequestOverrides,
  ): AsyncGenerator<Agent> {
    const pageSize = params.limit ?? 50;
    let offset = 0;
    for (;;) {
      const page = await this.list({ ...params, limit: pageSize, offset }, options);
      yield* page.data;
      if (page.data.length === 0 || !page.hasMore) return;
      offset += page.data.length;
    }
  }

  /** Get an agent, at its current version. */
  async get(agentId: string, options?: RequestOverrides): Promise<Agent> {
    const wire = await this.call<AgentWire>({
      method: "GET",
      path: runtimePath(`/agents/${encodeURIComponent(agentId)}`),
      ...pickOverrides(options),
    });
    return toAgent(wire);
  }

  /**
   * Replace an agent's definition, which cuts a new version.
   *
   * This is a full replacement, not a patch: whatever you leave out is
   * cleared. Read the agent first if you only mean to change one field.
   */
  async update(
    agentId: string,
    params: UpdateAgentParams,
    options?: RequestOverrides,
  ): Promise<Agent> {
    const wire = await this.call<AgentWire>({
      method: "PUT",
      path: runtimePath(`/agents/${encodeURIComponent(agentId)}`),
      body: {
        name: params.name,
        model: params.model,
        instructions: params.instructions,
        description: params.description,
        config: toConfigWire(params.config),
      },
      ...pickOverrides(options),
    });
    return toAgent(wire);
  }

  /**
   * Archive an agent. Archived agents refuse new runs.
   *
   * Past runs, versions, and transcripts stay readable.
   */
  async archive(agentId: string, options?: RequestOverrides): Promise<ArchivedAgent> {
    const wire = await this.call<{ id: string; status: string }>({
      method: "DELETE",
      path: runtimePath(`/agents/${encodeURIComponent(agentId)}`),
      ...pickOverrides(options),
    });
    return { id: wire.id, status: wire.status };
  }

  /** List one page of an agent's versions. */
  async listVersions(
    agentId: string,
    params: ListAgentVersionsParams = {},
    options?: RequestOverrides,
  ): Promise<Page<AgentVersion>> {
    const wire = await this.call<PageWire<AgentVersionWire>>({
      method: "GET",
      path: runtimePath(`/agents/${encodeURIComponent(agentId)}/versions`),
      query: { limit: params.limit, offset: params.offset },
      ...pickOverrides(options),
    });
    return toPage(wire, toAgentVersion);
  }

  /** Yield every version of an agent, fetching pages as you go. */
  async *listAllVersions(
    agentId: string,
    params: Omit<ListAgentVersionsParams, "offset"> = {},
    options?: RequestOverrides,
  ): AsyncGenerator<AgentVersion> {
    const pageSize = params.limit ?? 50;
    let offset = 0;
    for (;;) {
      const page = await this.listVersions(agentId, { limit: pageSize, offset }, options);
      yield* page.data;
      if (page.data.length === 0 || !page.hasMore) return;
      offset += page.data.length;
    }
  }

  /** Get one version of an agent by its number. */
  async getVersion(
    agentId: string,
    versionNumber: number,
    options?: RequestOverrides,
  ): Promise<AgentVersion> {
    const wire = await this.call<AgentVersionWire>({
      method: "GET",
      path: runtimePath(`/agents/${encodeURIComponent(agentId)}/versions/${versionNumber}`),
      ...pickOverrides(options),
    });
    return toAgentVersion(wire);
  }

  /**
   * Roll back to an earlier version.
   *
   * This moves the agent's pointer; it does not cut a new version and nothing
   * is lost.
   */
  async activateVersion(
    agentId: string,
    versionNumber: number,
    options?: RequestOverrides,
  ): Promise<Agent> {
    const wire = await this.call<AgentWire>({
      method: "POST",
      path: runtimePath(
        `/agents/${encodeURIComponent(agentId)}/versions/${versionNumber}/activate`,
      ),
      ...pickOverrides(options),
    });
    return toAgent(wire);
  }
}

/**
 * Run an agent for one of your end users, and read what happened.
 *
 * Two ways to run, so the return type never depends on an argument:
 * `create()` resolves with the settled run, `stream()` yields events.
 */
export class RunsClient extends BaseClient {
  private runBody(params: CreateRunParams, stream: boolean): Record<string, unknown> {
    return {
      input: params.input,
      end_user_id: params.endUserId,
      session_id: params.sessionId,
      max_turns: params.maxTurns,
      stream,
    };
  }

  /** Retrying without a key can charge twice, so make one when retrying. */
  private idempotencyKey(params: CreateRunParams): string | undefined {
    if (params.idempotencyKey) return params.idempotencyKey;
    return (params.maxRetries ?? 0) > 0 ? newIdempotencyKey() : undefined;
  }

  /**
   * Run an agent and wait for the answer.
   *
   * @throws {@link BudgetExceededError} when the end user has spent their budget.
   * @throws {@link SessionBusyError} when another run holds the session.
   */
  async create(
    agentId: string,
    params: CreateRunParams,
    options?: RequestOverrides,
  ): Promise<Run> {
    const key = this.idempotencyKey(params);
    const maxRetries = params.maxRetries ?? 0;
    const headers = {
      ...(options?.headers ?? {}),
      ...(key ? { "Idempotency-Key": key } : {}),
    };

    for (let attempt = 0; ; attempt += 1) {
      try {
        const wire = await this.call<RunWire>({
          method: "POST",
          path: runtimePath(`/agents/${encodeURIComponent(agentId)}/runs`),
          body: this.runBody(params, false),
          headers,
          signal: options?.signal,
        });
        return toRun(wire);
      } catch (error) {
        if (!(error instanceof SessionBusyError) || attempt >= maxRetries) throw error;
        await sleep(
          error.retryAfter !== undefined ? error.retryAfter * 1000 : DEFAULT_RETRY_BACKOFF_MS,
        );
      }
    }
  }

  /**
   * Run an agent and watch it work.
   *
   * Yields events as the run happens: text as it is generated, each tool call
   * and its result, what each generation cost, and finally `run.completed` or
   * `run.failed`. Event names this SDK does not know are ignored, so a newer
   * server cannot break an older client.
   *
   * A failed run arrives as a `run.failed` event, not a thrown error —
   * including a run stopped mid-stream because the end user ran out of
   * budget. Errors are thrown for runs that never started.
   *
   * A replay of an idempotency key omits `message.delta`: partial text is
   * never stored, so there is nothing to replay.
   *
   * @example
   * ```ts
   * for await (const event of celesto.runs.stream(agent.id, {
   *   input: "Where is my order?",
   *   endUserId: "usr_8837",
   * })) {
   *   if (event.name === "message.delta") process.stdout.write(event.data.text ?? "");
   * }
   * ```
   */
  async *stream(
    agentId: string,
    params: CreateRunParams,
    options?: RequestOverrides,
  ): AsyncGenerator<RunEvent> {
    const key = this.idempotencyKey(params);
    const maxRetries = params.maxRetries ?? 0;
    const headers = {
      Accept: "text/event-stream",
      ...(options?.headers ?? {}),
      ...(key ? { "Idempotency-Key": key } : {}),
    };

    for (let attempt = 0; ; attempt += 1) {
      let response: Response;
      try {
        response = await requestStream(buildRequestContext(this.config), {
          method: "POST",
          path: runtimePath(`/agents/${encodeURIComponent(agentId)}/runs`),
          body: this.runBody(params, true),
          headers,
          signal: options?.signal,
        });
      } catch (error) {
        const typed = toManagedAgentError(error);
        if (!(typed instanceof SessionBusyError) || attempt >= maxRetries) throw typed;
        await sleep(
          typed.retryAfter !== undefined ? typed.retryAfter * 1000 : DEFAULT_RETRY_BACKOFF_MS,
        );
        continue;
      }

      yield* readEventStream(response);
      return;
    }
  }

  /** Get a run by id, settled or not. */
  async get(runId: string, options?: RequestOverrides): Promise<Run> {
    const wire = await this.call<RunWire>({
      method: "GET",
      path: runtimePath(`/runs/${encodeURIComponent(runId)}`),
      ...pickOverrides(options),
    });
    return toRun(wire);
  }

  /**
   * Read one page of a run's stored events.
   *
   * The same event contract as {@link stream}, read back after the fact,
   * minus `message.delta` — partial text is never stored.
   */
  async listEvents(
    runId: string,
    params: ListRunEventsParams = {},
    options?: RequestOverrides,
  ): Promise<RunEventsPage> {
    const wire = await this.call<RunEventsPageWire>({
      method: "GET",
      path: runtimePath(`/runs/${encodeURIComponent(runId)}/events`),
      query: { after_seq: params.afterSeq, limit: params.limit },
      ...pickOverrides(options),
    });
    return { data: wire.data ?? [], eventsVersion: wire.events_version };
  }

  /** Yield every stored event of a run, in order, fetching pages as you go. */
  async *listAllEvents(
    runId: string,
    params: ListRunEventsParams = {},
    options?: RequestOverrides,
  ): AsyncGenerator<StoredRunEvent> {
    const pageSize = params.limit ?? 100;
    let afterSeq = params.afterSeq ?? 0;
    for (;;) {
      const page = await this.listEvents(runId, { afterSeq, limit: pageSize }, options);
      yield* page.data;
      // This endpoint reports no `has_more`; a short page is the end.
      if (page.data.length < pageSize) return;
      const last = page.data[page.data.length - 1];
      if (!last) return;
      afterSeq = last.seq;
    }
  }
}

/**
 * The conversations your end users have had.
 *
 * A session holds one end user's transcript with one agent. Runs on the same
 * session share history; runs without a session get a fresh one.
 */
export class SessionsClient extends BaseClient {
  /** List one page of an end user's sessions. */
  async list(params: ListSessionsParams, options?: RequestOverrides): Promise<Page<Session>> {
    const wire = await this.call<PageWire<SessionWire>>({
      method: "GET",
      path: runtimePath("/sessions"),
      query: {
        end_user_id: params.endUserId,
        limit: params.limit,
        offset: params.offset,
      },
      ...pickOverrides(options),
    });
    return toPage(wire, toSession);
  }

  /** Yield every session for an end user, fetching pages as you go. */
  async *listAll(
    params: Omit<ListSessionsParams, "offset">,
    options?: RequestOverrides,
  ): AsyncGenerator<Session> {
    const pageSize = params.limit ?? 50;
    let offset = 0;
    for (;;) {
      const page = await this.list({ ...params, limit: pageSize, offset }, options);
      yield* page.data;
      if (page.data.length === 0 || !page.hasMore) return;
      offset += page.data.length;
    }
  }

  /**
   * Get a session and a page of its transcript.
   *
   * The transcript pages backwards: `beforeSeq` asks for what came before a
   * message you already have.
   */
  async get(
    sessionId: string,
    params: GetSessionParams = {},
    options?: RequestOverrides,
  ): Promise<SessionTranscript> {
    const wire = await this.call<SessionTranscriptWire>({
      method: "GET",
      path: runtimePath(`/sessions/${encodeURIComponent(sessionId)}`),
      query: { limit: params.limit, before_seq: params.beforeSeq },
      ...pickOverrides(options),
    });
    return {
      session: toSession(wire.session),
      messages: (wire.messages ?? []).map(toSessionMessage),
    };
  }

  /** Yield a session's messages newest first, fetching pages as you go. */
  async *listAllMessages(
    sessionId: string,
    params: GetSessionParams = {},
    options?: RequestOverrides,
  ): AsyncGenerator<SessionMessage> {
    const pageSize = params.limit ?? 50;
    let beforeSeq = params.beforeSeq;
    for (;;) {
      const transcript = await this.get(sessionId, { limit: pageSize, beforeSeq }, options);
      const messages = transcript.messages;
      if (messages.length === 0) return;
      yield* [...messages].sort((a, b) => b.seq - a.seq);
      if (messages.length < pageSize) return;
      beforeSeq = messages.reduce((lowest, m) => Math.min(lowest, m.seq), Infinity);
    }
  }
}

/**
 * Your users: what they have spent, and what they are allowed to spend.
 *
 * An end user is addressed by *your* identifier for them. You never store a
 * Celesto id, and the record is created the first time you run an agent for
 * them.
 */
export class EndUsersClient extends BaseClient {
  /** Get an end user's budget and activity. */
  async get(endUserId: string, options?: RequestOverrides): Promise<EndUser> {
    const wire = await this.call<EndUserWire>({
      method: "GET",
      path: runtimePath(`/end_users/${encodeURIComponent(endUserId)}`),
      ...pickOverrides(options),
    });
    return toEndUser(wire);
  }

  /**
   * Set an end user's budget override or metadata, creating them if needed.
   *
   * Fields you do not pass are left alone. Passing `null` clears the field:
   * `budgetCapUsd: null` drops back to your organization's default budget.
   */
  async update(
    endUserId: string,
    params: UpdateEndUserParams,
    options?: RequestOverrides,
  ): Promise<EndUser> {
    // Gated on `!== undefined`, not `in`: `in` reports a key as present when
    // it was passed explicitly as undefined, which is what spreading an
    // optional variable produces. Coercing that to null sent "clear the cap" —
    // a destructive instruction the caller never wrote. Only a literal null
    // clears.
    const body: Record<string, unknown> = {};
    if (params.budgetCapUsd !== undefined) {
      body.budget_cap_usd =
        params.budgetCapUsd === null ? null : toMoneyString(params.budgetCapUsd);
    }
    if (params.metadata !== undefined) {
      body.metadata = params.metadata;
    }

    const wire = await this.call<EndUserWire>({
      method: "PUT",
      path: runtimePath(`/end_users/${encodeURIComponent(endUserId)}`),
      body,
      ...pickOverrides(options),
    });
    return toEndUser(wire);
  }

  /** Drop an end user's override, back to the organization default. */
  async clearBudget(endUserId: string, options?: RequestOverrides): Promise<EndUser> {
    return this.update(endUserId, { budgetCapUsd: null }, options);
  }
}

/** Organization-wide defaults for managed agents. */
export class RuntimeSettingsClient extends BaseClient {
  /** Read the default budget every end user starts with. */
  async get(options?: RequestOverrides): Promise<RuntimeSettings> {
    const wire = await this.call<RuntimeSettingsWire>({
      method: "GET",
      path: runtimePath("/runtime/settings"),
      ...pickOverrides(options),
    });
    return toRuntimeSettings(wire);
  }

  /**
   * Set the default budget every end user starts with.
   *
   * Pass `null` to remove the default, which leaves end users uncapped unless
   * they have their own override.
   */
  async update(
    params: UpdateRuntimeSettingsParams,
    options?: RequestOverrides,
  ): Promise<RuntimeSettings> {
    // Same gate as EndUsers.update: an explicit undefined must not read as
    // "clear the org default".
    const body: Record<string, unknown> = {};
    if (params.defaultEndUserBudgetUsd !== undefined) {
      body.default_end_user_budget_usd =
        params.defaultEndUserBudgetUsd === null
          ? null
          : toMoneyString(params.defaultEndUserBudgetUsd);
    }

    const wire = await this.call<RuntimeSettingsWire>({
      method: "PUT",
      path: runtimePath("/runtime/settings"),
      body,
      ...pickOverrides(options),
    });
    return toRuntimeSettings(wire);
  }
}

async function* readEventStream(response: Response): AsyncGenerator<RunEvent> {
  if (!response.body) {
    throw new Error("Celesto did not return a run event stream.");
  }

  const reader = response.body.getReader();
  const textDecoder = new TextDecoder();
  const sse = new SseDecoder();
  let completed = false;

  try {
    for (;;) {
      const chunk = await reader.read();
      if (chunk.done) {
        completed = true;
        for (const frame of sse.push(textDecoder.decode())) {
          const event = toRunEvent(frame);
          if (event) yield event;
        }
        for (const frame of sse.flush()) {
          const event = toRunEvent(frame);
          if (event) yield event;
        }
        return;
      }

      for (const frame of sse.push(textDecoder.decode(chunk.value, { stream: true }))) {
        const event = toRunEvent(frame);
        if (event) yield event;
      }
    }
  } finally {
    if (!completed) {
      try {
        await reader.cancel();
      } catch {
        // The request may already be aborted or disconnected.
      }
    }
    reader.releaseLock();
  }
}

/**
 * Run your agents for your end users.
 *
 * @example
 * ```ts
 * const celesto = new ManagedAgentsClient({ apiKey: process.env.CELESTO_API_KEY });
 * const agent = await celesto.agents.create({ name: "support-bot", model: "openai/gpt-5.4-mini" });
 * const run = await celesto.runs.create(agent.id, {
 *   input: "Where is my order?",
 *   endUserId: "usr_8837",
 * });
 * console.log(run.output, run.usage.costUsd);
 * ```
 */
export class ManagedAgentsClient {
  readonly agents: AgentsClient;
  readonly runs: RunsClient;
  readonly sessions: SessionsClient;
  readonly endUsers: EndUsersClient;
  readonly settings: RuntimeSettingsClient;

  constructor(config: ClientConfig = {}) {
    this.agents = new AgentsClient(config);
    this.runs = new RunsClient(config);
    this.sessions = new SessionsClient(config);
    this.endUsers = new EndUsersClient(config);
    this.settings = new RuntimeSettingsClient(config);
  }
}

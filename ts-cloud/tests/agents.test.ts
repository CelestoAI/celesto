import assert from "node:assert/strict";
import { describe, it } from "node:test";

import * as sdk from "../src/index";
import {
  ALLOWED_CONFIG_KEYS,
  BudgetExceededError,
  ConfigKeyNotAllowedError,
  ManagedAgentError,
  ManagedAgentsClient,
  ModelRequiresOwnKeyError,
  SessionBusyError,
  eventText,
  isTerminal,
  parseRunEvents,
  parseSseFrames,
} from "../src/agents";
import type { ClientConfig } from "../src/core/config";
import { CelestoApiError } from "../src/core/errors";

interface RecordedCall {
  url: string;
  method: string;
  headers: Record<string, string>;
  body: unknown;
}

interface MockReply {
  status: number;
  body: unknown;
  headers?: Record<string, string>;
}

const makeFetchMock = (
  responder: (call: RecordedCall, index: number) => MockReply,
): { fetch: typeof fetch; calls: RecordedCall[] } => {
  const calls: RecordedCall[] = [];
  const mock: typeof fetch = async (input, init) => {
    const url =
      typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
    const rawHeaders = (init?.headers ?? {}) as Record<string, string>;
    const headers: Record<string, string> = {};
    for (const [k, v] of Object.entries(rawHeaders)) {
      headers[k.toLowerCase()] = v;
    }
    const bodyStr = typeof init?.body === "string" ? init.body : undefined;
    const call: RecordedCall = {
      url,
      method: init?.method ?? "GET",
      headers,
      body: bodyStr ? JSON.parse(bodyStr) : undefined,
    };
    calls.push(call);
    const reply = responder(call, calls.length - 1);
    return new Response(JSON.stringify(reply.body), {
      status: reply.status,
      headers: { "content-type": "application/json", ...(reply.headers ?? {}) },
    });
  };
  return { fetch: mock, calls };
};

const makeConfig = (fetchMock: typeof fetch): ClientConfig => ({
  baseUrl: "https://api.example.test",
  token: "test-token",
  fetch: fetchMock,
});

const AGENT_WIRE = {
  id: "agt_1",
  object: "agent",
  name: "support-bot",
  model: "openai/gpt-5.4-mini",
  instructions: "Be brief.",
  config: { temperature: 0.2, max_turns: 4 },
  version: 1,
  current_version_id: "agv_1",
  project_id: "prj_1",
  organization_id: "org_1",
  status: "active",
  created_at: "2026-08-09T00:00:00Z",
  updated_at: "2026-08-09T00:00:00Z",
};

const RUN_WIRE = {
  run_id: "run_1",
  object: "run",
  status: "completed",
  output: "Your order ships tomorrow.",
  usage: {
    input_tokens: 120,
    output_tokens: 32,
    total_tokens: 152,
    cost_usd: "0.000450",
  },
  agent_id: "agt_1",
  agent_version_id: "agv_1",
  session_id: "ses_1",
  end_user_id: "usr_8837",
  turn_count: 1,
  created_at: "2026-08-09T00:00:00Z",
};

const END_USER_WIRE = {
  end_user_id: "usr_8837",
  object: "end_user",
  first_activity_at: "2026-08-01T00:00:00Z",
  budget: {
    cap_usd: "5.000000",
    source: "override",
    window_start: "2026-08-01T00:00:00Z",
    window_resets_at: "2026-08-31T00:00:00Z",
    spent_usd: "0.000000",
  },
  created_at: "2026-08-01T00:00:00Z",
};

// A whole run on the wire, including one event name this SDK has never heard
// of. Deltas carry no id: they are not stored, so they are not resume points.
const SSE_BODY = `id: 1
event: run.started
data: {"run_id":"run_1","agent_id":"agt_1","agent_version_id":"agv_1","session_id":"ses_1","end_user_id":"usr_8837","model":"openai/gpt-5.4-mini","created_at":"2026-08-09T00:00:00Z"}

: keep-alive

event: message.delta
data: {"text":"Your order ","turn":1}

event: message.delta
data: {"text":"ships tomorrow.","turn":1}

id: 2
event: reasoning.delta
data: {"text":"an event from a future server"}

id: 3
event: tool.call
data: {"call_id":"call_1","name":"lookup_order","args":{"id":"42"},"turn":1}

id: 4
event: tool.result
data: {"call_id":"call_1","name":"lookup_order","result":{"eta":"tomorrow"},"turn":1}

id: 5
event: usage
data: {"turn":1,"model":"openai/gpt-5.4-mini","input_tokens":120,"output_tokens":32,"total_tokens":152,"cost_usd":"0.000450"}

id: 6
event: run.completed
data: {"run_id":"run_1","status":"completed","output":"Your order ships tomorrow.","turn_count":1,"usage":{"input_tokens":120,"output_tokens":32,"total_tokens":152,"cost_usd":"0.000450"}}

`;

const streamingFetch = (
  chunks: string[],
  onRequest?: (init: RequestInit | undefined, url: string) => void,
): typeof fetch => {
  const encoder = new TextEncoder();
  return async (input, init) => {
    onRequest?.(init, String(input));
    const body = new ReadableStream<Uint8Array>({
      start(controller) {
        for (const chunk of chunks) {
          controller.enqueue(encoder.encode(chunk));
        }
        controller.close();
      },
    });
    return new Response(body, {
      status: 200,
      headers: {
        "content-type": "text/event-stream",
        "x-celesto-events-version": "1",
      },
    });
  };
};

describe("ManagedAgentsClient", () => {
  it("exposes the five namespaces from the package root, named as in Python", () => {
    assert.equal(sdk.ManagedAgentsClient, ManagedAgentsClient);
    const client = new ManagedAgentsClient({ token: "t" });
    assert.ok(client.agents);
    assert.ok(client.runs);
    assert.ok(client.sessions);
    // endUsers/end_users differ only by each language's casing convention.
    assert.ok(client.endUsers);
    assert.ok(client.settings);
  });

  it("create() posts the definition and maps snake_case to camelCase", async () => {
    const { fetch, calls } = makeFetchMock(() => ({ status: 201, body: AGENT_WIRE }));
    const client = new ManagedAgentsClient(makeConfig(fetch));

    const agent = await client.agents.create({
      name: "support-bot",
      model: "openai/gpt-5.4-mini",
      instructions: "Be brief.",
      config: { temperature: 0.2, maxTurns: 4 },
    });

    assert.equal(agent.currentVersionId, "agv_1");
    assert.equal(agent.organizationId, "org_1");
    assert.deepEqual(agent.config, { temperature: 0.2, maxTurns: 4 });
    assert.equal(calls[0]!.url, "https://api.example.test/v1/agents");
    assert.deepEqual(calls[0]!.body, {
      name: "support-bot",
      model: "openai/gpt-5.4-mini",
      instructions: "Be brief.",
      config: { temperature: 0.2, max_turns: 4 },
    });
  });

  it("refuses a config key outside the allowlist before sending anything", async () => {
    const { fetch, calls } = makeFetchMock(() => ({ status: 201, body: AGENT_WIRE }));
    const client = new ManagedAgentsClient(makeConfig(fetch));

    await assert.rejects(
      () =>
        client.agents.create({
          name: "support-bot",
          model: "openai/gpt-5.4-mini",
          // The type system rejects this too; the cast is what a JS caller does.
          config: { tempurature: 0.2 } as never,
        }),
      (error: unknown) => {
        assert.ok(error instanceof ConfigKeyNotAllowedError);
        assert.equal(error.code, "config_key_not_allowed");
        assert.match(error.message, /tempurature/);
        return true;
      },
    );
    assert.equal(calls.length, 0);
  });

  it("documents exactly the generation settings the API accepts", () => {
    assert.deepEqual([...ALLOWED_CONFIG_KEYS].sort(), [
      "frequencyPenalty",
      "maxOutputTokens",
      "maxTokens",
      "maxTurns",
      "presencePenalty",
      "reasoningEffort",
      "seed",
      "stop",
      "temperature",
      "topP",
      "verbosity",
    ]);
  });
});

describe("pagination", () => {
  it("listAll() follows has_more and stops when it is false", async () => {
    const pages = [
      { data: [AGENT_WIRE, AGENT_WIRE], has_more: true },
      { data: [AGENT_WIRE], has_more: false },
    ];
    const { fetch, calls } = makeFetchMock((_call, index) => ({
      status: 200,
      body: pages[index] ?? { data: [], has_more: false },
    }));
    const client = new ManagedAgentsClient(makeConfig(fetch));

    const agents = [];
    for await (const agent of client.agents.listAll({ limit: 2 })) {
      agents.push(agent);
    }

    assert.equal(agents.length, 3);
    assert.equal(calls.length, 2);
    assert.match(calls[0]!.url, /offset=0/);
    assert.match(calls[1]!.url, /offset=2/);
  });

  it("run events page forward with after_seq and stop on a short page", async () => {
    const pages = [
      {
        data: [
          { seq: 1, event: "run.started", data: {} },
          { seq: 2, event: "message.completed", data: { text: "hi" } },
        ],
        events_version: "1",
      },
      { data: [{ seq: 3, event: "run.completed", data: {} }], events_version: "1" },
    ];
    const { fetch, calls } = makeFetchMock((_call, index) => ({
      status: 200,
      body: pages[index] ?? { data: [], events_version: "1" },
    }));
    const client = new ManagedAgentsClient(makeConfig(fetch));

    const seqs = [];
    for await (const event of client.runs.listAllEvents("run_1", { limit: 2 })) {
      seqs.push(event.seq);
    }

    assert.deepEqual(seqs, [1, 2, 3]);
    assert.equal(calls.length, 2);
    assert.match(calls[0]!.url, /after_seq=0/);
    assert.match(calls[1]!.url, /after_seq=2/);
  });

  it("session transcripts page backward with before_seq, newest first", async () => {
    const session = {
      id: "ses_1",
      end_user_id: "usr_8837",
      status: "idle",
      message_count: 3,
      created_at: "2026-08-09T00:00:00Z",
    };
    const message = (seq: number) => ({
      seq,
      role: "user",
      item: { text: `m${seq}` },
      created_at: "2026-08-09T00:00:00Z",
    });
    const pages = [
      { session, messages: [message(3), message(4)] },
      { session, messages: [message(2)] },
    ];
    const { fetch, calls } = makeFetchMock((_call, index) => ({
      status: 200,
      body: pages[index] ?? { session, messages: [] },
    }));
    const client = new ManagedAgentsClient(makeConfig(fetch));

    const seqs = [];
    for await (const item of client.sessions.listAllMessages("ses_1", { limit: 2 })) {
      seqs.push(item.seq);
    }

    assert.deepEqual(seqs, [4, 3, 2]);
    assert.ok(!calls[0]!.url.includes("before_seq"));
    assert.match(calls[1]!.url, /before_seq=3/);
  });
});

describe("money", () => {
  it("keeps costs as decimal strings, never numbers", async () => {
    const { fetch } = makeFetchMock(() => ({ status: 200, body: RUN_WIRE }));
    const client = new ManagedAgentsClient(makeConfig(fetch));

    const run = await client.runs.create("agt_1", {
      input: "Where is my order?",
      endUserId: "usr_8837",
    });

    assert.equal(typeof run.usage.costUsd, "string");
    assert.equal(run.usage.costUsd, "0.000450");

    // Why it stays a string: ten thousand of these runs, added up as floats,
    // no longer costs $4.50.
    let asFloat = 0;
    for (let i = 0; i < 10_000; i += 1) asFloat += Number(run.usage.costUsd);
    assert.notEqual(asFloat, 4.5);
  });

  it("reads an end user's budget as decimal strings", async () => {
    const { fetch } = makeFetchMock(() => ({
      status: 200,
      body: {
        end_user_id: "usr_8837",
        object: "end_user",
        first_activity_at: "2026-08-01T00:00:00Z",
        budget: {
          cap_usd: "0.500000",
          source: "override",
          window_start: "2026-08-01T00:00:00Z",
          window_resets_at: "2026-08-31T00:00:00Z",
          spent_usd: "0.010450",
          remaining_usd: "0.489550",
        },
        created_at: "2026-08-01T00:00:00Z",
      },
    }));
    const client = new ManagedAgentsClient(makeConfig(fetch));

    const user = await client.endUsers.get("usr_8837");

    assert.equal(user.budget.spentUsd, "0.010450");
    assert.equal(user.budget.remainingUsd, "0.489550");
    assert.equal(user.budget.windowResetsAt, "2026-08-31T00:00:00Z");
    assert.equal(typeof user.budget.capUsd, "string");
  });

  it("sends budget writes as strings and only the fields you pass", async () => {
    const { fetch, calls } = makeFetchMock(() => ({
      status: 200,
      body: {
        end_user_id: "usr_8837",
        first_activity_at: "2026-08-01T00:00:00Z",
        budget: {
          source: "override",
          window_start: "2026-08-01T00:00:00Z",
          window_resets_at: "2026-08-31T00:00:00Z",
          spent_usd: "0.000000",
        },
        created_at: "2026-08-01T00:00:00Z",
      },
    }));
    const client = new ManagedAgentsClient(makeConfig(fetch));

    await client.endUsers.update("usr_8837", { budgetCapUsd: "0.50" });
    await client.endUsers.update("usr_8837", { metadata: { plan: "free" } });
    await client.endUsers.clearBudget("usr_8837");

    assert.deepEqual(calls[0]!.body, { budget_cap_usd: "0.50" });
    assert.deepEqual(calls[1]!.body, { metadata: { plan: "free" } });
    assert.deepEqual(calls[2]!.body, { budget_cap_usd: null });
  });

  it("refuses a number budget instead of shipping its rounding error", async () => {
    // The type says DecimalString, but a type is advice at runtime: plain JS
    // callers, `any`, and JSON parsed from elsewhere all arrive as numbers.
    // This used to do String(value), so 0.1 + 0.2 went out as
    // "0.30000000000000004" and 1e-7 as "1e-7" — both of which the API
    // refuses anyway. 0.5 and 5 are refused too: sorting representable
    // numbers from lossy ones is the trap.
    const { fetch, calls } = makeFetchMock(() => ({ status: 200, body: {} }));
    const client = new ManagedAgentsClient(makeConfig(fetch));

    for (const amount of [0.5, 5, 0.1 + 0.2, 1e-7]) {
      await assert.rejects(
        async () =>
          client.endUsers.update("usr_8837", {
            budgetCapUsd: amount as unknown as string,
          }),
        (error: unknown) =>
          error instanceof TypeError && /cannot be a number/.test(error.message),
      );
    }

    // It fails before the request, not after a 422 round trip.
    assert.equal(calls.length, 0);
  });

  it("treats an explicit undefined as absent, not as a request to clear", async () => {
    // `"budgetCapUsd" in params` is true when the key was passed with an
    // undefined value — which is exactly what spreading an optional variable
    // produces. That used to be coerced to null and sent, wiping the cap the
    // caller was trying to leave alone.
    const { fetch, calls } = makeFetchMock(() => ({ status: 200, body: END_USER_WIRE }));
    const client = new ManagedAgentsClient(makeConfig(fetch));

    const maybeCap: string | undefined = undefined;
    await client.endUsers.update("usr_8837", { budgetCapUsd: maybeCap, metadata: undefined });

    assert.deepEqual(calls[0]!.body, {});

    await client.settings.update({ defaultEndUserBudgetUsd: undefined });
    assert.deepEqual(calls[1]!.body, {});
  });

  it("still clears the cap when the caller writes null", async () => {
    const { fetch, calls } = makeFetchMock(() => ({ status: 200, body: END_USER_WIRE }));
    const client = new ManagedAgentsClient(makeConfig(fetch));

    await client.endUsers.update("usr_8837", { budgetCapUsd: null });
    assert.deepEqual(calls[0]!.body, { budget_cap_usd: null });
  });

  it("refuses a malformed amount string, not just a number", async () => {
    // Refusing a number and then sending "1e-7" — the exact form the API
    // rejects — would leave the front door open on a locked window.
    const { fetch, calls } = makeFetchMock(() => ({ status: 200, body: END_USER_WIRE }));
    const client = new ManagedAgentsClient(makeConfig(fetch));

    for (const bad of ["1e-7", "abc", "-5", "5.0000001", "$5.00", ""]) {
      await assert.rejects(
        async () => client.endUsers.update("usr_8837", { budgetCapUsd: bad }),
        (error: unknown) =>
          error instanceof TypeError && /not a valid amount/.test(error.message),
      );
    }
    assert.equal(calls.length, 0);
  });

  it("does not suggest the caller's own rounding error as the fix", async () => {
    const { fetch } = makeFetchMock(() => ({ status: 200, body: {} }));
    const client = new ManagedAgentsClient(makeConfig(fetch));

    await assert.rejects(
      async () =>
        client.endUsers.update("usr_8837", {
          budgetCapUsd: (0.1 + 0.2) as unknown as string,
        }),
      (error: unknown) => {
        const message = (error as Error).message;
        const advice = message.slice(message.indexOf("Pass a decimal string"));
        return !advice.includes("0.30000000000000004") && advice.includes('"5.00"');
      },
    );
  });
});

describe("idempotency and retries", () => {
  it("sends the Idempotency-Key header and replays return the stored run", async () => {
    const { fetch, calls } = makeFetchMock(() => ({ status: 200, body: RUN_WIRE }));
    const client = new ManagedAgentsClient(makeConfig(fetch));

    const first = await client.runs.create("agt_1", {
      input: "Hi",
      endUserId: "usr_8837",
      idempotencyKey: "order-status-42",
    });
    const replay = await client.runs.create("agt_1", {
      input: "Hi",
      endUserId: "usr_8837",
      idempotencyKey: "order-status-42",
    });

    assert.equal(first.runId, replay.runId);
    assert.equal(calls[0]!.headers["idempotency-key"], "order-status-42");
    assert.equal(calls[1]!.headers["idempotency-key"], "order-status-42");
  });

  it("retries a busy session with one generated key and honours Retry-After", async () => {
    const { fetch, calls } = makeFetchMock((_call, index) =>
      index === 0
        ? {
            status: 409,
            body: { detail: { code: "session_busy", message: "Run in flight." } },
            headers: { "retry-after": "0" },
          }
        : { status: 200, body: RUN_WIRE },
    );
    const client = new ManagedAgentsClient(makeConfig(fetch));

    const run = await client.runs.create("agt_1", {
      input: "Hi",
      endUserId: "usr_8837",
      maxRetries: 1,
    });

    assert.equal(run.runId, "run_1");
    assert.equal(calls.length, 2);
    const key = calls[0]!.headers["idempotency-key"];
    // A retry without a key could charge the end user twice, so one is made.
    assert.ok(key);
    assert.equal(calls[1]!.headers["idempotency-key"], key);
  });

  it("throws SessionBusyError, marked retryable, when retries run out", async () => {
    const { fetch } = makeFetchMock(() => ({
      status: 409,
      body: { detail: { code: "session_busy", message: "Run in flight." } },
      headers: { "retry-after": "3" },
    }));
    const client = new ManagedAgentsClient(makeConfig(fetch));

    await assert.rejects(
      () => client.runs.create("agt_1", { input: "Hi", endUserId: "usr_8837" }),
      (error: unknown) => {
        assert.ok(error instanceof SessionBusyError);
        assert.equal(error.retryable, true);
        assert.equal(error.retryAfter, 3);
        assert.equal(error.status, 409);
        assert.equal(error.message, "Run in flight.");
        return true;
      },
    );
  });
});

describe("typed errors", () => {
  it("maps error codes to their own class, and keeps CelestoApiError", async () => {
    const cases: [number, string | undefined, new (...args: never[]) => Error][] = [
      [402, "budget_exceeded", BudgetExceededError],
      [402, undefined, BudgetExceededError],
      [422, "model_requires_own_key", ModelRequiresOwnKeyError],
    ];

    for (const [status, code, ErrorClass] of cases) {
      const { fetch } = makeFetchMock(() => ({
        status,
        body: { detail: code ? { code, message: "Refused." } : "Refused." },
      }));
      const client = new ManagedAgentsClient(makeConfig(fetch));

      await assert.rejects(
        () => client.runs.create("agt_1", { input: "Hi", endUserId: "usr_8837" }),
        (error: unknown) => {
          assert.ok(error instanceof ErrorClass);
          assert.ok(error instanceof ManagedAgentError);
          assert.ok(error instanceof CelestoApiError);
          return true;
        },
      );
    }
  });

  it("leaves errors it does not recognise alone", async () => {
    const { fetch } = makeFetchMock(() => ({
      status: 404,
      body: { detail: "Agent not found" },
    }));
    const client = new ManagedAgentsClient(makeConfig(fetch));

    await assert.rejects(
      () => client.runs.get("run_missing"),
      (error: unknown) => {
        assert.ok(error instanceof CelestoApiError);
        assert.equal(error instanceof ManagedAgentError, false);
        assert.equal(error.message, "Agent not found");
        return true;
      },
    );
  });
});

describe("the run event stream", () => {
  it("ignores event names this SDK does not know", () => {
    const names = parseRunEvents(SSE_BODY).map((event) => event.name);

    assert.equal(names.includes("reasoning.delta" as never), false);
    assert.deepEqual(names, [
      "run.started",
      "message.delta",
      "message.delta",
      "tool.call",
      "tool.result",
      "usage",
      "run.completed",
    ]);
  });

  it("parses every frame, including the one the mapping then drops", () => {
    const frames = parseSseFrames(SSE_BODY).filter((frame) => frame.event);

    assert.deepEqual(
      frames.map((frame) => frame.event),
      [
        "run.started",
        "message.delta",
        "message.delta",
        "reasoning.delta",
        "tool.call",
        "tool.result",
        "usage",
        "run.completed",
      ],
    );
  });

  it("gives deltas no sequence number, because they are not stored", () => {
    const events = parseRunEvents(SSE_BODY);
    const delta = events.find((event) => event.name === "message.delta");
    const started = events.find((event) => event.name === "run.started");
    const completed = events.find((event) => event.name === "run.completed");

    assert.equal(delta!.seq, null);
    assert.equal(started!.seq, 1);
    assert.equal(completed!.seq, 6);
  });

  it("maps event bodies to camelCase and keeps cost a string", () => {
    const events = parseRunEvents(SSE_BODY);
    const started = events.find((event) => event.name === "run.started")!;
    const usage = events.find((event) => event.name === "usage")!;
    const completed = events.find((event) => event.name === "run.completed")!;
    const toolResult = events.find((event) => event.name === "tool.result")!;

    assert.equal(started.name, "run.started");
    if (started.name !== "run.started") throw new Error("unreachable");
    assert.equal(started.data.endUserId, "usr_8837");

    if (usage.name !== "usage") throw new Error("unreachable");
    assert.equal(usage.data.costUsd, "0.000450");
    assert.equal(usage.data.totalTokens, 152);

    if (completed.name !== "run.completed") throw new Error("unreachable");
    assert.equal(completed.data.usage.costUsd, "0.000450");
    assert.equal(completed.data.turnCount, 1);

    if (toolResult.name !== "tool.result") throw new Error("unreachable");
    assert.deepEqual(toolResult.data.result, { eta: "tomorrow" });
    assert.equal("error" in toolResult.data, false);
  });

  it("reads text and terminal status through the helpers", () => {
    const events = parseRunEvents(SSE_BODY);
    const text = events
      .filter((event) => event.name === "message.delta")
      .map(eventText)
      .join("");

    assert.equal(text, "Your order ships tomorrow.");
    assert.equal(isTerminal(events[events.length - 1]!), true);
    assert.equal(isTerminal(events[0]!), false);
  });

  it("drops a malformed data line rather than killing the stream", () => {
    const body =
      'event: message.delta\ndata: {not json\n\nevent: message.completed\ndata: {"text":"ok","turn":1}\n\n';

    assert.deepEqual(
      parseRunEvents(body).map((event) => event.name),
      ["message.completed"],
    );
  });

  it("stream() reassembles frames split across chunk boundaries", async () => {
    let seenBody: Record<string, unknown> = {};
    let seenKey: string | null = null;
    const half = Math.floor(SSE_BODY.length / 2);
    const fetch = streamingFetch(
      [SSE_BODY.slice(0, half), SSE_BODY.slice(half)],
      (init) => {
        seenBody = JSON.parse(String(init?.body));
        seenKey = new Headers(init?.headers).get("idempotency-key");
      },
    );
    const client = new ManagedAgentsClient(makeConfig(fetch));

    const events = [];
    for await (const event of client.runs.stream("agt_1", {
      input: "Where is my order?",
      endUserId: "usr_8837",
      idempotencyKey: "k-9",
    })) {
      events.push(event);
    }

    assert.equal(seenBody.stream, true);
    assert.equal(seenBody.end_user_id, "usr_8837");
    assert.equal(seenKey, "k-9");
    assert.equal(events[events.length - 1]!.name, "run.completed");
    assert.equal(
      events.some((event) => (event.name as string) === "reasoning.delta"),
      false,
    );
  });

  it("stream() throws the typed error when the run is refused up front", async () => {
    const { fetch } = makeFetchMock(() => ({
      status: 402,
      body: { detail: { code: "budget_exceeded", message: "Out of budget." } },
    }));
    const client = new ManagedAgentsClient(makeConfig(fetch));

    await assert.rejects(async () => {
      for await (const _event of client.runs.stream("agt_1", {
        input: "Hi",
        endUserId: "usr_8837",
      })) {
        // The first read is where the refusal surfaces.
      }
    }, BudgetExceededError);
  });

  it("stream() reports a failed run as an event, not a thrown error", async () => {
    const body = `id: 9
event: run.failed
data: {"run_id":"run_1","status":"failed","error_code":"budget_exceeded","error":"Budget exhausted mid-run.","turn_count":2,"usage":{"input_tokens":1,"output_tokens":1,"total_tokens":2,"cost_usd":"0.500000"}}

`;
    const client = new ManagedAgentsClient(makeConfig(streamingFetch([body])));

    const events = [];
    for await (const event of client.runs.stream("agt_1", {
      input: "Hi",
      endUserId: "usr_8837",
    })) {
      events.push(event);
    }

    assert.equal(events.length, 1);
    const failed = events[0]!;
    if (failed.name !== "run.failed") throw new Error("unreachable");
    assert.equal(failed.data.errorCode, "budget_exceeded");
    assert.equal(failed.data.usage.costUsd, "0.500000");
    assert.equal(isTerminal(failed), true);
  });
});

describe("runtime settings", () => {
  it("reads and writes the organization default budget", async () => {
    const { fetch, calls } = makeFetchMock((_call, index) => ({
      status: 200,
      body: {
        organization_id: "org_1",
        default_end_user_budget_usd: index === 0 ? "0.500000" : "1.000000",
      },
    }));
    const client = new ManagedAgentsClient(makeConfig(fetch));

    const current = await client.settings.get();
    const updated = await client.settings.update({ defaultEndUserBudgetUsd: "1.00" });

    assert.equal(current.defaultEndUserBudgetUsd, "0.500000");
    assert.equal(updated.defaultEndUserBudgetUsd, "1.000000");
    assert.deepEqual(calls[1]!.body, { default_end_user_budget_usd: "1.00" });
  });
});

import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import type { AddressInfo } from "node:net";
import { request as httpRequest } from "node:http";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import type { Agent } from "@earendil-works/pi-agent-core";
import { createApp } from "../server/index.js";
import { ConversationManager, type RuntimeDependencies } from "../server/manager.js";
import type { ModelAccessService } from "../server/model-access.js";
import { ConversationStateStore, serializeConversation } from "../server/state-store.js";
import type { ConversationContext } from "../server/types.js";

test("conversation commands are idempotent and reject stale versions", async (t) => {
  const manager = new ConversationManager("", "gpt-5-mini");
  const created = await manager.create();
  const internals = manager as unknown as { runTurn: (context: ConversationContext, text: string) => Promise<void> };
  internals.runTurn = async () => undefined;
  const server = createApp(manager);
  await new Promise<void>((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
  t.after(() => new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve())));
  const origin = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
  const bootstrapResponse = await fetch(`${origin}/api/bootstrap`);
  const bootstrap = await bootstrapResponse.json() as { csrfToken: string };
  const headers = {
    "content-type": "application/json",
    "x-smol-csrf": bootstrap.csrfToken,
    cookie: bootstrapResponse.headers.get("set-cookie")!.split(";")[0]!,
    origin,
  };
  const body = JSON.stringify({ commandId: "message-one", command: { kind: "send_message", text: "Only once" } });

  const first = await fetch(`${origin}/api/conversations/${created.id}/commands`, { method: "POST", headers, body });
  const duplicate = await fetch(`${origin}/api/conversations/${created.id}/commands`, { method: "POST", headers, body });
  assert.equal(first.status, 202);
  assert.equal(duplicate.status, 202);
  assert.equal(manager.snapshot(created.id).messages.filter((message) => message.text === "Only once").length, 1);

  const conflicting = await fetch(`${origin}/api/conversations/${created.id}/commands`, {
    method: "POST",
    headers,
    body: JSON.stringify({ commandId: "message-one", command: { kind: "send_message", text: "A different message" } }),
  });
  assert.equal(conflicting.status, 409);
  assert.equal((await conflicting.json() as { code: string }).code, "command_id_conflict");
  assert.equal(manager.snapshot(created.id).messages.some((message) => message.text === "A different message"), false);

  const stale = await fetch(`${origin}/api/conversations/${created.id}/commands`, {
    method: "POST",
    headers,
    body: JSON.stringify({ commandId: "stale-stop", expectedVersion: 1, command: { kind: "stop" } }),
  });
  assert.equal(stale.status, 409);
  assert.equal((await stale.json() as { code: string }).code, "stale_version");
});

test("the conversation view stream is session-bound and starts with a full current view", async (t) => {
  const manager = new ConversationManager("", "gpt-5-mini");
  const created = await manager.create();
  const server = createApp(manager);
  await new Promise<void>((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
  t.after(() => new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve())));
  const origin = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;

  const unauthenticated = await fetch(`${origin}/api/conversations/${created.id}/events`);
  assert.equal(unauthenticated.status, 401);

  const bootstrapResponse = await fetch(`${origin}/api/bootstrap`);
  const cookie = bootstrapResponse.headers.get("set-cookie")!.split(";")[0]!;

  const nonLoopbackStatus = await new Promise<number>((resolve, reject) => {
    const request = httpRequest({ hostname: "127.0.0.1", port: (server.address() as AddressInfo).port, path: `/api/conversations/${created.id}/events`, headers: { cookie, host: "example.com" } }, (response) => {
      response.resume();
      response.on("end", () => resolve(response.statusCode ?? 0));
    });
    request.on("error", reject);
    request.end();
  });
  assert.equal(nonLoopbackStatus, 403);

  const missing = await fetch(`${origin}/api/conversations/not-this-conversation`, { headers: { cookie } });
  assert.equal(missing.status, 404);

  const stream = await fetch(`${origin}/api/conversations/${created.id}/events`, { headers: { cookie } });
  const reader = stream.body!.getReader();
  const decoder = new TextDecoder();
  let body = "";
  while (!body.includes("\n\n")) {
    const chunk = await reader.read();
    if (chunk.done) break;
    body += decoder.decode(chunk.value, { stream: true });
  }
  assert.match(body, /event: conversation\.view/);
  assert.match(body, new RegExp(`"conversationId":"${created.id}"`));
  assert.match(body, /"turns":\[\]/);
  await reader.cancel().catch(() => undefined);
});

test("recovery routes continue interrupted work and start over with a clean conversation", async (t) => {
  const directory = await mkdtemp(join(tmpdir(), "open-muse-routes-"));
  t.after(() => rm(directory, { recursive: true, force: true }));
  const store = new ConversationStateStore(join(directory, "state.json"));
  const initial = new ConversationManager("", "gpt-5-mini");
  const created = await initial.create();
  const initialContext = (initial as unknown as { context: ConversationContext }).context;
  initialContext.runState = "model_turn";
  initialContext.messages.push({
    id: "request",
    role: "user",
    text: "Finish this task",
    createdAt: new Date().toISOString(),
  });
  await store.save(serializeConversation(initialContext));

  const manager = await ConversationManager.open("", "gpt-5-mini", false, store);
  const internals = manager as unknown as {
    turnQueue: Promise<void>;
    runTurn: (context: ConversationContext, text: string) => Promise<void>;
  };
  internals.runTurn = async () => undefined;
  const server = createApp(manager);
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  t.after(() => new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve())));
  const origin = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;

  const bootstrapResponse = await fetch(`${origin}/api/bootstrap`);
  const bootstrap = await bootstrapResponse.json() as { csrfToken: string; conversationId?: string };
  const cookie = bootstrapResponse.headers.get("set-cookie")!.split(";")[0]!;
  const headers = {
    "content-type": "application/json",
    "x-smol-csrf": bootstrap.csrfToken,
    cookie,
    origin,
  };
  assert.equal(bootstrap.conversationId, created.id);

  const continuedResponse = await fetch(`${origin}/api/conversations/${created.id}/commands`, {
    method: "POST",
    headers,
    body: JSON.stringify({ commandId: "continue-one", command: { kind: "continue" } }),
  });
  const continued = await continuedResponse.json() as { id: string; runState: string };
  assert.equal(continuedResponse.status, 200);
  assert.equal(continued.id, created.id);
  assert.equal(continued.runState, "model_turn");
  await internals.turnQueue;

  const startOverResponse = await fetch(`${origin}/api/conversations/${created.id}/commands`, {
    method: "POST",
    headers,
    body: JSON.stringify({ commandId: "start-over-one", command: { kind: "start_over" } }),
  });
  const replacement = await startOverResponse.json() as { id: string; runState: string; messages: unknown[] };
  assert.equal(startOverResponse.status, 200);
  assert.notEqual(replacement.id, created.id);
  assert.equal(replacement.runState, "idle");
  assert.deepEqual(replacement.messages, []);
});

test("message and resume routes wait for their checkpoints before responding", async (t) => {
  const directory = await mkdtemp(join(tmpdir(), "open-muse-awaited-routes-"));
  t.after(() => rm(directory, { recursive: true, force: true }));
  const store = new ConversationStateStore(join(directory, "state.json"));
  const manager = new ConversationManager("", "gpt-5-mini", false, store);
  const created = await manager.create();
  const internals = manager as unknown as {
    turnQueue: Promise<void>;
    runTurn: (context: ConversationContext, text: string) => Promise<void>;
  };
  internals.runTurn = async () => undefined;
  const server = createApp(manager);
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  t.after(() => new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve())));
  const origin = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
  const bootstrapResponse = await fetch(`${origin}/api/bootstrap`);
  const bootstrap = await bootstrapResponse.json() as { csrfToken: string };
  const headers = {
    "content-type": "application/json",
    "x-smol-csrf": bootstrap.csrfToken,
    cookie: bootstrapResponse.headers.get("set-cookie")!.split(";")[0]!,
    origin,
  };

  const messageResponse = await fetch(`${origin}/api/conversations/${created.id}/commands`, {
    method: "POST",
    headers,
    body: JSON.stringify({ commandId: "message-durable", command: { kind: "send_message", text: "Persist this before replying" } }),
  });
  assert.equal(messageResponse.status, 202);
  assert.equal((await store.load())?.conversation.messages.at(-1)?.text, "Persist this before replying");
  await internals.turnQueue;

  const takeover = await manager.takeover(created.id);
  const resumeResponse = await fetch(`${origin}/api/conversations/${created.id}/commands`, {
    method: "POST",
    headers,
    body: JSON.stringify({ commandId: "return-control-one", command: { kind: "return_control", controlEpoch: takeover.controlEpoch } }),
  });
  assert.equal(resumeResponse.status, 200);
  assert.equal((await store.load())?.conversation.controlOwner, "agent");
});

test("model-access mutations require CSRF and reject unknown JSON fields", async (t) => {
  const manager = new ConversationManager("", "gpt-5-mini");
  let cancelled = false;
  let started = false;
  const modelAccess = {
    snapshot: async () => ({ providers: [], disconnectingProviderIds: [] }),
    cancelSessionAttempts: () => undefined,
    close: () => undefined,
    cancelAttempt: () => { cancelled = true; return { id: "attempt", providerId: "openai", state: "cancelled", createdAt: new Date().toISOString(), expiresAt: new Date().toISOString() }; },
    startAttempt: () => { started = true; throw new Error("should not run"); },
  } as unknown as ModelAccessService;
  const server = createApp(manager, undefined, modelAccess);
  await new Promise<void>((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
  t.after(() => new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve())));
  const origin = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
  const bootstrapResponse = await fetch(`${origin}/api/bootstrap`);
  const bootstrap = await bootstrapResponse.json() as { csrfToken: string };
  const cookie = bootstrapResponse.headers.get("set-cookie")!.split(";")[0]!;

  const missingCsrf = await fetch(`${origin}/api/auth-attempts/attempt`, { method: "DELETE", headers: { "content-type": "application/json", cookie, origin }, body: "{}" });
  assert.equal(missingCsrf.status, 403);
  assert.equal(cancelled, false);

  const invalidBody = await fetch(`${origin}/api/auth-attempts`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-smol-csrf": bootstrap.csrfToken, cookie, origin },
    body: JSON.stringify({ providerId: "openai", method: "api_key", unexpected: true }),
  });
  assert.equal(invalidBody.status, 400);
  assert.deepEqual(await invalidBody.json(), { error: "Request body is invalid. Check the fields and try again.", code: "invalid_request" });
  assert.equal(started, false);
});

test("model-access routes preserve session selection and expose the complete local lifecycle", async (t) => {
  const now = new Date().toISOString();
  const calls: string[] = [];
  const attempt = { id: "attempt-positive", providerId: "test-provider", state: "waiting_for_input" as const, createdAt: now, expiresAt: now, prompt: { id: "prompt-positive", type: "secret" as const, message: "Enter key" } };
  const modelAccess = {
    models: {},
    snapshot: async (selection?: { providerId: string; modelId: string }) => ({
      providers: [{ id: "test-provider", name: "Test Provider", configured: true, source: "api_key" as const, methods: [{ type: "api_key" as const, label: "Use a key", enabled: true }], models: [{ id: "model-a", name: "Model A", recommended: true }, { id: "model-b", name: "Model B", recommended: false }] }],
      selection,
      disconnectingProviderIds: [],
    }),
    validateSelection: async (selection: { providerId: string; modelId: string }) => { calls.push(`validate:${selection.modelId}`); return { id: selection.modelId }; },
    preflight: async (selection: { providerId: string; modelId: string }) => { calls.push(`preflight:${selection.modelId}`); return { id: selection.modelId }; },
    startAttempt: () => { calls.push("start"); return attempt; },
    getAttempt: () => attempt,
    submitPrompt: (_session: string, _attempt: string, promptId: string, value: string) => { calls.push(`prompt:${promptId}:${value}`); return { ...attempt, state: "succeeded" as const, prompt: undefined }; },
    cancelAttempt: () => { calls.push("cancel"); return { ...attempt, state: "cancelled" as const, prompt: undefined }; },
    subscribe: (_session: string, _attempt: string, listener: (event: { id: number; type: string; snapshot: unknown }) => void) => {
      listener({ id: 1, type: "auth.succeeded", snapshot: { ...attempt, state: "succeeded", prompt: undefined } });
      return () => undefined;
    },
    logout: async (providerId: string) => { calls.push(`logout:${providerId}`); },
    cancelSessionAttempts: () => undefined,
    close: () => undefined,
  } as unknown as ModelAccessService;
  const fakeAgent = { state: { messages: [] }, abort: () => undefined, waitForIdle: async () => undefined } as unknown as Agent;
  const runtime = { createAgentWithModel: () => fakeAgent } satisfies Partial<RuntimeDependencies>;
  const manager = new ConversationManager("", "legacy", false, undefined, undefined, runtime, modelAccess);
  const server = createApp(manager, undefined, modelAccess);
  await new Promise<void>((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
  t.after(() => new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve())));
  const origin = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
  const bootstrapResponse = await fetch(`${origin}/api/bootstrap`);
  const bootstrap = await bootstrapResponse.json() as { csrfToken: string; modelAccess: { selection?: unknown } };
  const headers = { "content-type": "application/json", "x-smol-csrf": bootstrap.csrfToken, cookie: bootstrapResponse.headers.get("set-cookie")!.split(";")[0]!, origin };

  const selection = { providerId: "test-provider", modelId: "model-a" };
  assert.equal((await fetch(`${origin}/api/model-access`, { headers: { cookie: headers.cookie } })).status, 200);
  assert.equal((await fetch(`${origin}/api/model-access/selection`, { method: "PUT", headers, body: JSON.stringify(selection) })).status, 200);
  const selectedAccess = await (await fetch(`${origin}/api/model-access`, { headers: { cookie: headers.cookie } })).json() as { selection: typeof selection };
  assert.deepEqual(selectedAccess.selection, selection);

  const createdResponse = await fetch(`${origin}/api/conversations`, { method: "POST", headers, body: "{}" });
  const created = await createdResponse.json() as { id: string; modelId: string };
  assert.equal(created.modelId, "model-a");
  assert.equal(createdResponse.status, 201);

  const started = await fetch(`${origin}/api/auth-attempts`, { method: "POST", headers, body: JSON.stringify({ providerId: "test-provider", method: "api_key" }) });
  assert.equal(started.status, 201);
  assert.equal((await fetch(`${origin}/api/auth-attempts/${attempt.id}`, { headers: { cookie: headers.cookie } })).status, 200);
  assert.equal((await fetch(`${origin}/api/auth-attempts/${attempt.id}/prompts/${attempt.prompt.id}`, { method: "POST", headers, body: JSON.stringify({ value: "secret" }) })).status, 200);
  const eventResponse = await fetch(`${origin}/api/auth-attempts/${attempt.id}/events`, { headers: { cookie: headers.cookie } });
  assert.match(await eventResponse.text(), /event: auth\.succeeded/);
  assert.equal((await fetch(`${origin}/api/auth-attempts/${attempt.id}`, { method: "DELETE", headers, body: "{}" })).status, 202);

  const switchedResponse = await fetch(`${origin}/api/conversations/${created.id}/commands`, { method: "POST", headers, body: JSON.stringify({ commandId: "change-model-one", command: { kind: "change_model", providerId: "test-provider", modelId: "model-b" } }) });
  assert.equal(switchedResponse.status, 200);
  assert.equal(((await switchedResponse.json()) as { modelId: string }).modelId, "model-b");
  assert.equal((await fetch(`${origin}/api/model-access/providers/test-provider`, { method: "DELETE", headers, body: "{}" })).status, 200);
  assert.equal((await fetch(`${origin}/api/conversations/${created.id}/commands`, { method: "POST", headers, body: JSON.stringify({ commandId: "reconnect-model-one", command: { kind: "reconnect_model" } }) })).status, 200);

  assert.deepEqual(calls, ["validate:model-a", "validate:model-a", "start", "prompt:prompt-positive:secret", "cancel", "preflight:model-b", "logout:test-provider", "preflight:model-b"]);
});

test("conversation history routes list, create, and activate saved chats", async (t) => {
  const manager = new ConversationManager("", "gpt-5-mini");
  const first = await manager.create();
  const context = (manager as unknown as { context: ConversationContext }).context;
  context.messages.push({ id: "history-title", role: "user", text: "Plan a weekend trip", createdAt: new Date().toISOString() });
  const server = createApp(manager);
  await new Promise<void>((resolve, reject) => { server.once("error", reject); server.listen(0, "127.0.0.1", resolve); });
  t.after(() => new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve())));
  const origin = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
  const bootstrapResponse = await fetch(`${origin}/api/bootstrap`);
  const bootstrap = await bootstrapResponse.json() as { csrfToken: string; conversationId: string };
  const cookie = bootstrapResponse.headers.get("set-cookie")!.split(";")[0]!;
  const headers = { "content-type": "application/json", "x-smol-csrf": bootstrap.csrfToken, cookie, origin };

  assert.equal(bootstrap.conversationId, first.id);
  const initialList = await (await fetch(`${origin}/api/conversations`, { headers: { cookie } })).json() as { activeConversationId: string; conversations: Array<{ id: string; title: string }> };
  assert.equal(initialList.activeConversationId, first.id);
  assert.equal(initialList.conversations[0]?.title, "Plan a weekend trip");

  const createdResponse = await fetch(`${origin}/api/conversations`, { method: "POST", headers, body: JSON.stringify({ providerId: "openai", modelId: "gpt-5-mini" }) });
  const second = await createdResponse.json() as { id: string };
  assert.equal(createdResponse.status, 201);
  assert.notEqual(second.id, first.id);

  const activatedResponse = await fetch(`${origin}/api/conversations/${first.id}/activate`, { method: "POST", headers, body: "{}" });
  assert.equal(activatedResponse.status, 200);
  assert.equal(((await activatedResponse.json()) as { id: string }).id, first.id);
  assert.equal((await fetch(`${origin}/api/conversations/missing/activate`, { method: "POST", headers, body: "{}" })).status, 404);
  assert.equal((await fetch(`${origin}/api/conversations`, { method: "POST", headers, body: JSON.stringify({ providerId: "openai", extra: true }) })).status, 400);
});

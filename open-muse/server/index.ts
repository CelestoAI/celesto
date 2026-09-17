import { createReadStream } from "node:fs";
import { access, stat } from "node:fs/promises";
import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";
import type { Duplex } from "node:stream";
import { extname, join, normalize, sep } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { randomBytes } from "node:crypto";
import httpProxy from "http-proxy";
import { z } from "zod";
import { ConversationManager } from "./manager.js";
import { createComputerProvider } from "./computer-provider.js";
import { ModelAccessService, type ModelSelection } from "./model-access.js";

const authAttemptBody = z.object({ providerId: z.string().min(1).max(80), method: z.enum(["oauth", "api_key"]) }).strict();
const authPromptBody = z.object({ value: z.string().min(1).max(16_384) }).strict();
const selectionBody = z.object({ providerId: z.string().min(1).max(80), modelId: z.string().min(1).max(200) }).strict();
const createConversationBody = z.union([z.object({}).strict(), selectionBody]);
const commandBody = z.object({
  commandId: z.string().min(1).max(100),
  expectedVersion: z.number().int().nonnegative().optional(),
  command: z.discriminatedUnion("kind", [
    z.object({ kind: z.literal("send_message"), text: z.string().trim().min(1).max(8_000) }).strict(),
    z.object({ kind: z.literal("approve"), approvalId: z.string().min(1).max(200), actionDigest: z.string().length(64) }).strict(),
    z.object({ kind: z.literal("reject"), approvalId: z.string().min(1).max(200), actionDigest: z.string().length(64) }).strict(),
    z.object({ kind: z.literal("take_control") }).strict(),
    z.object({ kind: z.literal("return_control"), controlEpoch: z.string().min(12).max(200) }).strict(),
    z.object({ kind: z.literal("continue") }).strict(),
    z.object({ kind: z.literal("start_over") }).strict(),
    z.object({ kind: z.literal("stop") }).strict(),
    z.object({ kind: z.literal("reconnect_model") }).strict(),
    z.object({ kind: z.literal("change_model"), providerId: z.string().min(1).max(80), modelId: z.string().min(1).max(200) }).strict(),
    z.object({ kind: z.literal("adopt_popup"), tabId: z.string().min(1).max(200) }).strict(),
  ]),
}).strict();
interface LocalSession { csrfToken: string; createdAt: number; lastSeenAt: number; selection?: ModelSelection }
const sessions = new Map<string, LocalSession>();
const SESSION_IDLE_MS = 12 * 60 * 60_000;
const SESSION_ABSOLUTE_MS = 24 * 60 * 60_000;
const MAX_SESSIONS = 32;
const proxy = httpProxy.createProxyServer({ ws: true, xfwd: false, changeOrigin: false });
proxy.on("error", (_error, _request, response) => {
  if (response && "writeHead" in response) { response.writeHead(502); response.end("Live browser proxy unavailable"); }
});

const securityHeaders = {
  "content-security-policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' ws://127.0.0.1:*; frame-src 'self'; frame-ancestors 'self'; object-src 'none'; base-uri 'none'",
  "x-content-type-options": "nosniff", "referrer-policy": "no-referrer", "cache-control": "no-store",
};

export function createApp(manager: ConversationManager, staticRoot = fileURLToPath(new URL("../client", import.meta.url)), modelAccess?: ModelAccessService) {
  const viewerSockets = new Map<string, Set<Duplex>>();
  const closeViewerSockets = (conversationId: string) => {
    const sockets = viewerSockets.get(conversationId);
    viewerSockets.delete(conversationId);
    for (const socket of sockets ?? []) socket.destroy();
  };
  const stopWatchingViewerSessions = manager.onViewerInvalidated(closeViewerSockets);
  const server = createServer(async (request, response) => {
    for (const [name, value] of Object.entries(securityHeaders)) response.setHeader(name, value);
    try { await route(manager, staticRoot, request, response, modelAccess); }
    catch (error) {
      if (response.headersSent) return response.end();
      const status = error instanceof z.ZodError ? 400 : typeof (error as { status?: unknown })?.status === "number" ? (error as { status: number }).status : 500;
      const message = error instanceof z.ZodError ? "Request body is invalid. Check the fields and try again." : status < 500 && error instanceof Error ? error.message : "OpenMuse hit an unexpected error. Check the server log and try again.";
      if (status >= 500) console.error("OpenMuse request failed.");
      sendJson(response, status, { error: message, code: error instanceof z.ZodError ? "invalid_request" : typeof (error as { code?: unknown })?.code === "string" ? (error as { code: string }).code : "request_failed" });
    }
  });
  server.on("upgrade", async (request, socket, head) => {
    try {
      const url = new URL(request.url ?? "/", "http://127.0.0.1");
      const match = url.pathname.match(/^\/api\/conversations\/([^/]+)\/viewer\/websockify$/);
      if (!match || !authenticated(request)) return socket.destroy();
      const targetUrl = await manager.consumeViewerNonce(match[1], url.searchParams.get("token") ?? "");
      if (!targetUrl) return socket.destroy();
      const target = new URL(targetUrl);
      const conversationId = match[1];
      const sockets = viewerSockets.get(conversationId) ?? new Set<Duplex>();
      viewerSockets.set(conversationId, sockets);
      sockets.add(socket);
      const forgetSocket = () => {
        sockets.delete(socket);
        if (sockets.size === 0) viewerSockets.delete(conversationId);
      };
      socket.once("close", forgetSocket);
      socket.once("error", forgetSocket);
      prepareViewerProxyRequest(request, target);
      proxy.ws(request, socket, head, { target: target.origin });
    } catch { socket.destroy(); }
  });
  const cleanupTimer = setInterval(() => cleanupSessions(modelAccess), 15 * 60_000);
  cleanupTimer.unref();
  server.on("close", () => {
    clearInterval(cleanupTimer);
    stopWatchingViewerSessions();
    for (const conversationId of viewerSockets.keys()) closeViewerSockets(conversationId);
    modelAccess?.close();
  });
  return server;
}

async function route(manager: ConversationManager, staticRoot: string, request: IncomingMessage, response: ServerResponse, modelAccess?: ModelAccessService): Promise<void> {
  const method = request.method ?? "GET";
  const url = new URL(request.url ?? "/", "http://127.0.0.1");
  if (method === "GET" && url.pathname === "/api/bootstrap") {
    assertLoopbackRequest(request);
    cleanupSessions(modelAccess);
    let capability = cookieValue(request);
    let session = capability ? validSession(capability) : undefined;
    if (!session) {
      capability = randomBytes(32).toString("base64url");
      const now = Date.now();
      session = { csrfToken: randomBytes(32).toString("base64url"), createdAt: now, lastSeenAt: now };
      sessions.set(capability, session);
      enforceSessionLimit(modelAccess);
      response.setHeader("set-cookie", `open_muse_session=${capability}; HttpOnly; SameSite=Strict; Path=/; Max-Age=86400`);
    } else session.lastSeenAt = Date.now();
    return sendJson(response, 200, {
      csrfToken: session.csrfToken,
      conversationId: manager.activeConversationId,
      ...(modelAccess ? { modelAccess: await modelAccess.snapshot(session.selection) } : {}),
    });
  }
  if (method === "GET" && url.pathname === "/api/health") return sendJson(response, 200, { ready: true });
  if (url.pathname.startsWith("/api/") && !authenticated(request)) throw Object.assign(new Error("Reload OpenMuse to restore the local session."), { status: 401 });

  if (!["GET", "HEAD", "OPTIONS"].includes(method)) assertMutation(request);
  const sessionId = cookieValue(request)!;
  const session = sessions.get(sessionId)!;
  if (modelAccess && method === "GET" && url.pathname === "/api/model-access") return sendJson(response, 200, await modelAccess.snapshot(session.selection));
  if (modelAccess && method === "PUT" && url.pathname === "/api/model-access/selection") {
    const selection = selectionBody.parse(await readJson(request));
    await modelAccess.validateSelection(selection);
    session.selection = selection;
    return sendJson(response, 200, selection);
  }
  if (modelAccess && method === "POST" && url.pathname === "/api/auth-attempts") {
    const body = authAttemptBody.parse(await readJson(request));
    return sendJson(response, 201, { attempt: modelAccess.startAttempt(sessionId, body.providerId, body.method) });
  }
  const attemptMatch = url.pathname.match(/^\/api\/auth-attempts\/([^/]+)$/);
  if (modelAccess && method === "GET" && attemptMatch) return sendJson(response, 200, { attempt: modelAccess.getAttempt(sessionId, attemptMatch[1]) });
  if (modelAccess && method === "DELETE" && attemptMatch) return sendJson(response, 202, { stopping: true, attempt: modelAccess.cancelAttempt(sessionId, attemptMatch[1]) });
  const attemptEventsMatch = url.pathname.match(/^\/api\/auth-attempts\/([^/]+)\/events$/);
  if (modelAccess && method === "GET" && attemptEventsMatch) return streamAuthEvents(modelAccess, sessionId, attemptEventsMatch[1], request, response);
  const promptMatch = url.pathname.match(/^\/api\/auth-attempts\/([^/]+)\/prompts\/([^/]+)$/);
  if (modelAccess && method === "POST" && promptMatch) {
    const body = authPromptBody.parse(await readJson(request));
    return sendJson(response, 200, { attempt: modelAccess.submitPrompt(sessionId, promptMatch[1], promptMatch[2], body.value) });
  }
  const logoutMatch = url.pathname.match(/^\/api\/model-access\/providers\/([^/]+)$/);
  if (modelAccess && method === "DELETE" && logoutMatch) {
    await manager.disconnectProvider(logoutMatch[1]);
    return sendJson(response, 200, { disconnected: true });
  }
  if (method === "GET" && url.pathname === "/api/conversations") return sendJson(response, 200, manager.list());
  if (method === "POST" && url.pathname === "/api/conversations") {
    const body = createConversationBody.parse(await readJson(request));
    const requested = "providerId" in body ? selectionBody.parse(body) : modelAccess ? session.selection : undefined;
    const conversation = await manager.create(requested);
    if (modelAccess) session.selection = { providerId: conversation.providerId, modelId: conversation.modelId };
    return sendJson(response, 201, conversation);
  }
  const snapshotMatch = url.pathname.match(/^\/api\/conversations\/([^/]+)$/);
  if (method === "GET" && snapshotMatch) return sendJson(response, 200, manager.snapshot(snapshotMatch[1]));
  const commandsMatch = url.pathname.match(/^\/api\/conversations\/([^/]+)\/commands$/);
  if (method === "POST" && commandsMatch) {
    const body = commandBody.parse(await readJson(request));
    const result = await manager.dispatch(commandsMatch[1], body);
    if (modelAccess && body.command.kind === "change_model") session.selection = { providerId: body.command.providerId, modelId: body.command.modelId };
    return sendJson(response, body.command.kind === "send_message" || body.command.kind === "stop" ? 202 : 200, result);
  }
  const activateMatch = url.pathname.match(/^\/api\/conversations\/([^/]+)\/activate$/);
  if (method === "POST" && activateMatch) {
    const conversation = await manager.activate(activateMatch[1]);
    if (modelAccess) session.selection = { providerId: conversation.providerId, modelId: conversation.modelId };
    return sendJson(response, 200, conversation);
  }
  const diagnosticsMatch = url.pathname.match(/^\/api\/conversations\/([^/]+)\/diagnostics$/);
  if (method === "GET" && diagnosticsMatch) {
    assertLoopbackRequest(request);
    return sendJson(response, 200, manager.diagnostics(diagnosticsMatch[1]));
  }
  const eventsMatch = url.pathname.match(/^\/api\/conversations\/([^/]+)\/events$/);
  if (method === "GET" && eventsMatch) { assertLoopbackRequest(request); return streamEvents(manager, eventsMatch[1], request, response); }
  const tokenMatch = url.pathname.match(/^\/api\/conversations\/([^/]+)\/viewer-token$/);
  if (method === "POST" && tokenMatch) return sendJson(response, 200, manager.issueViewerNonce(tokenMatch[1]));
  if (url.pathname.startsWith("/api/")) throw Object.assign(new Error("That OpenMuse route does not exist."), { status: 404 });
  if (method !== "GET" && method !== "HEAD") throw Object.assign(new Error("Method not allowed."), { status: 405 });
  await serveStatic(staticRoot, url.pathname, response, method === "HEAD");
}

function assertLoopbackRequest(request: IncomingMessage): void {
  const host = (request.headers.host ?? "").split(":")[0].replace(/^\[|\]$/g, "");
  if (!new Set(["127.0.0.1", "localhost", "::1"]).has(host)) throw Object.assign(new Error("OpenMuse only accepts requests from this computer."), { status: 403 });
  const site = request.headers["sec-fetch-site"];
  if (site && site !== "same-origin" && site !== "none") throw Object.assign(new Error("Open the local OpenMuse page directly on this computer."), { status: 403 });
}

function cookieValue(request: IncomingMessage): string | undefined {
  return request.headers.cookie?.split(";").map((part) => part.trim()).find((part) => part.startsWith("open_muse_session="))?.slice("open_muse_session=".length);
}
function validSession(capability: string): LocalSession | undefined {
  const session = sessions.get(capability);
  if (!session) return;
  const now = Date.now();
  if (now - session.lastSeenAt > SESSION_IDLE_MS || now - session.createdAt > SESSION_ABSOLUTE_MS) return;
  return session;
}
function authenticated(request: IncomingMessage): boolean {
  const value = cookieValue(request);
  const session = value ? validSession(value) : undefined;
  if (session) session.lastSeenAt = Date.now();
  return Boolean(session);
}
function prepareViewerProxyRequest(request: IncomingMessage, target: URL): void {
  request.url = `${target.pathname}${target.search}`;
  request.headers.host = target.host;
  delete request.headers.cookie;
  delete request.headers.authorization;
  delete request.headers["x-smol-csrf"];
}
function cleanupSessions(modelAccess?: ModelAccessService): void {
  const now = Date.now();
  for (const [capability, session] of sessions) {
    if (now - session.lastSeenAt > SESSION_IDLE_MS || now - session.createdAt > SESSION_ABSOLUTE_MS) {
      modelAccess?.cancelSessionAttempts(capability);
      sessions.delete(capability);
    }
  }
  enforceSessionLimit(modelAccess);
}
function enforceSessionLimit(modelAccess?: ModelAccessService): void {
  while (sessions.size > MAX_SESSIONS) {
    const oldest = [...sessions.entries()].sort((a, b) => a[1].lastSeenAt - b[1].lastSeenAt)[0];
    if (!oldest) return;
    modelAccess?.cancelSessionAttempts(oldest[0]);
    sessions.delete(oldest[0]);
  }
}
function assertMutation(request: IncomingMessage): void {
  assertLoopbackRequest(request);
  const origin = request.headers.origin;
  if (!origin || !["127.0.0.1", "localhost", "::1"].includes(new URL(origin).hostname)) throw Object.assign(new Error("Reload OpenMuse and try again."), { status: 403 });
  const capability = cookieValue(request)!;
  if (request.headers["x-smol-csrf"] !== sessions.get(capability)?.csrfToken) throw Object.assign(new Error("Reload OpenMuse and try again."), { status: 403 });
  if (!(request.headers["content-type"] ?? "").startsWith("application/json")) throw Object.assign(new Error("Requests must use JSON."), { status: 415 });
}

async function readJson(request: IncomingMessage): Promise<unknown> {
  const chunks: Buffer[] = []; let size = 0;
  for await (const chunk of request) { const bytes = Buffer.from(chunk); size += bytes.length; if (size > 32 * 1024) throw Object.assign(new Error("Request body is too large."), { status: 413 }); chunks.push(bytes); }
  try { return JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}"); } catch { throw Object.assign(new Error("Request body must be valid JSON."), { status: 400 }); }
}

function streamAuthEvents(modelAccess: ModelAccessService, sessionId: string, attemptId: string, request: IncomingMessage, response: ServerResponse): void {
  modelAccess.getAttempt(sessionId, attemptId);
  response.statusCode = 200; response.setHeader("content-type", "text/event-stream"); response.setHeader("connection", "keep-alive"); response.setHeader("x-accel-buffering", "no"); response.flushHeaders();
  const afterId = Number(request.headers["last-event-id"] ?? 0) || 0;
  let unsubscribe: () => void = () => undefined;
  unsubscribe = modelAccess.subscribe(sessionId, attemptId, (event) => {
    response.write(`id: ${event.id}\nevent: ${event.type}\ndata: ${JSON.stringify(event)}\n\n`);
    if (["auth.succeeded", "auth.failed", "auth.cancelled", "auth.expired", "auth.resync_required"].includes(event.type)) queueMicrotask(() => { unsubscribe(); response.end(); });
  }, afterId);
  const heartbeat = setInterval(() => response.write(": heartbeat\n\n"), 15_000);
  request.on("close", () => { clearInterval(heartbeat); unsubscribe(); });
}

function streamEvents(manager: ConversationManager, id: string, request: IncomingMessage, response: ServerResponse): void {
  response.statusCode = 200; response.setHeader("content-type", "text/event-stream"); response.setHeader("connection", "keep-alive"); response.setHeader("x-accel-buffering", "no"); response.flushHeaders();
  const unsubscribe = manager.subscribeViews(id, (view) => response.write(`id: ${view.version}\nevent: conversation.view\ndata: ${JSON.stringify({ view })}\n\n`));
  if (!unsubscribe) { response.end(`event: error\ndata: {"error":"Conversation not found"}\n\n`); return; }
  const heartbeat = setInterval(() => response.write(": heartbeat\n\n"), 15_000);
  request.on("close", () => { clearInterval(heartbeat); unsubscribe(); });
}

async function serveStatic(root: string, pathname: string, response: ServerResponse, head: boolean): Promise<void> {
  const relative = normalize(decodeURIComponent(pathname)).replace(/^([/\\])+/, ""); let target = join(root, relative || "index.html");
  if (target !== root && !target.startsWith(`${root}${sep}`)) throw Object.assign(new Error("Not found."), { status: 404 });
  try { const info = await stat(target); if (info.isDirectory()) target = join(target, "index.html"); await access(target); }
  catch { if (extname(target)) throw Object.assign(new Error("Not found."), { status: 404 }); target = join(root, "index.html"); }
  const mime: Record<string, string> = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml" };
  response.statusCode = 200; response.setHeader("content-type", mime[extname(target)] ?? "application/octet-stream");
  if (head) { response.end(); return; } createReadStream(target).pipe(response);
}
function sendJson(response: ServerResponse, status: number, body: unknown): void { response.statusCode = status; response.setHeader("content-type", "application/json; charset=utf-8"); response.end(JSON.stringify(body)); }

export function startupFailureMessage(error: unknown): string {
  const detail = error instanceof Error && error.message.trim() ? error.message.trim() : "An unknown error occurred.";
  return `OpenMuse could not start: ${detail}`;
}

export function closeHttpServer(server: Server): Promise<void> {
  if (!server.listening) return Promise.resolve();
  return new Promise<void>((resolve, reject) => {
    server.close((error) => error ? reject(error) : resolve());
    server.closeAllConnections();
  });
}

async function main(): Promise<void> {
  try { process.loadEnvFile(".env.local"); } catch { /* optional */ }
  const host = process.env.OPEN_MUSE_HOST ?? "127.0.0.1"; const port = Number(process.env.OPEN_MUSE_PORT ?? 4318);
  if (host !== "127.0.0.1") throw new Error("OpenMuse only listens locally. Set OPEN_MUSE_HOST=127.0.0.1.");
  const modelAccess = ModelAccessService.createDefault();
  const computerProvider = createComputerProvider();
  const manager = await ConversationManager.open(
    process.env.OPENAI_API_KEY ?? "",
    process.env.OPENAI_MODEL ?? "gpt-5.6-luna",
    process.env.OPEN_MUSE_FIXTURE_STORE === "1",
    undefined,
    { computerProvider },
    modelAccess,
  );
  const server = createApp(manager, fileURLToPath(new URL("../client", import.meta.url)), modelAccess); let closing = false;
  const shutdown = async () => {
    if (closing) return;
    closing = true;
    modelAccess.close();
    await Promise.all([closeHttpServer(server), manager.close()]);
  };
  process.once("SIGINT", () => void shutdown()); process.once("SIGTERM", () => void shutdown());
  server.listen(port, host, () => console.log(`OpenMuse is ready at http://${host}:${port}`));
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  void main().catch((error: unknown) => {
    console.error(startupFailureMessage(error));
    process.exitCode = 1;
  });
}

export const _test = { assertLoopbackRequest, prepareViewerProxyRequest };

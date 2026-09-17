import assert from "node:assert/strict";
import type { AddressInfo } from "node:net";
import test from "node:test";
import { ConversationManager } from "../server/manager.js";

// Regression: ISSUE-001 — CommonJS http-proxy used a named ESM import and crashed server startup
// Found by /qa on 2026-09-13
// Report: .gstack/qa-reports/qa-report-127-0-0-1-2026-09-13.md
test("the server module loads in the Node ESM runtime", async () => {
  const server = await import("../server/index.js");
  assert.equal(typeof server.createApp, "function");
});

test("startup failures preserve the actionable cause", async () => {
  const { startupFailureMessage } = await import("../server/index.js");
  assert.equal(
    startupFailureMessage(new Error("OpenMuse only listens locally. Set OPEN_MUSE_HOST=127.0.0.1.")),
    "OpenMuse could not start: OpenMuse only listens locally. Set OPEN_MUSE_HOST=127.0.0.1.",
  );
  assert.equal(startupFailureMessage(undefined), "OpenMuse could not start: An unknown error occurred.");
});

test("server shutdown closes active trace streams", async () => {
  const { closeHttpServer, createApp } = await import("../server/index.js");
  const manager = new ConversationManager("", "gpt-5-mini");
  const conversation = await manager.create();
  const server = createApp(manager);
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  const origin = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
  const bootstrap = await fetch(`${origin}/api/bootstrap`);
  const cookie = bootstrap.headers.get("set-cookie")!.split(";")[0]!;
  const stream = await fetch(`${origin}/api/conversations/${conversation.id}/traces/events`, { headers: { cookie } });

  await closeHttpServer(server);

  assert.equal(server.listening, false);
  await stream.body?.cancel().catch(() => undefined);
});

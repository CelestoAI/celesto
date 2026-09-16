import assert from "node:assert/strict";
import type { AddressInfo } from "node:net";
import test from "node:test";
import { createComputerProvider, type ProviderDependencies } from "../server/computer-provider.js";
import { closeHttpServer, createApp } from "../server/index.js";
import { ConversationManager } from "../server/manager.js";

test("Celesto delete returns after the delete request is accepted", async () => {
  const cloud = {
    id: "cmp-delete", status: "running", lastError: undefined,
    exec: async () => ({ exitCode: 0, stdout: "", stderr: "" }),
    createBrowserConnection: async () => ({ url: "wss://gateway/browser" }),
    createDisplayConnection: async () => ({ url: "wss://gateway/display", mode: "read_only" as const }),
    delete: async () => { cloud.status = "deleting"; return cloud; },
    start: async () => cloud,
    refresh: async () => cloud,
  };
  const provider = createComputerProvider({ provider: "celesto", apiKey: "key-secret" }, {
    createCloudComputer: async () => cloud as never,
    wait: async () => new Promise<void>(() => undefined),
  } satisfies Partial<ProviderDependencies>);
  const computer = await provider.create({ network: "open", viewport: { width: 1, height: 1 } });

  const deleted = await Promise.race([
    computer.delete().then(() => true),
    new Promise<false>((resolve) => setTimeout(() => resolve(false), 25)),
  ]);

  assert.equal(deleted, true);
  assert.equal(cloud.status, "deleting");
});

test("server shutdown closes active trace streams", async () => {
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

  await Promise.race([
    closeHttpServer(server),
    new Promise<never>((_resolve, reject) => setTimeout(() => reject(new Error("server shutdown timed out")), 500)),
  ]);

  assert.equal(server.listening, false);
  await stream.body?.cancel().catch(() => undefined);
});

import assert from "node:assert/strict";
import test from "node:test";
import { CelestoApiError } from "@celestoai/sdk";
import {
  computerProviderConfig,
  createComputerProvider,
  type ProviderDependencies,
} from "../server/computer-provider.js";

test("computer provider configuration defaults to SmolVM and validates Celesto credentials", () => {
  assert.deepEqual(computerProviderConfig({}), { provider: "smolvm" });
  assert.deepEqual(computerProviderConfig({
    OPENMUSE_COMPUTER_PROVIDER: "celesto",
    CELESTO_API_KEY: "key-secret",
    CELESTO_API_URL: "https://control.example",
  }), { provider: "celesto", apiKey: "key-secret", apiUrl: "https://control.example" });
  assert.throws(
    () => computerProviderConfig({ OPENMUSE_COMPUTER_PROVIDER: "celesto" }),
    /CELESTO_API_KEY is empty.*OPENMUSE_COMPUTER_PROVIDER=smolvm/,
  );
  assert.throws(
    () => computerProviderConfig({ OPENMUSE_COMPUTER_PROVIDER: "remote" }),
    /must be 'smolvm' or 'celesto'/,
  );
});

test("SmolVM provider preserves the existing computer behavior behind the protocol", async () => {
  const calls: string[] = [];
  const browser = {
    cdpUrl: null as string | null,
    async launch() { calls.push("launch"); this.cdpUrl = "http://127.0.0.1:9222"; },
  };
  const computer = {
    browser,
    display: { viewerUrl: "http://127.0.0.1:6080/vnc.html" },
    exec: async () => ({ ok: true, exitCode: 0, stdout: "ok", stderr: "", durationMs: 1 }),
    delete: async () => { calls.push("delete"); },
  };
  const provider = createComputerProvider({ provider: "smolvm" }, {
    createSmolVM: () => ({
      computers: { create: async (options: unknown) => { calls.push(JSON.stringify(options)); return computer; } },
      close: async () => { calls.push("close"); },
    }) as never,
  });

  const handle = await provider.create({ network: "off", viewport: { width: 1440, height: 900 } });
  assert.equal(handle.reference, undefined);
  assert.deepEqual(await handle.createBrowserConnection(), { url: "http://127.0.0.1:9222" });
  assert.deepEqual(await handle.createDisplayConnection("read_only"), { url: "ws://127.0.0.1:6080/websockify" });
  await handle.detach();
  await handle.delete();

  assert.match(calls[0]!, /"network":\{"mode":"off"\}/);
  assert.deepEqual(calls.slice(1), ["launch", "delete", "close"]);
});

test("Celesto provider creates, reconnects, executes, and mints scoped connections", async () => {
  const calls: Array<unknown> = [];
  const cloud = {
    id: "cmp-cloud",
    status: "running",
    lastError: undefined,
    exec: async (command: string, options: unknown) => {
      calls.push(["exec", command, options]);
      return { exitCode: 0, stdout: "done", stderr: "", durationMs: 12 };
    },
    createBrowserConnection: async () => ({ url: "wss://gateway/browser?token=browser-secret" }),
    createDisplayConnection: async (options: unknown) => {
      calls.push(["display", options]);
      return { url: "wss://gateway/display?token=display-secret", mode: "read_only" };
    },
    delete: async () => { calls.push("delete"); cloud.status = "deleted"; return cloud; },
    start: async () => cloud,
    refresh: async () => cloud,
  };
  const dependencies: Partial<ProviderDependencies> = {
    createCloudComputer: async (options, config) => {
      calls.push(["create", options, config]);
      return cloud as never;
    },
    getCloudComputer: async (id, config) => {
      calls.push(["get", id, config]);
      return cloud as never;
    },
  };
  const provider = createComputerProvider({
    provider: "celesto",
    apiKey: "key-secret",
    apiUrl: "https://control.example",
  }, dependencies);

  const created = await provider.create({ network: "open", viewport: { width: 1440, height: 900 } });
  assert.deepEqual(created.reference, { provider: "celesto", id: "cmp-cloud" });
  assert.deepEqual(await created.exec(["printf", "it's safe"], { timeoutMs: 35_000 }), {
    ok: true, exitCode: 0, stdout: "done", stderr: "", durationMs: 12,
  });
  assert.deepEqual(await created.createBrowserConnection(), { url: "wss://gateway/browser?token=browser-secret" });
  assert.deepEqual(await created.createDisplayConnection("read_only"), { url: "wss://gateway/display?token=display-secret" });
  assert.ok(await provider.reconnect({ provider: "celesto", id: "cmp-cloud" }));
  await created.detach();
  await created.delete();

  assert.deepEqual(calls[0], ["create", { templateId: "browser-agent", networkPolicy: { mode: "open" } }, { apiKey: "key-secret", baseUrl: "https://control.example" }]);
  assert.deepEqual(calls[1], ["exec", `'printf' 'it'"'"'s safe'`, { timeout: 35, signal: undefined }]);
  assert.deepEqual(calls[2], ["display", { mode: "read_only" }]);
  assert.deepEqual(calls[3], ["get", "cmp-cloud", { apiKey: "key-secret", baseUrl: "https://control.example" }]);
  assert.equal(calls[4], "delete");
});

test("Celesto reconnect treats only a missing computer as recoverable", async () => {
  const missing = createComputerProvider({ provider: "celesto", apiKey: "key-secret" }, {
    getCloudComputer: async () => { throw new CelestoApiError("missing", 404, {}); },
  });
  assert.equal(await missing.reconnect({ provider: "celesto", id: "gone" }), undefined);

  const unauthorized = createComputerProvider({ provider: "celesto", apiKey: "key-secret" }, {
    getCloudComputer: async () => { throw new CelestoApiError("unauthorized", 401, {}); },
  });
  await assert.rejects(unauthorized.reconnect({ provider: "celesto", id: "private" }), /unauthorized/);

  const deleted = createComputerProvider({ provider: "celesto", apiKey: "key-secret" }, {
    getCloudComputer: async () => ({ id: "deleted", status: "deleted", lastError: undefined }) as never,
  });
  assert.equal(await deleted.reconnect({ provider: "celesto", id: "deleted" }), undefined);
});

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
  });
  const computer = await provider.create({ network: "open", viewport: { width: 1, height: 1 } });

  const deleted = await Promise.race([
    computer.delete().then(() => true),
    new Promise<false>((resolve) => setTimeout(() => resolve(false), 25)),
  ]);

  assert.equal(deleted, true);
  assert.equal(cloud.status, "deleting");
});

test("Celesto connections poll a starting sandbox with bounded backoff", async () => {
  const waits: number[] = [];
  let browserAttempts = 0;
  let displayAttempts = 0;
  const cloud = {
    id: "cmp-starting", status: "running", lastError: undefined,
    exec: async () => ({ exitCode: 0, stdout: "", stderr: "" }),
    createBrowserConnection: async () => {
      browserAttempts += 1;
      if (browserAttempts < 3) throw new CelestoApiError("Sandbox is still starting", 409, { detail: "Sandbox is still starting" });
      return { url: "wss://gateway/browser" };
    },
    createDisplayConnection: async () => {
      displayAttempts += 1;
      if (displayAttempts < 2) throw new CelestoApiError("Sandbox is still starting", 409, { detail: "Sandbox is still starting" });
      return { url: "wss://gateway/display", mode: "read_only" as const };
    },
    delete: async () => cloud, start: async () => cloud, refresh: async () => cloud,
  };
  const provider = createComputerProvider({ provider: "celesto", apiKey: "key-secret" }, {
    createCloudComputer: async () => cloud as never,
    wait: async (milliseconds) => { waits.push(milliseconds); },
  });
  const computer = await provider.create({ network: "open", viewport: { width: 1, height: 1 } });

  assert.deepEqual(await computer.createBrowserConnection(), { url: "wss://gateway/browser" });
  assert.deepEqual(await computer.createDisplayConnection("read_only"), { url: "wss://gateway/display" });
  assert.deepEqual(waits, [250, 500, 250]);
});

test("Celesto connection polling stops after a bounded number of starting responses", async () => {
  let attempts = 0;
  const cloud = {
    id: "cmp-starting", status: "running", lastError: undefined,
    exec: async () => ({ exitCode: 0, stdout: "", stderr: "" }),
    createBrowserConnection: async () => {
      attempts += 1;
      throw new CelestoApiError("Sandbox is still starting", 409, { detail: "Sandbox is still starting" });
    },
    createDisplayConnection: async () => ({ url: "wss://gateway/display", mode: "read_only" as const }),
    delete: async () => cloud, start: async () => cloud, refresh: async () => cloud,
  };
  const provider = createComputerProvider({ provider: "celesto", apiKey: "key-secret" }, {
    createCloudComputer: async () => cloud as never,
    wait: async () => undefined,
  });
  const computer = await provider.create({ network: "open", viewport: { width: 1, height: 1 } });

  await assert.rejects(computer.createBrowserConnection(), /did not become ready/);
  assert.equal(attempts, 15);
});

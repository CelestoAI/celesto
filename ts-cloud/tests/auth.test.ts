import assert from "node:assert/strict";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  MISSING_CREDENTIALS_MESSAGE,
  resolveCelestoApiKey,
  resolveClientConfig,
} from "../src/core/auth";
import { CelestoError } from "../src/core/errors";

test("explicit SDK credentials take precedence over local sources", async () => {
  let readDotEnv = false;
  let loadSavedApiKey = false;

  const config = await resolveClientConfig(
    { token: "explicit-key", timeoutMs: 1_000 },
    {
      env: { CELESTO_API_KEY: "environment-key" },
      readDotEnv: async () => {
        readDotEnv = true;
        return "CELESTO_API_KEY=dotenv-key";
      },
      loadSavedApiKey: async () => {
        loadSavedApiKey = true;
        return "saved-key";
      },
    },
  );

  assert.equal(config.token, "explicit-key");
  assert.equal(config.timeoutMs, 1_000);
  assert.equal(readDotEnv, false);
  assert.equal(loadSavedApiKey, false);
});

test("environment credentials take precedence", async () => {
  let readDotEnv = false;
  let loadSavedApiKey = false;

  const apiKey = await resolveCelestoApiKey({
    cwd: "/project",
    env: { CELESTO_API_KEY: "environment-key" },
    readDotEnv: async () => {
      readDotEnv = true;
      return "CELESTO_API_KEY=dotenv-key";
    },
    loadSavedApiKey: async () => {
      loadSavedApiKey = true;
      return "saved-key";
    },
  });

  assert.equal(apiKey, "environment-key");
  assert.equal(readDotEnv, false);
  assert.equal(loadSavedApiKey, false);
});

test("credentials can be loaded from the current project .env", async () => {
  let requestedPath = "";
  let loadSavedApiKey = false;

  const apiKey = await resolveCelestoApiKey({
    cwd: "/project",
    env: {},
    readDotEnv: async (filePath) => {
      requestedPath = filePath;
      return 'OTHER=value\nCELESTO_API_KEY="dotenv-key"\n';
    },
    loadSavedApiKey: async () => {
      loadSavedApiKey = true;
      return "saved-key";
    },
  });

  assert.equal(apiKey, "dotenv-key");
  assert.equal(requestedPath, "/project/.env");
  assert.equal(loadSavedApiKey, false);
});

test("saved CLI credentials are used after environment sources miss", async () => {
  const apiKey = await resolveCelestoApiKey({
    cwd: "/project",
    env: {},
    readDotEnv: async () => {
      throw new Error("missing");
    },
    loadSavedApiKey: async () => "saved-key",
  });

  assert.equal(apiKey, "saved-key");
});

test("reads the CLI's actual saved login format and keeps the key on its saved origin", async (t) => {
  const homeDir = await mkdtemp(join(tmpdir(), "celesto-sdk-home-"));
  t.after(() => rm(homeDir, { recursive: true, force: true }));
  const dir = join(homeDir, ".celesto");
  await mkdir(dir);
  await writeFile(join(dir, "credentials"), JSON.stringify({
    api_key: "fixture-key",
    base_url: "https://saved.example.test/",
  }), { mode: 0o600 });
  const options = { env: {}, cwd: homeDir, homeDir };
  const config = await resolveClientConfig({ baseUrl: undefined }, options);
  assert.equal(config.token, "fixture-key");
  assert.equal(config.baseUrl, "https://saved.example.test");
  await assert.rejects(
    resolveClientConfig({ baseUrl: "https://other.example.test" }, options),
    /different API URL/i,
  );
});

test("missing credentials return the actionable SDK error", async () => {
  await assert.rejects(
    resolveClientConfig(
      {},
      {
        cwd: "/project",
        env: {},
        readDotEnv: async () => "OTHER=value\n",
        loadSavedApiKey: async () => undefined,
      },
    ),
    (error: unknown) =>
      error instanceof CelestoError &&
      error.message === MISSING_CREDENTIALS_MESSAGE,
  );
});

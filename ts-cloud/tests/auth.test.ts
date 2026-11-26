import assert from "node:assert/strict";
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

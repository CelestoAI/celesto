import assert from "node:assert/strict";
import test from "node:test";
import { bootstrap } from "../client/api.js";

test("bootstrap retries while the local API server is still starting", async () => {
  const originalFetch = globalThis.fetch;
  let attempts = 0;
  globalThis.fetch = async () => {
    attempts += 1;
    if (attempts < 3) throw new TypeError("fetch failed");
    return new Response(JSON.stringify({ csrfToken: "csrf-token", conversationId: "conversation" }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  };

  try {
    assert.deepEqual(await bootstrap(), { conversationId: "conversation", modelAccess: undefined });
    assert.equal(attempts, 3);
  }
  finally {
    globalThis.fetch = originalFetch;
  }
});

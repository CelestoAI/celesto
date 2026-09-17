import assert from "node:assert/strict";
import test from "node:test";
import { waitForOpenMuseApi } from "../scripts/start-client.js";

test("the dev client waits for the API before starting Vite", async () => {
  let attempts = 0;
  const waits: number[] = [];
  await waitForOpenMuseApi(
    async () => {
      attempts += 1;
      if (attempts < 3) throw new TypeError("connection refused");
      return new Response('{"ready":true}', { status: 200 });
    },
    async (milliseconds) => { waits.push(milliseconds); },
  );

  assert.equal(attempts, 3);
  assert.deepEqual(waits, [50, 50]);
});

test("the dev client stops waiting when the API cannot start", async () => {
  let clock = 0;
  await assert.rejects(
    waitForOpenMuseApi(
      async () => { throw new TypeError("connection refused"); },
      async (milliseconds) => { clock += milliseconds; },
      100,
      () => clock,
    ),
    /check the server log/,
  );
});

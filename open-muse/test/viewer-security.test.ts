import assert from "node:assert/strict";
import test from "node:test";
import type { IncomingMessage } from "node:http";
import { _test } from "../server/index.js";
import { viewerReconnectDelay } from "../client/viewer-reconnect.js";

test("viewer reconnects use bounded backoff", () => {
  assert.equal(viewerReconnectDelay(0), 0);
  assert.equal(viewerReconnectDelay(1), 250);
  assert.equal(viewerReconnectDelay(2), 1_000);
  assert.equal(viewerReconnectDelay(3), 3_000);
  assert.equal(viewerReconnectDelay(4), undefined);
});

test("viewer proxy strips local credentials after authentication", () => {
  const request = {
    headers: {
      cookie: "open_muse_session=local-secret",
      authorization: "Bearer local-secret",
      "x-smol-csrf": "csrf-secret",
      "sec-websocket-key": "upgrade-key",
    },
  } as unknown as IncomingMessage;

  _test.stripLocalViewerCredentials(request);

  assert.equal(request.headers.cookie, undefined);
  assert.equal(request.headers.authorization, undefined);
  assert.equal(request.headers["x-smol-csrf"], undefined);
  assert.equal(request.headers["sec-websocket-key"], "upgrade-key");
});

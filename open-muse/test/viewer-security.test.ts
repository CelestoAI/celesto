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

test("viewer proxy targets the remote gateway without forwarding local credentials", () => {
  const request = {
    url: "/api/conversations/local/viewer/websockify?token=local-viewer-token",
    headers: {
      host: "127.0.0.1:4318",
      cookie: "open_muse_session=local-secret",
      authorization: "Bearer local-secret",
      "x-smol-csrf": "csrf-secret",
      "sec-websocket-key": "upgrade-key",
    },
  } as unknown as IncomingMessage;

  _test.prepareViewerProxyRequest(request, new URL("wss://gateway.example/v1/displays/computer/connect?token=remote-secret"));

  assert.equal(request.url, "/v1/displays/computer/connect?token=remote-secret");
  assert.equal(request.headers.host, "gateway.example");
  assert.equal(request.headers.cookie, undefined);
  assert.equal(request.headers.authorization, undefined);
  assert.equal(request.headers["x-smol-csrf"], undefined);
  assert.equal(request.headers["sec-websocket-key"], "upgrade-key");
});

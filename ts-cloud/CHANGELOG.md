# Cloud TypeScript SDK changelog

## 0.1.7

- Moved the Cloud TypeScript SDK into the Celesto repository without changing
  the npm package name or import paths. The source was imported from
  [`CelestoAI/sdk` at `1ab90c7`](https://github.com/CelestoAI/sdk/tree/1ab90c7fa0d845800c5e93a5a43ef163661e3f5b/ts).
- `Computer.create()` now sends the required `Idempotency-Key`. Pass
  `idempotencyKey` to reuse a key on retry.
- Use `sizeId` instead of CPU, memory, or disk overrides, which are now
  rejected before the request. The SDK also rejects unknown create options.
- `runStream()` and `execStream()` yield buffered output and an exit event
  after `/exec` completes. They no longer call the unavailable `/exec/stream`
  endpoint. Aborting stops the HTTP request, not necessarily the remote command.

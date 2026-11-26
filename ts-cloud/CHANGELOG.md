# Cloud TypeScript SDK changelog

## 0.1.7

- Moved the Cloud TypeScript SDK into the Celesto repository. The npm package
  name and the import paths for computers and agents are unchanged. Imported from
  [`CelestoAI/sdk` at `1ab90c7`](https://github.com/CelestoAI/sdk/tree/1ab90c7fa0d845800c5e93a5a43ef163661e3f5b/ts).
- Removed `GatekeeperClient` and `@celestoai/sdk/gatekeeper`. The Cloud API no
  longer offers Gatekeeper or its delegated Google Drive access.
- `Computer.create()` now sends the required `Idempotency-Key`. Pass
  `idempotencyKey` to reuse a key on retry.
- Use `sizeId` instead of CPU, memory, or disk overrides, which are now
  rejected before the request. The SDK also rejects unknown create options.
- `runStream()` and `execStream()` yield buffered output and an exit event
  after `/exec` completes. They no longer call the unavailable `/exec/stream`
  endpoint. Aborting stops the HTTP request, not necessarily the remote command.
- The computer SDK reads logins saved by `celesto auth login` and keeps each
  saved key on its original API URL.
- Requests honor their configured deadline even when a caller also supplies
  an abort signal. Managed-agent retries stop when canceled, and a stream
  that ends before a final event reports an error instead of partial success.

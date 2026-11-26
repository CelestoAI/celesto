# @celestoai/sdk

Use this package to run work in Celesto from a Node.js app. Your code can create
a cloud computer, run commands in it, and delete it when the work is done.

An AI agent is software that can plan and run tasks. A harness is the code that
starts, tests, or supervises an agent.

Use this package when you want to:

- Run an AI agent or harness in a clean computer.
- Run shell commands from JavaScript or TypeScript.
- Keep agent work separate from your laptop, server, or production system.

This is the Cloud SDK. To run computers on your own machine, use the separate
[@celestoai/celesto](https://github.com/CelestoAI/celesto/tree/main/ts) package.

## Requirements

- Node.js 18 or newer.
- A Celesto API key from [Celesto Settings](https://celesto.ai) under
  **Settings > Security**.

## Install

```bash
npm install @celestoai/sdk
```

The computer examples below require `@celestoai/sdk` 0.1.7 or newer.

Sign in once with the Celesto CLI:

```bash
pip install celesto
celesto auth login
```

The `Computer` API checks an explicitly passed `token` or `apiKey` first, then
`CELESTO_API_KEY` in the shell, the current project's `.env`, and credentials
saved by `celesto auth login`. A saved login is used only with the API URL it
was saved for. You can use a local `.env` instead of the CLI:

```bash .env
CELESTO_API_KEY="your-api-key"
```

Add `.env` to `.gitignore`.

## Quickstart

Create a file named `quickstart.mjs`. `Computer.create()` can return before
the computer is ready, so check its status before running commands.

```js
import { setTimeout as delay } from "node:timers/promises";
import { Computer } from "@celestoai/sdk";

const computer = await Computer.create();
console.log(`Computer ID: ${computer.id}`);
try {
  const deadline = Date.now() + 60_000;
  while (computer.status === "creating" && Date.now() < deadline) {
    await delay(500);
    await computer.refresh();
  }
  if (computer.status !== "running") {
    throw new Error(`Computer ${computer.id} is ${computer.status}. Check it in the Cloud dashboard.`);
  }

  const result = await computer.run("uname -a");
  console.log(result.stdout);
} finally {
  if (computer.status !== "creating") await computer.delete();
}
```

If it is still `creating` when the example stops waiting, check the printed
ID in the dashboard and delete it once creation finishes.

Run it:

```bash
node quickstart.mjs
```

## Computers

A computer is a disposable cloud machine for your app or agent. By default,
Celesto creates a `scratch` computer, which is a minimal Ubuntu computer.

### Choose a Size

```js
const computer = await Computer.create({ sizeId: "micro" });
```

Use the same readiness and cleanup steps as in the quickstart. Omit `sizeId`
to use your account's default. The SDK sends `sizeId` as `size_id`; the current
catalog (`GET /v1/billing/sizes`) lists the exact CPU, memory, and disk values.
Cloud computers do not accept CPU, memory, or disk overrides. The SDK also
rejects unknown options, including `name`, `labels`, and `size`.

The SDK generates an `Idempotency-Key` for each call. If your app needs to
retry the same creation request after a lost response, pass an
`idempotencyKey` you saved before the first attempt, and reuse that key and
the same options on retry. The SDK does not retry automatically.

### Control Internet Access

Internet is on by default. To disable outbound connections, replace the
`Computer.create()` line in the [quickstart](#quickstart):

```js
const computer = await Computer.create({ networkPolicy: { mode: "off" } });
```

Keep the quickstart's readiness check and cleanup. Commands and terminal
sessions still work without internet access. The policy cannot be changed
after creation. Pool computers do not support
`persistentHome: true`. Domain and IP allowlists are not supported.

### Templates

Use a template when you want a computer that already has extra tools installed.
For example, `coding-agent` includes common tools for coding tasks.

List available templates:

Create a file named `list-templates.mjs`:

```js
import { Computer } from "@celestoai/sdk";

const templates = await Computer.listTemplates();
for (const template of templates) {
  console.log(template.id, template.defaultRamMb);
}
```

To create a computer from a template, change the create call in the
[quickstart](#quickstart):

```js
const computer = await Computer.create({ templateId: "coding-agent" });
```

### Run a Command

Use the name or ID of a running computer:

```js
import { Computer } from "@celestoai/sdk";

const computer = await Computer.get("curie");
const result = await computer.run("ls -la", { timeout: 60 });
console.log(result.exitCode, result.stdout);
console.error(result.stderr);
```

Commands allow up to 10,000 characters and a timeout of 1–300 seconds. Do not
put secrets in command text. Encoding them in base64 does not protect them.

Use `runStream()` or its alias `execStream()` to consume the result as events.
Cloud waits for the command to finish before yielding any events. It yields
non-empty stdout first, then non-empty stderr, then an exit event. It does not
yield a `started` event or preserve the original order of stdout and stderr.

```js
import { Computer } from "@celestoai/sdk";

const computer = await Computer.get("curie");
const controller = new AbortController();

for await (const event of computer.runStream("npm test", {
  timeout: 300,
  signal: controller.signal,
})) {
  if (event.type === "stdout") process.stdout.write(event.data);
  if (event.type === "stderr") process.stderr.write(event.data);
  if (event.type === "exit") console.log(`Exit code: ${event.exitCode}`);
}
```

Call `controller.abort()` to stop waiting for the response. This does not
guarantee the remote command stopped. For interactive live output, use
[`createTerminalSession()`](#terminal-connections).

### Manage Computers

`computerId` can be `computer.id` from `Computer.create()` or a computer name
shown by the Celesto command-line tool: `celesto computer list --cloud`.

| Method | What it does |
| --- | --- |
| `Computer.list()` | List computers in your account |
| `Computer.get(computerId)` | Get one computer by name or ID |
| `computer.listCommandHistory()` | List recent commands and their status |
| `computer.createTerminalSession()` | Create a short-lived fast terminal connection |
| `computer.createBrowserConnection()` | Create a short-lived CDP connection to browser-agent Chromium |
| `computer.createDisplayConnection({ mode: "read_only" })` | Create a short-lived RFB display connection |
| `computer.stop()` | Stop a running computer |
| `computer.start()` | Start a stopped computer |
| `computer.delete()` | Delete a computer |

Save `computer.id` with the job that owns it so you can clean it up later.
If `delete()` returns HTTP 409 while the computer is `creating`, refresh its
status and retry deletion by the same ID once creation finishes. After
`stop()` and `start()`, check that your services are running again. Do not
assume processes survived.

### Publish Ports

Publish a port when a service inside the computer needs a public URL. Celesto
does not add authentication to the URL. Add authentication to the service
before publishing it if access should be restricted.

```js
import { Computer } from "@celestoai/sdk";

const computer = await Computer.get("curie");
const url = await computer.publishPort(8000);
console.log(url);
```

List and remove published ports:

```js
import { Computer } from "@celestoai/sdk";

const computer = await Computer.get("curie");
console.log(await computer.listPublishedPorts());
await computer.unpublishPort(8000);
```

### Terminal Connections

Use `createTerminalSession()` when you are building an interactive terminal.
Celesto returns a short-lived URL that connects directly to the fast terminal
gateway instead of sending terminal traffic through the control plane. Creating
a terminal session requires write access to the computer.

For Node.js, first install a WebSocket client:

```bash
npm install ws
```

Then connect with the authenticated URL:

```js
import { Computer } from "@celestoai/sdk";
import WebSocket from "ws";

const computer = await Computer.get("curie");
const connection = await computer.createTerminalSession();
const ws = new WebSocket(connection.url);

ws.on("message", (data) => process.stdout.write(data));
ws.on("open", () => ws.send("pwd\n"));
```

`connection.url` contains a short-lived terminal token. Treat it as a secret and
create a new terminal session after `connection.expiresAt`.

### Browser Automation Connections

Use the `browser-agent` template when your application needs an existing
Chromium browser. `createBrowserConnection()` returns a short-lived Chrome
DevTools Protocol (CDP) WebSocket URL that Playwright can attach to.

Install Playwright Core in the application that runs this code:

```bash
npm install playwright-core
```

Create a computer with the `browser-agent` template and wait until it is
running, as in the [quickstart](#quickstart). Replace `curie` with its name or
ID to connect without creating another computer:

```js
import { Computer } from "@celestoai/sdk";
import { chromium } from "playwright-core";

const computer = await Computer.get("curie");
const connection = await computer.createBrowserConnection();
const browser = await chromium.connectOverCDP(connection.url);
try {
  const context = browser.contexts()[0];
  if (!context) throw new Error("Celesto browser did not provide a context");
  const pages = context.pages();
  const page = pages[0] ?? await context.newPage();

  await page.goto("https://example.com");
  console.log(await page.title());
} finally {
  await browser.close();
}
```

Delete the computer separately when you no longer need it.

### Display Connections

Use `createDisplayConnection()` when a Remote Framebuffer (RFB) client, such as
the browser-based noVNC viewer, needs to watch the graphical desktop.
Connections are read-only by default. Pass
`{ mode: "read_write" }` when the viewer also needs pointer and keyboard control:

```js
import { Computer } from "@celestoai/sdk";

const computer = await Computer.get("curie");
const display = await computer.createDisplayConnection({ mode: "read_only" });
console.log(display.mode, display.expiresAt);
```

Pass `display.url` to the RFB client before it expires. Browser and display URLs
contain short-lived secret tokens, so do not log, persist, or share them. Create
a new connection after a disconnect or expiry. Browser automation and
read-write display connections require write access to the computer.

## Configuration

| Option | What it does |
| --- | --- |
| `token` | Celesto API key or JWT |
| `apiKey` | Alias for `token` |
| `baseUrl` | Custom Celesto API URL |
| `organizationId` | Sends the `X-Current-Organization` header |
| `timeoutMs` | Deadline in milliseconds for each request, including reading the response body |
| `headers` | Extra headers to send with every request |

Pass these options as the second argument to `Computer.create()` or
`Computer.get()`. An explicit `token` or `apiKey` takes precedence over local
credential discovery.

JWT is a signed login token. Most users should use a Celesto API key.

## Errors

The SDK exports these error classes:

| Error | When it is used |
| --- | --- |
| `CelestoApiError` | The API returns an error status |
| `CelestoNetworkError` | The network request fails |
| `CelestoError` | Base class for API and network errors |
| `TypeError` | The SDK rejects unsupported create options or invalid command arguments before sending a request |

## Develop Locally

If you are contributing and have `npm` installed, run these commands from the
repository's `ts-cloud` directory:

```bash
npm ci
npm run check
```

The package test installs the built npm archive and checks it against a local
HTTP fixture. No Cloud API key is needed. The tested archive and request
transcript are saved to `artifacts/cloud-sdk/` at the repository root.

## License

Apache-2.0. The SDK is open source. Use of the Celesto platform is governed by
the Celesto Terms of Service: https://celesto.ai/legal/terms
